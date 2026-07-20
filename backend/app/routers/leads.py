from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .. import cnpj_api
from ..dependencies import get_current_user, get_db
from ..models import CnpjConsulta, Lead, RegistroLigacao, User
from ..schemas import ConsultaCnpjOut, LeadCreate, LeadOut, RegistroLigacaoCreate

router = APIRouter(prefix="/leads", tags=["leads"])

# A base da Receita Federal é atualizada mensalmente — não faz sentido bater
# na API pública de novo para o mesmo CNPJ com mais frequência que isso.
CNPJ_CACHE_DIAS = 30


@router.get("/consultar-cnpj/{cnpj:path}", response_model=ConsultaCnpjOut)
def consultar_cnpj(
    cnpj: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Busca dados de uma empresa por CNPJ em APIs públicas (BrasilAPI/OpenCNPJ)
    para preencher automaticamente o formulário de novo lead — sem precisar
    baixar ou processar a base completa da Receita Federal.
    """
    digitos = cnpj_api.somente_digitos(cnpj)
    if len(digitos) != 14:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CNPJ inválido")

    cache = db.query(CnpjConsulta).filter(CnpjConsulta.cnpj == digitos).first()
    if cache is not None:
        idade = datetime.now(timezone.utc) - cache.consultado_em.replace(tzinfo=timezone.utc)
        if idade < timedelta(days=CNPJ_CACHE_DIAS):
            return ConsultaCnpjOut(
                razao_social=cache.razao_social,
                cnpj=cnpj_api.formatar_cnpj(cache.cnpj),
                uf=cache.uf,
                municipio=cache.municipio,
                telefone=cache.telefone,
                email=cache.email,
                segmento=cache.segmento,
                situacao_cadastral=cache.situacao_cadastral,
                fonte=f"{cache.fonte} (cache)",
            )

    try:
        dados = cnpj_api.consultar_cnpj(digitos)
    except cnpj_api.CnpjInvalido:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CNPJ inválido")
    except cnpj_api.CnpjNaoEncontrado:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CNPJ não encontrado")
    except cnpj_api.ConsultaIndisponivel:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Não foi possível consultar o CNPJ agora. Tente novamente em instantes.",
        )

    nova_entrada = cache is None
    if nova_entrada:
        cache = CnpjConsulta(cnpj=digitos)
        db.add(cache)
    cache.razao_social = dados["razao_social"]
    cache.uf = dados["uf"]
    cache.municipio = dados["municipio"]
    cache.telefone = dados["telefone"]
    cache.email = dados["email"]
    cache.segmento = dados["segmento"]
    cache.situacao_cadastral = dados["situacao_cadastral"]
    cache.fonte = dados["fonte"]
    cache.consultado_em = datetime.now(timezone.utc)
    try:
        db.commit()
    except IntegrityError:
        # Duas requisições quase simultâneas para o mesmo CNPJ ainda não
        # cacheado: a outra já inseriu a linha entre nossa leitura e nosso
        # commit. Não é um erro de verdade — só usamos o que ela já salvou.
        db.rollback()
        if nova_entrada:
            cache = db.query(CnpjConsulta).filter(CnpjConsulta.cnpj == digitos).first()

    return ConsultaCnpjOut(**dados)


@router.get("", response_model=list[LeadOut])
def listar_leads(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(Lead)
        .filter(Lead.owner_id == current_user.id)
        .order_by(Lead.id.desc())
        .all()
    )


@router.post("", response_model=LeadOut, status_code=status.HTTP_201_CREATED)
def adicionar_lead(
    dados: LeadCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Canonicaliza o CNPJ (mesmo formato sempre) antes de comparar/guardar —
    # sem isso, a mesma empresa enviada com pontuação diferente escaparia da
    # checagem de duplicado e do UniqueConstraint(owner_id, cnpj).
    digitos = cnpj_api.somente_digitos(dados.cnpj)
    if len(digitos) != 14:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CNPJ inválido")
    cnpj_canonico = cnpj_api.formatar_cnpj(digitos)

    ja_existe = (
        db.query(Lead)
        .filter(Lead.owner_id == current_user.id, Lead.cnpj == cnpj_canonico)
        .first()
    )
    if ja_existe:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Esse lead já está na sua lista",
        )
    dados_lead = dados.model_dump()
    dados_lead["cnpj"] = cnpj_canonico
    lead = Lead(owner_id=current_user.id, status="sem_contato", **dados_lead)
    db.add(lead)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Esse lead já está na sua lista",
        )
    db.refresh(lead)
    return lead


@router.delete("/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_lead(
    lead_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    lead = (
        db.query(Lead)
        .filter(Lead.id == lead_id, Lead.owner_id == current_user.id)
        .first()
    )
    if not lead:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead não encontrado")
    db.delete(lead)
    db.commit()


@router.post("/{lead_id}/registros", response_model=LeadOut)
def salvar_registro(
    lead_id: int,
    dados: RegistroLigacaoCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    lead = (
        db.query(Lead)
        .filter(Lead.id == lead_id, Lead.owner_id == current_user.id)
        .first()
    )
    if not lead:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead não encontrado")

    registro = RegistroLigacao(
        lead_id=lead.id,
        status=dados.status,
        nota=dados.nota or "(sem anotação)",
    )
    lead.status = dados.status
    db.add(registro)
    db.commit()
    db.refresh(lead)
    return lead
