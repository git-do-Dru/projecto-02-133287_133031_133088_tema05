from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from .database import Base

# 1. Tabela de Utilizadores
class Utilizador(Base):
    __tablename__ = "utilizadores"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, unique=True, index=True, nullbase=False )

# 2. Tabela de Leilões
class Leilao(Base):
    __tablename__ = "leiloes"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String, nullable=False)
    descricao = Column(String)
    preco_inicial = Column(Float, nullable=False)
    preco_atual = Column(Float, nullable=False)
    
    # Guarda a data e hora exata em que o leilão foi criado automaticamente
    criado_em = Column(DateTime(timezone=True), server_default=func.now())
    
    # Chave Estrangeira: Diz-nos qual foi o utilizador (id) que criou este leilão
    dono_id = Column(Integer, ForeignKey("utilizadores.id"))