import random

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .. import cnpj_api
from ..dependencies import get_current_user, get_db
from ..models import Lead, LeadOculto, User
from ..schemas import NovoLeadOut, OcultarLeadRequest

router = APIRouter(prefix="/leads/novos", tags=["novos-leads"])

# Sem UF/CNAE explícitos na chamada, sorteamos uma UF entre as mais populosas
# para manter a listagem variada a cada consulta — a API é quem decide quais
# empresas existem de verdade, isso só evita repetir sempre a mesma UF.
UFS_PADRAO = ["SP", "RJ", "MG", "PR", "RS", "SC", "GO", "CE", "BA", "PE", "DF", "ES"]

LEADS_POR_BUSCA = 50
PAGINAS_MAXIMAS = 6  # limite de segurança: a API de busca não tem SLA garantido
ITENS_POR_PAGINA = 100


def _buscar_leads_novos(uf: str | None, cnae: str | None, excluidos: set[str]) -> list[dict]:
    """Busca empresas ativas via API pública, paginando até juntar
    `LEADS_POR_BUSCA` leads que ainda não foram salvos nem ocultados pelo
    usuário (ou até esgotar as páginas / o limite de segurança).
    """
    encontrados: list[dict] = []
    cursor: str | None = None

    for _ in range(PAGINAS_MAXIMAS):
        pagina, cursor = cnpj_api.buscar_por_criterio(
            uf=uf, cnae=cnae, cursor=cursor, limit=ITENS_POR_PAGINA
        )
        for empresa in pagina:
            if empresa["situacao_cadastral"] != "ATIVA":
                continue
            if empresa["cnpj"] not in excluidos:
                encontrados.append(empresa)
        if len(encontrados) >= LEADS_POR_BUSCA or cursor is None:
            break

    return encontrados[:LEADS_POR_BUSCA]


@router.get("", response_model=list[NovoLeadOut])
def listar_novos_leads(
    uf: str | None = None,
    cnae: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cnpjs_salvos = {
        row.cnpj for row in db.query(Lead.cnpj).filter(Lead.owner_id == current_user.id)
    }
    cnpjs_ocultados = {
        row.cnpj for row in db.query(LeadOculto.cnpj).filter(LeadOculto.owner_id == current_user.id)
    }
    excluidos = cnpjs_salvos | cnpjs_ocultados

    try:
        encontrados = _buscar_leads_novos(uf or random.choice(UFS_PADRAO), cnae, excluidos)
    except cnpj_api.ConsultaIndisponivel:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "A busca de novos leads está indisponível no momento "
                "(API pública fora do ar). Tente novamente em instantes."
            ),
        )

    return [NovoLeadOut(**empresa) for empresa in encontrados]


@router.post("/ocultar", status_code=status.HTTP_204_NO_CONTENT)
def ocultar_lead(
    dados: OcultarLeadRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Canonicaliza pro mesmo formato usado pela busca (cnpj_api.formatar_cnpj)
    # — senão um CNPJ ocultado num formato diferente nunca bate com
    # `empresa["cnpj"]` em `_buscar_leads_novos` e a empresa reaparece.
    digitos = cnpj_api.somente_digitos(dados.cnpj)
    if len(digitos) != 14:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CNPJ inválido")
    cnpj_canonico = cnpj_api.formatar_cnpj(digitos)

    ja_oculto = (
        db.query(LeadOculto)
        .filter(LeadOculto.owner_id == current_user.id, LeadOculto.cnpj == cnpj_canonico)
        .first()
    )
    if not ja_oculto:
        db.add(LeadOculto(owner_id=current_user.id, cnpj=cnpj_canonico))
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
