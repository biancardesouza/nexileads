import secrets
import string
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..auth import agora_sem_microssegundos, hash_password, senha_excede_limite_bcrypt
from ..dependencies import get_current_admin, get_db
from ..models import LogAuditoria, PasswordResetToken, User
from ..schemas import AdminCreateUserRequest, AdminResetSenhaResponse, AdminUserOut, LogAuditoriaOut
from .auth import SENHA_MINIMA, UPLOAD_DIR

router = APIRouter(prefix="/admin", tags=["admin"])

ALFABETO_SENHA = string.ascii_letters + string.digits

LIMITE_AUDITORIA = 200


def gerar_senha_temporaria(tamanho: int = 10) -> str:
    return "".join(secrets.choice(ALFABETO_SENHA) for _ in range(tamanho))


def _registrar_auditoria(
    db: Session, admin: User, acao: str, alvo_username: str, detalhes: str | None = None
) -> None:
    db.add(
        LogAuditoria(
            admin_username=admin.username,
            acao=acao,
            alvo_username=alvo_username,
            detalhes=detalhes,
        )
    )


def _para_admin_user_out(user: User) -> AdminUserOut:
    return AdminUserOut(
        id=user.id,
        username=user.username,
        nome=user.nome,
        email=user.email,
        telefone=user.telefone,
        is_admin=user.is_admin,
        total_leads=len(user.leads),
    )


@router.get("/usuarios", response_model=list[AdminUserOut])
def listar_usuarios(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    usuarios = db.query(User).order_by(User.id).all()
    return [_para_admin_user_out(u) for u in usuarios]


@router.post("/usuarios", response_model=AdminUserOut, status_code=status.HTTP_201_CREATED)
def criar_usuario(
    dados: AdminCreateUserRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    if len(dados.password) < SENHA_MINIMA:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"A senha deve ter pelo menos {SENHA_MINIMA} caracteres",
        )
    if senha_excede_limite_bcrypt(dados.password):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Senha muito longa")
    if db.query(User).filter(func.lower(User.username) == dados.username.lower()).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Esse nome de usuário já está em uso",
        )
    user = User(
        username=dados.username,
        nome=dados.nome,
        hashed_password=hash_password(dados.password),
        is_admin=dados.is_admin,
    )
    db.add(user)
    _registrar_auditoria(
        db, current_admin, "criar_usuario", dados.username,
        detalhes="como administrador" if dados.is_admin else None,
    )
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Esse nome de usuário já está em uso",
        )
    db.refresh(user)
    return _para_admin_user_out(user)


@router.post("/usuarios/{user_id}/resetar-senha", response_model=AdminResetSenhaResponse)
def resetar_senha(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")

    nova_senha = gerar_senha_temporaria()
    user.hashed_password = hash_password(nova_senha)
    user.senha_alterada_em = agora_sem_microssegundos()
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id, PasswordResetToken.usado.is_(False)
    ).update({"usado": True})
    _registrar_auditoria(db, current_admin, "resetar_senha", user.username)
    db.commit()
    return AdminResetSenhaResponse(nova_senha=nova_senha)


@router.delete("/usuarios/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_usuario(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    if user_id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Você não pode excluir sua própria conta por aqui",
        )
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")

    if user.foto_url:
        (UPLOAD_DIR / Path(user.foto_url).name).unlink(missing_ok=True)
    _registrar_auditoria(
        db, current_admin, "excluir_usuario", user.username,
        detalhes=f"{len(user.leads)} lead(s) removido(s) junto",
    )
    db.delete(user)
    db.commit()


@router.get("/auditoria", response_model=list[LogAuditoriaOut])
def listar_auditoria(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    return (
        db.query(LogAuditoria)
        .order_by(LogAuditoria.criado_em.desc())
        .limit(LIMITE_AUDITORIA)
        .all()
    )
