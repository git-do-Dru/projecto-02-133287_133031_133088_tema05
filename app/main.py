import os
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import redis.asyncio as aioredis
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from . import schemas
from .database import get_db
from .database import engine, Base, get_db, AsyncSessionLocal

from .database import engine, Base
from . import models  # Obriga o Python a ler o ficheiro models.py

app = FastAPI(title="Plataforma de Leilões em Tempo Real")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = None

# O evento "startup" corre ANTES de o servidor começar a receber utilizadores
@app.on_event("startup")
async def startup_event():
    global redis_client
    redis_client = aioredis.from_url(REDIS_URL, decode_responses=True)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


    async with AsyncSessionLocal() as db:
        result = await db.execute(select(models.Leilao))
        leiloes_existentes = result.scalars().first()
        
        if not leiloes_existentes:
            # 1. Criar dois utilizadores diferentes
            vendedor = models.Utilizador(nome="Admin")
            comprador = models.Utilizador(nome="Geraldo_Alberto")
            db.add_all([vendedor, comprador])
            await db.commit()
            await db.refresh(vendedor)
            await db.refresh(comprador)
            
            # 2. Criar os leilões 
            l1 = models.Leilao(titulo="Rolex Submariner", descricao="Relógio de luxo", preco_inicial=5000.0, preco_atual=5500.0, dono_id=vendedor.id)
            l2 = models.Leilao(titulo="PlayStation 5", descricao="Nova na caixa", preco_inicial=400.0, preco_atual=460.0, dono_id=vendedor.id)
            l3 = models.Leilao(titulo="Bicicleta de Montanha Santa Cruz", descricao="Cor preta com dupla suspensao da Fox", preco_inicial=100.0, preco_atual=100.0, dono_id=vendedor.id) 
            
            db.add_all([l1, l2, l3])
            await db.commit()
            await db.refresh(l1)
            await db.refresh(l2)
            
            # 3. Registar o histórico dos lances no sistema!
            lance_rolex = models.Licitacao(valor=5500.0, leilao_id=l1.id, utilizador_id=comprador.id)
            lance_ps5 = models.Licitacao(valor=460.0, leilao_id=l2.id, utilizador_id=comprador.id)
            
            db.add_all([lance_rolex, lance_ps5])
            await db.commit()

@app.get("/")

# Metodo que faz a criacao de user (contem apenas o nickname)
@app.post("/entrar", response_model=schemas.UtilizadorResponse)
async def entrar_na_plataforma(utilizador: schemas.UtilizadorCreate, db: AsyncSession = Depends(get_db)):
    
    # 1. Vai à base de dados procurar se este Nick já existe
    result = await db.execute(select(models.Utilizador).where(models.Utilizador.nome == utilizador.nome))
    db_user = result.scalars().first()
    
    # 2. Se já existir, devolvemos esse utilizador (Login com sucesso)
    if db_user:
        return db_user
        
    # 3. Se não existir, criamos um novo!
    novo_utilizador = models.Utilizador(nome=utilizador.nome)
    db.add(novo_utilizador)
    await db.commit() # Guarda na base de dados
    await db.refresh(novo_utilizador) # Atualiza a variável para descobrirmos que "id" lhe foi dado
    
    return novo_utilizador

async def read_root():
    return {
        "status": "API REST Ativa",
        "projeto": "Tema 5 - Leilões Online",
        "ambiente": "Dockerizado"
    }

@app.websocket("/ws/leilao/{leilao_id}")
async def websocket_endpoint(websocket: WebSocket, leilao_id: str):
    await websocket.accept()
    
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(f"leilao:{leilao_id}")
    
    async def redis_listener():
        try:
            while True:
                message = await pubsub.get_message(ignore_subscribe_messages=True)
                if message and message["type"] == "message":
                    await websocket.send_text(f"Broadcast: {message['data']}")
                await asyncio.sleep(0.1)
        except Exception:
            pass

    listener_task = asyncio.create_task(redis_listener())

    try:
        while True:
            data = await websocket.receive_text()
            await redis_client.publish(f"leilao:{leilao_id}", f"Nova licitação recebida: {data}")
            
    except WebSocketDisconnect:
        listener_task.cancel()
        await pubsub.unsubscribe(f"leilao:{leilao_id}")
        await websocket.close()




#--- ROTAS DO MENU DE LEILÕES ---

@app.post("/leiloes", response_model=schemas.LeilaoResponse)
async def anunciar_item(leilao: schemas.LeilaoCreate, dono_id: int, db: AsyncSession = Depends(get_db)):
    """Rota para um utilizador criar um leilão novo"""
    novo_leilao = models.Leilao(
        titulo=leilao.titulo,
        descricao=leilao.descricao,
        preco_inicial=leilao.preco_inicial,
        preco_atual=leilao.preco_inicial, 
        dono_id=dono_id
    )
    db.add(novo_leilao)
    await db.commit()
    await db.refresh(novo_leilao)
    return novo_leilao

@app.get("/leiloes", response_model=list[schemas.LeilaoResponse])
async def listar_montra(db: AsyncSession = Depends(get_db)):
    """Rota para listar todos os leilões ativos na plataforma"""
    result = await db.execute(select(models.Leilao))
    lista_de_leiloes = result.scalars().all()
    return lista_de_leiloes