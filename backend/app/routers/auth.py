import re
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .. import rate_limit
from ..auth import (
    agora_sem_microssegundos,
    create_access_token,
    hash_password,
    senha_excede_limite_bcrypt,
    verify_password,
)
from ..database import SessionLocal
from ..dependencies import get_current_user, get_db
from ..email_utils import enviar_email_redefinicao
from ..models import PasswordResetToken, User
from ..schemas import (
    AlterarSenhaRequest,
    EsqueciSenhaRequest,
    ExcluirContaRequest,
    LoginRequest,
    PerfilUpdateRequest,
    PerfilUpdateResponse,
    RedefinirSenhaRequest,
    RegistrarRequest,
    Token,
    UserOut,
)

SENHA_MINIMA = 6
TOKEN_RESET_VALIDADE_MINUTOS = 30
MENSAGEM_ESQUECI_SENHA = "Se o usuário existir e tiver e-mail cadastrado, enviamos um link de redefinição."

router = APIRouter(prefix="/auth", tags=["auth"])

UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

TIPOS_PERMITIDOS = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
TAMANHO_MAXIMO_BYTES = 5 * 1024 * 1024  # 5MB

EMAIL_REGEX = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

# Assinaturas (magic bytes) dos formatos aceitos no upload de foto — conferir
# isso é mais confiável do que o Content-Type enviado pelo cliente, que pode
# dizer qualquer coisa independente do conteúdo real do arquivo.
ASSINATURAS_IMAGEM = {
    "image/jpeg": (b"\xff\xd8\xff",),
    "image/png": (b"\x89PNG\r\n\x1a\n",),
    "image/webp": (b"RIFF",),  # bytes 8-11 do arquivo precisam ser "WEBP", checado à parte
}


def validar_tamanho_senha(senha: str) -> None:
    if senha_excede_limite_bcrypt(senha):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Senha muito longa",
        )


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


@router.patch("/me", response_model=PerfilUpdateResponse)
def atualizar_perfil(
    dados: PerfilUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if dados.email and not EMAIL_REGEX.match(dados.email):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="E-mail inválido")

    telefone_normalizado = None
    if dados.telefone:
        telefone_normalizado = normalizar_telefone(dados.telefone)
        if not telefone_normalizado:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Telefone inválido. Use o formato (11) 91234-5678 ou apenas os números",
            )

    if dados.username.lower() != current_user.username.lower():
        ja_existe = (
            db.query(User)
            .filter(func.lower(User.username) == dados.username.lower(), User.id != current_user.id)
            .first()
        )
        if ja_existe:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Esse nome de usuário já está em uso",
            )
        current_user.username = dados.username

    if dados.email:
        outro_com_email = (
            db.query(User)
            .filter(func.lower(User.email) == dados.email.lower(), User.id != current_user.id)
            .first()
        )
        if outro_com_email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Esse e-mail já está em uso por outra conta",
            )

    current_user.nome = dados.nome
    current_user.email = dados.email or None
    current_user.telefone = telefone_normalizado
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Esse nome de usuário já está em uso",
        )
    db.refresh(current_user)

    novo_token = create_access_token({"sub": current_user.username})
    return PerfilUpdateResponse(
        username=current_user.username,
        nome=current_user.nome,
        email=current_user.email,
        telefone=current_user.telefone,
        foto_url=current_user.foto_url,
        is_admin=current_user.is_admin,
        access_token=novo_token,
    )


def _assinatura_bate(conteudo: bytes, content_type: str) -> bool:
    assinaturas = ASSINATURAS_IMAGEM.get(content_type, ())
    if not any(conteudo.startswith(a) for a in assinaturas):
        return False
    if content_type == "image/webp":
        return conteudo[8:12] == b"WEBP"
    return True


@router.post("/me/foto", response_model=UserOut)
async def atualizar_foto(
    foto: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    extensao = TIPOS_PERMITIDOS.get(foto.content_type)
    if not extensao:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Envie uma imagem JPEG, PNG ou WEBP",
        )

    # Lê em pedaços e aborta assim que passar do limite, em vez de bufferizar
    # o upload inteiro na memória antes de checar o tamanho.
    pedacos: list[bytes] = []
    total = 0
    while True:
        pedaco = await foto.read(1024 * 1024)
        if not pedaco:
            break
        total += len(pedaco)
        if total > TAMANHO_MAXIMO_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="A imagem deve ter no máximo 5MB",
            )
        pedacos.append(pedaco)
    conteudo = b"".join(pedacos)

    if not _assinatura_bate(conteudo, foto.content_type):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="O arquivo não parece ser uma imagem válida desse formato",
        )

    if current_user.foto_url:
        (UPLOAD_DIR / Path(current_user.foto_url).name).unlink(missing_ok=True)

    nome_arquivo = f"user_{current_user.id}_{uuid.uuid4().hex[:8]}{extensao}"
    (UPLOAD_DIR / nome_arquivo).write_bytes(conteudo)

    current_user.foto_url = f"/uploads/{nome_arquivo}"
    db.commit()
    db.refresh(current_user)
    return current_user


@router.patch("/me/senha", status_code=status.HTTP_204_NO_CONTENT)
def alterar_senha(
    dados: AlterarSenhaRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not verify_password(dados.senha_atual, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Senha atual incorreta",
        )
    if len(dados.nova_senha) < SENHA_MINIMA:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"A nova senha deve ter pelo menos {SENHA_MINIMA} caracteres",
        )
    validar_tamanho_senha(dados.nova_senha)
    current_user.hashed_password = hash_password(dados.nova_senha)
    current_user.senha_alterada_em = agora_sem_microssegundos()
    # Uma senha nova invalida qualquer link de "esqueci minha senha" pendente
    # — sem isso, um token emitido antes continuaria valendo por até 30 min
    # mesmo depois da senha ter mudado por outro caminho.
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == current_user.id, PasswordResetToken.usado.is_(False)
    ).update({"usado": True})
    db.commit()


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def excluir_conta(
    dados: ExcluirContaRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not verify_password(dados.password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Senha incorreta",
        )
    if current_user.is_admin:
        outros_admins = (
            db.query(User).filter(User.is_admin.is_(True), User.id != current_user.id).count()
        )
        if outros_admins == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Você é o único administrador — promova outra conta a admin antes de excluir a sua",
            )
    if current_user.foto_url:
        (UPLOAD_DIR / Path(current_user.foto_url).name).unlink(missing_ok=True)
    db.delete(current_user)
    db.commit()


@router.post("/login", response_model=Token)
def login(dados: LoginRequest, db: Session = Depends(get_db)):
    chave_bloqueio = dados.username.strip().lower()
    if rate_limit.bloqueado(chave_bloqueio):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Muitas tentativas de login. Tente novamente em alguns minutos.",
        )

    user = db.query(User).filter(User.username == dados.username).first()
    # Roda verify_password mesmo quando o usuário não existe (contra um hash
    # fixo) para o tempo de resposta não denunciar, por timing, se o
    # username é válido ou não.
    senha_ok = verify_password(dados.password, user.hashed_password if user else None)
    if not user or not senha_ok:
        rate_limit.registrar_falha(chave_bloqueio)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha inválidos",
        )

    rate_limit.limpar(chave_bloqueio)
    token = create_access_token({"sub": user.username})
    return Token(access_token=token, nome=user.nome)


@router.post("/esqueci-senha", status_code=status.HTTP_202_ACCEPTED)
def esqueci_senha(
    dados: EsqueciSenhaRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    identificador = dados.identificador.strip()
    chave_bloqueio = f"esqueci-senha:{identificador.lower()}"
    if rate_limit.bloqueado(chave_bloqueio):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Muitos pedidos de redefinição. Tente novamente em alguns minutos.",
        )
    rate_limit.registrar_falha(chave_bloqueio)

    user = (
        db.query(User)
        .filter((User.username == identificador) | (func.lower(User.email) == identificador.lower()))
        .first()
    )
    if user and user.email:
        # Invalida links antigos ainda não usados antes de emitir um novo.
        db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user.id, PasswordResetToken.usado.is_(False)
        ).update({"usado": True})
        token = secrets.token_urlsafe(32)
        db.add(
            PasswordResetToken(
                user_id=user.id,
                token=token,
                expira_em=datetime.now(timezone.utc) + timedelta(minutes=TOKEN_RESET_VALIDADE_MINUTOS),
            )
        )
        db.commit()
        # O envio de e-mail (SMTP síncrono) roda depois da resposta ser
        # devolvida — assim o tempo de resposta não muda conforme o
        # identificador existir ou não, e o cliente não fica esperando o SMTP.
        background_tasks.add_task(_tentar_enviar_email_redefinicao, user.email, user.nome, token)

    # Limpeza oportunista: tokens já usados ou expirados não servem mais pra
    # nada, então aproveitamos essa chamada (rodando depois da resposta, sem
    # atrasar nem virar mais um sinal de timing) pra tirá-los do banco. Existe
    # também limpar_dados_antigos.py pra rodar isso (e o cache de CNPJ) por
    # fora, periodicamente — essa chamada aqui é só uma rede de segurança.
    background_tasks.add_task(_limpar_tokens_antigos)

    return {"detail": MENSAGEM_ESQUECI_SENHA}


def _tentar_enviar_email_redefinicao(email: str, nome: str, token: str) -> None:
    try:
        enviar_email_redefinicao(email, nome, token)
    except Exception as exc:
        print(f"[esqueci-senha] falha ao enviar e-mail para {email}: {exc}")


def _limpar_tokens_antigos() -> None:
    # Roda numa sessão própria — a sessão da requisição (via Depends(get_db))
    # já foi fechada quando um BackgroundTask executa.
    db = SessionLocal()
    try:
        agora = datetime.now(timezone.utc)
        db.query(PasswordResetToken).filter(
            (PasswordResetToken.usado.is_(True)) | (PasswordResetToken.expira_em < agora)
        ).delete(synchronize_session=False)
        db.commit()
    except Exception as exc:
        print(f"[limpeza] falha ao limpar tokens antigos: {exc}")
    finally:
        db.close()


@router.post("/redefinir-senha", status_code=status.HTTP_204_NO_CONTENT)
def redefinir_senha(dados: RedefinirSenhaRequest, db: Session = Depends(get_db)):
    registro = (
        db.query(PasswordResetToken)
        .filter(PasswordResetToken.token == dados.token, PasswordResetToken.usado.is_(False))
        .first()
    )
    agora = datetime.now(timezone.utc)
    if not registro or registro.expira_em.replace(tzinfo=timezone.utc) < agora:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Link inválido ou expirado")

    if len(dados.nova_senha) < SENHA_MINIMA:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"A nova senha deve ter pelo menos {SENHA_MINIMA} caracteres",
        )
    validar_tamanho_senha(dados.nova_senha)

    user = db.query(User).filter(User.id == registro.user_id).first()
    if user is None:
        # A conta foi excluída depois do link ser gerado (o cascade em
        # models.py evita isso daqui pra frente, mas não custa checar).
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Link inválido ou expirado")

    user.hashed_password = hash_password(dados.nova_senha)
    user.senha_alterada_em = agora_sem_microssegundos()
    registro.usado = True
    # Qualquer outro link de redefinição pendente pra essa conta também é
    # invalidado — não faz sentido dois links vivos ao mesmo tempo.
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.usado.is_(False),
        PasswordResetToken.id != registro.id,
    ).update({"usado": True})
    db.commit()


@router.post("/registrar", response_model=Token, status_code=status.HTTP_201_CREATED)
def registrar(dados: RegistrarRequest, db: Session = Depends(get_db)):
    if len(dados.password) < SENHA_MINIMA:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"A senha deve ter pelo menos {SENHA_MINIMA} caracteres",
        )
    validar_tamanho_senha(dados.password)
    if db.query(User).filter(func.lower(User.username) == dados.username.lower()).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Esse nome de usuário já está em uso",
        )
    user = User(
        username=dados.username,
        nome=dados.nome,
        hashed_password=hash_password(dados.password),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Esse nome de usuário já está em uso",
        )
    db.refresh(user)
    token = create_access_token({"sub": user.username})
    return Token(access_token=token, nome=user.nome)
