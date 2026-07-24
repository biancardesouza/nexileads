import re
import secrets

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import rate_limit
from ..auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    COOKIE_SAMESITE,
    COOKIE_SECURE,
    TOKEN_COOKIE_NAME,
    create_access_token,
)
from ..bubble_client import BubbleIndisponivel, autenticar_no_bubble
from ..dependencies import get_current_user, get_db
from ..models import User
from ..schemas import LoginOut, LoginRequest, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


def obter_ip_cliente(request: Request) -> str | None:
    """Atrás do load balancer do Render, request.client.host é o IP do proxy,
    não o do usuário — usamos o X-Forwarded-For que a plataforma preenche com
    o IP original, caindo pro IP da conexão direta em dev local (sem proxy)."""
    encaminhado = request.headers.get("x-forwarded-for")
    if encaminhado:
        return encaminhado.split(",")[0].strip()
    return request.client.host if request.client else None


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


@router.post("/login", response_model=LoginOut)
def login(dados: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    chave_bloqueio = dados.email.strip().lower()
    ip_cliente = obter_ip_cliente(request)
    chave_ip = f"ip:{ip_cliente}" if ip_cliente else None

    bloqueado_por_email = rate_limit.bloqueado(chave_bloqueio)
    bloqueado_por_ip = chave_ip is not None and rate_limit.bloqueado(chave_ip, limite=rate_limit.LIMITE_IP)
    if bloqueado_por_email or bloqueado_por_ip:
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
        if chave_ip:
            rate_limit.registrar_falha(chave_ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha inválidos",
        )

    # Só limpa o bloqueio da conta que acabou de autenticar com sucesso — o
    # contador por IP continua contando as falhas de outras contas testadas
    # a partir dele, senão um ataque de credential-stuffing conseguiria
    # "resetar" a própria proteção por IP só acertando uma credencial válida
    # no meio de várias tentativas.
    rate_limit.limpar(chave_bloqueio)
    user = _sincronizar_usuario_bubble(db, dados_bubble)
    token = create_access_token({"sub": user.username})
    # httpOnly: o token nunca fica acessível pra JS no navegador (nem em
    # localStorage, nem lido do corpo desta resposta) — protege contra roubo
    # de sessão via XSS. O front não precisa mais guardar nada: o cookie é
    # enviado automaticamente pelo navegador em cada requisição seguinte.
    response.set_cookie(
        key=TOKEN_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )
    return LoginOut(nome=user.nome)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response):
    # Sendo httpOnly, o front não consegue apagar esse cookie por conta
    # própria — precisa desse endpoint pra fazer o navegador descartá-lo.
    response.delete_cookie(
        key=TOKEN_COOKIE_NAME,
        path="/",
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
    )
