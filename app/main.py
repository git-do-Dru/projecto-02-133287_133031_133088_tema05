import os
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import redis.asyncio as aioredis

# --- NOVOS IMPORTS PARA A BASE DE DADOS ---
from .database import engine, Base
from . import models  # Obriga o Python a ler o ficheiro models.py

app = FastAPI(title="Plataforma de Leilões em Tempo Real")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = None

# O evento "startup" corre ANTES de o servidor começar a receber utilizadores
@app.on_event("startup")
async def startup_event():
    global redis_client
    
    # 1. Inicializa o cliente Redis assíncrono
    redis_client = aioredis.from_url(REDIS_URL, decode_responses=True)
    
    # 2. A MAGIA DA BASE DE DADOS:
    # Este comando diz ao motor (engine) para ir ao PostgreSQL e criar fisicamente 
    # todas as tabelas que herdam de 'Base' (as tabelas do models.py) se elas ainda não existirem.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("🚀 Tabelas da Base de Dados criadas/verificadas com sucesso!")

@app.get("/")
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