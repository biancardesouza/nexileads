import re
import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import rate_limit
from ..auth import create_access_token
from ..bubble_client import BubbleIndisponivel, autenticar_no_bubble
from ..dependencies import get_current_user, get_db
from ..models import User
from ..schemas import LoginRequest, Token, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


def normalizar_telefone(telefone: str) -> str | None:
    """Aceita o telefone com ou sem formatação (só dígitos, ou com DDD/traço)
    e devolve sempre no formato (11) 91234-5678. Retorna None se inválido."""
    digitos = re.sub(r"\D", "", telefone)
    if len(digitos) == 11:
        return f"({digitos[0:2]}) {digitos[2:7]}-{digitos[7:11]}"
    if len(digitos) == 10:
        return f"({digitos[0:2]}) {digitos[2:6]}-{digitos[6:10]}"
    return None


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user


def _sincronizar_usuario_bubble(db: Session, dados_bubble: dict) -> User:
    """Encontra (ou cria) a linha local correspondente à conta do Bubble que
    acabou de autenticar, e sincroniza os campos vindos de lá.

    Nomes de campo (`name`, `telephone`, `photo_url`) confirmados testando o
    workflow real no Bubble — não são só suposição."""
    bubble_id = dados_bubble.get("id") or dados_bubble.get("user_id")
    email = dados_bubble.get("email")
    nome = dados_bubble.get("name") or email
    telefone_bruto = dados_bubble.get("telephone")
    telefone = normalizar_telefone(telefone_bruto) if telefone_bruto else None
    foto_url = dados_bubble.get("photo_url")

    user = db.query(User).filter(User.bubble_user_id == bubble_id).first()
    if user is None and email:
        # Linka uma conta local pré-existente (criada antes da integração com
        # o Bubble) pelo e-mail, uma única vez — depois disso ela já tem
        # bubble_user_id e cai no filtro acima.
        user = db.query(User).filter(func.lower(User.email) == email.lower()).first()

    if user is None:
        user = User(
            username=email,
            nome=nome,
            # Ninguém verifica esse hash — o Bubble é quem autentica. É só um
            # valor opaco pra satisfazer o NOT NULL da coluna.
            hashed_password=secrets.token_urlsafe(32),
        )
        db.add(user)

    user.bubble_user_id = bubble_id
    user.nome = nome
    user.email = email
    if telefone:
        user.telefone = telefone
    if foto_url:
        user.foto_url = foto_url

    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(dados: LoginRequest, db: Session = Depends(get_db)):
    chave_bloqueio = dados.email.strip().lower()
    if rate_limit.bloqueado(chave_bloqueio):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Muitas tentativas de login. Tente novamente em alguns minutos.",
        )

    try:
        dados_bubble = autenticar_no_bubble(dados.email, dados.password)
    except BubbleIndisponivel:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Não foi possível validar seu login agora. Tente novamente em instantes.",
        )

    if dados_bubble is None:
        rate_limit.registrar_falha(chave_bloqueio)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha inválidos",
        )

    rate_limit.limpar(chave_bloqueio)
    user = _sincronizar_usuario_bubble(db, dados_bubble)
    token = create_access_token({"sub": user.username})
    return Token(access_token=token, nome=user.nome)
