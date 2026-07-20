from datetime import datetime, timezone

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def _agora():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(unique=True, index=True)
    nome: Mapped[str]
    hashed_password: Mapped[str]
    email: Mapped[str | None] = mapped_column(default=None)
    telefone: Mapped[str | None] = mapped_column(default=None)
    foto_url: Mapped[str | None] = mapped_column(default=None)
    is_admin: Mapped[bool] = mapped_column(default=False)
    senha_alterada_em: Mapped[datetime | None] = mapped_column(default=None)

    leads: Mapped[list["Lead"]] = relationship(back_populates="owner", cascade="all, delete-orphan")
    leads_ocultos: Mapped[list["LeadOculto"]] = relationship(back_populates="owner", cascade="all, delete-orphan")
    reset_tokens: Mapped[list["PasswordResetToken"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Lead(Base):
    __tablename__ = "leads"
    __table_args__ = (UniqueConstraint("owner_id", "cnpj", name="uq_lead_owner_cnpj"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    razao_social: Mapped[str]
    cnpj: Mapped[str] = mapped_column(index=True)
    uf: Mapped[str]
    municipio: Mapped[str]
    telefone: Mapped[str]
    email: Mapped[str]
    segmento: Mapped[str]
    status: Mapped[str] = mapped_column(default="sem_contato")
    criado_em: Mapped[datetime] = mapped_column(default=_agora)

    owner: Mapped["User"] = relationship(back_populates="leads")
    registros: Mapped[list["RegistroLigacao"]] = relationship(
        back_populates="lead",
        cascade="all, delete-orphan",
        order_by="desc(RegistroLigacao.criado_em)",
    )


class RegistroLigacao(Base):
    __tablename__ = "registros_ligacao"

    id: Mapped[int] = mapped_column(primary_key=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("leads.id"))
    status: Mapped[str]
    nota: Mapped[str]
    criado_em: Mapped[datetime] = mapped_column(default=_agora)

    lead: Mapped["Lead"] = relationship(back_populates="registros")


class LeadOculto(Base):
    __tablename__ = "leads_ocultos"
    __table_args__ = (UniqueConstraint("owner_id", "cnpj", name="uq_oculto_owner_cnpj"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    cnpj: Mapped[str] = mapped_column(index=True)

    owner: Mapped["User"] = relationship(back_populates="leads_ocultos")


class CnpjConsulta(Base):
    """Cache local de consultas a APIs públicas de CNPJ (BrasilAPI/OpenCNPJ).

    Evita bater na API externa de novo para o mesmo CNPJ em pouco tempo — a
    base da Receita é atualizada mensalmente, então cache por
    `CNPJ_CACHE_DIAS` (ver routers/leads.py) é seguro e reduz a dependência de
    serviços de terceiros sem SLA.
    """

    __tablename__ = "cnpj_consultas"

    id: Mapped[int] = mapped_column(primary_key=True)
    cnpj: Mapped[str] = mapped_column(unique=True, index=True)
    razao_social: Mapped[str]
    uf: Mapped[str]
    municipio: Mapped[str]
    telefone: Mapped[str]
    email: Mapped[str]
    segmento: Mapped[str]
    situacao_cadastral: Mapped[str] = mapped_column(default="")
    fonte: Mapped[str] = mapped_column(default="")
    consultado_em: Mapped[datetime] = mapped_column(default=_agora)


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    token: Mapped[str] = mapped_column(unique=True, index=True)
    criado_em: Mapped[datetime] = mapped_column(default=_agora)
    expira_em: Mapped[datetime]
    usado: Mapped[bool] = mapped_column(default=False)

    user: Mapped["User"] = relationship(back_populates="reset_tokens")


class LogAuditoria(Base):
    """Histórico de ações do admin sobre contas de usuário.

    Guarda username em texto (não FK) de propósito — o registro precisa
    sobreviver mesmo depois que a conta alvo (ou até o admin) for excluída,
    senão o log perderia justamente as exclusões, que são a ação mais
    importante de registrar.
    """

    __tablename__ = "logs_auditoria"

    id: Mapped[int] = mapped_column(primary_key=True)
    admin_username: Mapped[str]
    acao: Mapped[str]
    alvo_username: Mapped[str]
    detalhes: Mapped[str | None] = mapped_column(default=None)
    criado_em: Mapped[datetime] = mapped_column(default=_agora)
