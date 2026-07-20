"""Consulta de CNPJ via APIs públicas gratuitas — sem baixar a base completa da
Receita Federal (que tem dezenas de GB e exige um pipeline de ETL).

Cada CNPJ é consultado sob demanda em uma API pública (BrasilAPI, com OpenCNPJ
como alternativa caso a primeira falhe ou não responda), e o resultado é
normalizado para o formato usado pelos leads do Faro. O router é quem
decide se guarda o resultado em cache (ver `models.CnpjConsulta`).

Referências:
- https://brasilapi.com.br/docs (endpoint /api/cnpj/v1/{cnpj})
- https://opencnpj.org/ (endpoint /{cnpj})
"""

import re

import httpx

TIMEOUT = httpx.Timeout(6.0, connect=4.0)


class CnpjInvalido(Exception):
    pass


class CnpjNaoEncontrado(Exception):
    pass


class ConsultaIndisponivel(Exception):
    """Nenhuma das APIs públicas respondeu — tentar novamente mais tarde."""


def somente_digitos(cnpj: str) -> str:
    return re.sub(r"\D", "", cnpj or "")


_somente_digitos = somente_digitos


def formatar_cnpj(digitos: str) -> str:
    if len(digitos) != 14:
        return digitos
    return f"{digitos[0:2]}.{digitos[2:5]}.{digitos[5:8]}/{digitos[8:12]}-{digitos[12:14]}"


_formatar_cnpj = formatar_cnpj


def _normalizar_registro_rfb(dados: dict, digitos: str, fonte: str = "brasilapi") -> dict:
    """Normaliza um registro no formato usado pela BrasilAPI e pela busca
    paginada da API pública do minha-receita — as duas expõem exatamente os
    mesmos nomes de campo, pois ambas derivam do mesmo ETL sobre os dados da
    Receita Federal.
    """
    telefone = dados.get("ddd_telefone_1") or dados.get("ddd_telefone_2") or ""
    return {
        "cnpj": _formatar_cnpj(digitos),
        "razao_social": dados.get("razao_social") or dados.get("nome_fantasia") or "",
        "uf": dados.get("uf") or "",
        "municipio": dados.get("municipio") or "",
        "telefone": telefone,
        "email": dados.get("email") or "",
        "segmento": dados.get("cnae_fiscal_descricao") or "",
        "situacao_cadastral": (dados.get("descricao_situacao_cadastral") or "").upper(),
        "fonte": fonte,
    }


def _telefone_do_opencnpj(dados: dict) -> str:
    telefones = dados.get("telefones") or []
    if not telefones:
        return ""
    primeiro = telefones[0]
    if isinstance(primeiro, dict):
        ddd = primeiro.get("ddd", "")
        numero = primeiro.get("numero", "")
        return f"({ddd}) {numero}".strip() if (ddd or numero) else ""
    return str(primeiro)


def _segmento_do_opencnpj(dados: dict) -> str:
    for item in dados.get("cnaes") or []:
        if item.get("is_principal"):
            return item.get("descricao") or ""
    return ""


def _normalizar_opencnpj(dados: dict, digitos: str) -> dict:
    return {
        "cnpj": _formatar_cnpj(digitos),
        "razao_social": dados.get("razao_social") or dados.get("nome_fantasia") or "",
        "uf": dados.get("uf") or "",
        "municipio": dados.get("municipio") or "",
        "telefone": _telefone_do_opencnpj(dados),
        "email": dados.get("email") or "",
        "segmento": _segmento_do_opencnpj(dados),
        "situacao_cadastral": (dados.get("situacao_cadastral") or "").upper(),
        "fonte": "opencnpj",
    }


def _consultar_brasilapi(digitos: str) -> dict | None:
    resp = httpx.get(f"https://brasilapi.com.br/api/cnpj/v1/{digitos}", timeout=TIMEOUT)
    if resp.status_code == 404:
        return None
    if resp.status_code == 400:
        # A BrasilAPI valida o dígito verificador do CNPJ e responde 400 pra
        # um CNPJ com 14 dígitos mas checksum inválido — isso não é "API fora
        # do ar", é entrada inválida, e não adianta tentar a outra API.
        raise CnpjInvalido(f"CNPJ {digitos} inválido")
    resp.raise_for_status()
    return _normalizar_registro_rfb(resp.json(), digitos, fonte="brasilapi")


def _consultar_opencnpj(digitos: str) -> dict | None:
    resp = httpx.get(f"https://api.opencnpj.org/{digitos}", timeout=TIMEOUT)
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    return _normalizar_opencnpj(resp.json(), digitos)


def buscar_por_criterio(
    uf: str | None = None,
    cnae: str | None = None,
    cursor: str | None = None,
    limit: int = 100,
) -> tuple[list[dict], str | None]:
    """Busca empresas por critério (UF e/ou CNAE) via API pública — usada para
    a listagem de "novos leads" (prospecção), sem nenhuma base baixada
    localmente.

    Usa o endpoint de busca paginada da API pública do projeto minha-receita
    (https://docs.minhareceita.org/como-usar/#busca-paginada), que devolve os
    mesmos campos por empresa que a consulta por CNPJ único. Não tem garantia
    de disponibilidade (é mantida por doação voluntária) — quem chama essa
    função deve tratar `ConsultaIndisponivel`.

    Retorna a lista de empresas já normalizadas e o cursor para buscar a
    próxima página (`None` quando é a última).
    """
    params: dict[str, str | int] = {"limit": limit}
    if uf:
        params["uf"] = uf
    if cnae:
        params["cnae"] = cnae
    if cursor:
        params["cursor"] = cursor

    try:
        resp = httpx.get("https://minhareceita.org/", params=params, timeout=TIMEOUT)
        resp.raise_for_status()
        corpo = resp.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise ConsultaIndisponivel(
            "Não foi possível buscar novos leads agora — a API pública não respondeu"
        ) from exc

    # Sem SLA garantido, a API pode devolver 200 com um corpo que não é o
    # formato esperado (ex: um payload de erro). Tratamos isso como
    # indisponibilidade em vez de silenciosamente devolver "nenhum lead".
    if not isinstance(corpo, dict) or "data" not in corpo:
        raise ConsultaIndisponivel("A busca de novos leads devolveu uma resposta inesperada")

    itens = [
        _normalizar_registro_rfb(item, item.get("cnpj") or "", fonte="minha-receita")
        for item in corpo["data"]
        if isinstance(item, dict)
    ]
    return itens, corpo.get("cursor")


def consultar_cnpj(cnpj: str) -> dict:
    """Consulta um CNPJ nas APIs públicas gratuitas.

    Tenta a BrasilAPI primeiro; se ela estiver fora do ar ou der erro de rede,
    tenta a OpenCNPJ antes de desistir. Levanta `CnpjNaoEncontrado` só quando
    uma API respondeu de fato dizendo que o CNPJ não existe (404) — erro de
    rede/timeout vira `ConsultaIndisponivel`, para o chamador poder distinguir
    "não existe" de "não consegui verificar agora".
    """
    digitos = _somente_digitos(cnpj)
    if len(digitos) != 14:
        raise CnpjInvalido(f"CNPJ {cnpj!r} precisa ter 14 dígitos")

    nao_encontrado_em_alguma_api = False
    erros: list[Exception] = []

    for consultar in (_consultar_brasilapi, _consultar_opencnpj):
        try:
            resultado = consultar(digitos)
        except CnpjInvalido:
            # Dígito verificador inválido é um problema da entrada, não da
            # disponibilidade da API — não adianta tentar a próxima.
            raise
        except (httpx.HTTPError, ValueError) as exc:
            erros.append(exc)
            continue
        if resultado is None:
            nao_encontrado_em_alguma_api = True
            continue
        return resultado

    if nao_encontrado_em_alguma_api:
        raise CnpjNaoEncontrado(f"CNPJ {digitos} não encontrado")
    raise ConsultaIndisponivel(
        "Não foi possível consultar o CNPJ agora — as APIs públicas não responderam"
    ) from (erros[-1] if erros else None)
