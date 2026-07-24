from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    email: str = Field(min_length=1)
    password: str = Field(min_length=1)


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
