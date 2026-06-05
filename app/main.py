import os
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import redis.asyncio as aioredis

app = FastAPI(title="Plataforma de Leilões em Tempo Real - DETI")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = None

@app.on_event("startup")
async def startup_event():
    global redis_client
    # Inicializa o cliente Redis assíncrono
    redis_client = aioredis.from_url(REDIS_URL, decode_responses=True)

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
    
    # Criar um cliente pubsub dedicado para esta conexão WebSocket
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(f"leilao:{leilao_id}")
    
    # Tarefa em segundo plano para escutar mensagens do Redis e enviar ao cliente
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
            # Escuta novas licitações vindas DESTE cliente WebSocket específico
            data = await websocket.receive_text()
            
            # [Lógica Futura]: Validar transação atómica aqui usando o Redis.
            # Se for válida, fazemos Publish para avisar TODOS os clientes na sala:
            await redis_client.publish(f"leilao:{leilao_id}", f"Nova licitação recebida: {data}")
            
    except WebSocketDisconnect:
        # Limpeza quando o utilizador fecha a página ou cai a net
        listener_task.cancel()
        await pubsub.unsubscribe(f"leilao:{leilao_id}")
        await websocket.close()