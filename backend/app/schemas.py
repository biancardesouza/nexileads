from datetime import datetime

from pydantic import BaseModel, ConfigDict


class LoginRequest(BaseModel):
    username: str
    password: str


class RegistrarRequest(BaseModel):
    username: str
    password: str
    nome: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    nome: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    username: str
    nome: str
    email: str | None = None
    telefone: str | None = None
    foto_url: str | None = None
    is_admin: bool = False


class PerfilUpdateRequest(BaseModel):
    username: str
    nome: str
    email: str | None = None
    telefone: str | None = None


class PerfilUpdateResponse(UserOut):
    access_token: str


class ExcluirContaRequest(BaseModel):
    password: str


class AlterarSenhaRequest(BaseModel):
    senha_atual: str
    nova_senha: str


class EsqueciSenhaRequest(BaseModel):
    identificador: str


class RedefinirSenhaRequest(BaseModel):
    token: str
    nova_senha: str


class RegistroLigacaoCreate(BaseModel):
    status: str
    nota: str = ""


class RegistroLigacaoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: str
    nota: str
    criado_em: datetime


class LeadBase(BaseModel):
    razao_social: str
    cnpj: str
    uf: str
    municipio: str
    telefone: str
    email: str
    segmento: str


class LeadCreate(LeadBase):
    pass


class ConsultaCnpjOut(LeadBase):
    situacao_cadastral: str = ""
    fonte: str = ""


class LeadOut(LeadBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    criado_em: datetime
    registros: list[RegistroLigacaoOut] = []


class NovoLeadOut(LeadBase):
    model_config = ConfigDict(from_attributes=True)


class OcultarLeadRequest(BaseModel):
    cnpj: str


class AdminUserOut(BaseModel):
    id: int
    username: str
    nome: str
    email: str | None = None
    telefone: str | None = None
    is_admin: bool
    total_leads: int


class AdminCreateUserRequest(BaseModel):
    username: str
    nome: str
    password: str
    is_admin: bool = False


class AdminResetSenhaResponse(BaseModel):
    nova_senha: str


class LogAuditoriaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    admin_username: str
    acao: str
    alvo_username: str
    detalhes: str | None = None
    criado_em: datetime
