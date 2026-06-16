from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# 1. O que o user nos envia
class UtilizadorCreate(BaseModel):
    nome: str

# 2. O que nós DEVOLVEMOS ao utilizador
# (Devolvemos o Nick e o ID que o PostgreSQL lhe atribuiu)
class UtilizadorResponse(BaseModel):
    id: int
    nome: str

    # Esta configuração é obrigatória para o Pydantic conseguir ler os dados do SQLAlchemy (Base de Dados)
    class Config:
        from_attributes = True

# --- LEILÕES (O QUE ADICIONÁMOS AGORA) ---

# 1. O que o utilizador ENVIA para anunciar um item
class LeilaoCreate(BaseModel):
    titulo: str
    descricao: Optional[str] = None  # Optional significa que o utilizador pode deixar a descrição em branco
    preco_inicial: float

# 2. O que nós DEVOLVEMOS para mostrar na montra do "OLX"
class LeilaoResponse(BaseModel):
    id: int
    titulo: str
    descricao: Optional[str] = None
    preco_inicial: float
    preco_atual: float
    dono_id: int
    criado_em: datetime

    class Config:
        from_attributes = True
