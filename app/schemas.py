from pydantic import BaseModel

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