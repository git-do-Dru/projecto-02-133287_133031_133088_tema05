import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

#1. Recuperar o URL da Base de Dados das variáveis de ambiente do Docker

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("A variável de ambiente DATABASE_URL não foi definida!")

# 2. Criar o Motor (Engine) Assíncrono

engine = create_async_engine(DATABASE_URL, echo=True)

# 3. Criar a Fábrica de Sessões (Session Factory)
AsyncSessionLocal = async_sessionmaker(
    bind=engine, 
    autoflush=False, 
    autocommit=False, 
    expire_on_commit=False
)

# 4. Criar a Classe Base para os Modelos
Base = declarative_base()

# 5. O "Injetor de Dependência" (A função mágica do FastAPI)
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()