from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from .database import Base


class Utilizador(Base):
    __tablename__ = "utilizadores"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=True)
    carteira = Column(Float, nullable=False, default=10000.0)


class Leilao(Base):
    __tablename__ = "leiloes"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String, nullable=False)
    descricao = Column(String)
    preco_inicial = Column(Float, nullable=False)
    preco_atual = Column(Float, nullable=False)
    categoria = Column(String, nullable=True)
    localizacao = Column(String, nullable=True)
    emoji = Column(String, nullable=True)
    criado_em = Column(DateTime(timezone=True), server_default=func.now())
    dono_id = Column(Integer, ForeignKey("utilizadores.id"))


class Licitacao(Base):
    __tablename__ = "licitacoes"

    id = Column(Integer, primary_key=True, index=True)
    valor = Column(Float, nullable=False)
    criado_em = Column(DateTime(timezone=True), server_default=func.now())
    leilao_id = Column(Integer, ForeignKey("leiloes.id"))
    utilizador_id = Column(Integer, ForeignKey("utilizadores.id"))
