from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class UtilizadorCreate(BaseModel):
    nome: str
    password: str


class UtilizadorResponse(BaseModel):
    id: int
    nome: str

    class Config:
        from_attributes = True


class LeilaoCreate(BaseModel):
    titulo: str
    descricao: Optional[str] = None
    preco_inicial: float
    categoria: Optional[str] = None
    localizacao: Optional[str] = None
    emoji: Optional[str] = None


class LeilaoResponse(BaseModel):
    id: int
    titulo: str
    descricao: Optional[str] = None
    preco_inicial: float
    preco_atual: float
    categoria: Optional[str] = None
    localizacao: Optional[str] = None
    emoji: Optional[str] = None
    dono_id: int
    criado_em: datetime

    class Config:
        from_attributes = True