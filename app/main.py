import os
import asyncio
import json
import hashlib
import secrets
from datetime import datetime, timezone

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

import redis.asyncio as aioredis

from sqlalchemy import text, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from . import schemas, models, crud
from .database import engine, Base, get_db, AsyncSessionLocal


app = FastAPI(title="Plataforma de Leilões em Tempo Real")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = None
ultimo_heartbeat_bots = None


def criar_password_hash(password: str) -> str:
    salt = secrets.token_hex(16)
    hash_bytes = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        100_000
    )
    return f"pbkdf2_sha256${salt}${hash_bytes.hex()}"


def verificar_password(password: str, password_hash: str) -> bool:
    try:
        algoritmo, salt, hash_guardado = password_hash.split("$")

        if algoritmo != "pbkdf2_sha256":
            return False

        hash_bytes = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            100_000
        )

        return secrets.compare_digest(hash_bytes.hex(), hash_guardado)
    except Exception:
        return False


def bots_estao_ativos() -> bool:
    if ultimo_heartbeat_bots is None:
        return False

    agora = datetime.now(timezone.utc)
    diferenca = (agora - ultimo_heartbeat_bots).total_seconds()

    return diferenca <= 8


async def garantir_colunas_extra():
    async with engine.begin() as conn:
        await conn.execute(text("ALTER TABLE utilizadores ADD COLUMN IF NOT EXISTS password_hash VARCHAR"))
        await conn.execute(text("ALTER TABLE utilizadores ADD COLUMN IF NOT EXISTS carteira FLOAT DEFAULT 10000"))
        await conn.execute(text("ALTER TABLE leiloes ADD COLUMN IF NOT EXISTS categoria VARCHAR"))
        await conn.execute(text("ALTER TABLE leiloes ADD COLUMN IF NOT EXISTS localizacao VARCHAR"))
        await conn.execute(text("ALTER TABLE leiloes ADD COLUMN IF NOT EXISTS emoji VARCHAR"))


async def obter_ou_criar_utilizador(db: AsyncSession, nome: str, password: str = "bot"):
    result = await db.execute(
        select(models.Utilizador).where(models.Utilizador.nome == nome)
    )
    utilizador = result.scalars().first()

    if utilizador:
        if not getattr(utilizador, "password_hash", None):
            utilizador.password_hash = criar_password_hash(password)

        if getattr(utilizador, "carteira", None) is None:
            utilizador.carteira = 10000.0

        await db.commit()
        await db.refresh(utilizador)

        return utilizador

    utilizador = models.Utilizador(
        nome=nome,
        password_hash=criar_password_hash(password),
        carteira=10000.0
    )

    db.add(utilizador)
    await db.commit()
    await db.refresh(utilizador)

    return utilizador


async def criar_ou_atualizar_leilao(
    db: AsyncSession,
    titulo: str,
    descricao: str,
    preco: float,
    dono_id: int,
    categoria: str,
    localizacao: str,
    emoji: str
):
    result = await db.execute(
        select(models.Leilao).where(models.Leilao.titulo == titulo)
    )
    existente = result.scalars().first()

    if existente:
        existente.descricao = descricao
        existente.categoria = categoria
        existente.localizacao = localizacao
        existente.emoji = emoji
        existente.preco_inicial = preco
        existente.preco_atual = preco
        existente.dono_id = dono_id

        await db.commit()
        await db.refresh(existente)
        return existente

    novo = models.Leilao(
        titulo=titulo,
        descricao=descricao,
        preco_inicial=preco,
        preco_atual=preco,
        dono_id=dono_id,
        categoria=categoria,
        localizacao=localizacao,
        emoji=emoji
    )

    db.add(novo)
    await db.commit()
    await db.refresh(novo)

    return novo


async def criar_leiloes_padrao(db: AsyncSession):
    vendedor = await obter_ou_criar_utilizador(db, "Admin", "admin")

    await criar_ou_atualizar_leilao(
        db,
        "Rolex Submariner",
        "Relógio de luxo automático, caixa em aço inoxidável, resistente à água e em excelente estado de conservação. Ideal para colecionadores ou para quem procura uma peça premium.",
        5500.0,
        vendedor.id,
        "Luxo",
        "Porto",
        "⌚"
    )

    await criar_ou_atualizar_leilao(
        db,
        "PlayStation 5",
        "Consola PlayStation 5 praticamente nova, com comando DualSense incluído, cabos originais e caixa. Ideal para jogos atuais, 4K e tempos de carregamento rápidos.",
        400.0,
        vendedor.id,
        "Gaming",
        "Aveiro",
        "🎮"
    )

    await criar_ou_atualizar_leilao(
        db,
        "Bicicleta de Montanha Santa Cruz",
        "Bicicleta de montanha Santa Cruz em cor preta, com dupla suspensão Fox, travões de disco e quadro robusto. Indicada para trilhos, downhill ligeiro e uso desportivo.",
        100.0,
        vendedor.id,
        "Desporto",
        "Coimbra",
        "🚲"
    )

    await criar_ou_atualizar_leilao(
        db,
        "MacBook Pro 14 M3",
        "Portátil Apple em excelente estado, processador M3, 16GB de RAM, 512GB SSD, ecrã Liquid Retina XDR e bateria com boa autonomia.",
        1200.0,
        vendedor.id,
        "Tecnologia",
        "Aveiro",
        "💻"
    )

    await criar_ou_atualizar_leilao(
        db,
        "BMW Série 3 320d",
        "BMW Série 3 320d diesel, caixa automática, bom estado geral, revisão recente, interior cuidado e consumo equilibrado para viagens longas.",
        8500.0,
        vendedor.id,
        "Automóveis",
        "Porto",
        "🚗"
    )

    await criar_ou_atualizar_leilao(
        db,
        "Samsung Neo QLED 55",
        "Televisão Samsung Neo QLED de 55 polegadas, resolução 4K, Smart TV, HDR, boa qualidade de imagem e ideal para filmes, séries e gaming.",
        550.0,
        vendedor.id,
        "Imagem e Som",
        "Coimbra",
        "📺"
    )

    await criar_ou_atualizar_leilao(
        db,
        "Fender Stratocaster",
        "Guitarra elétrica Fender Stratocaster, som clássico, indicada para rock, blues e gravação. Corpo confortável e boa resposta nos pickups.",
        700.0,
        vendedor.id,
        "Música",
        "Lisboa",
        "🎸"
    )


async def limpar_demo(db: AsyncSession):
    await db.execute(delete(models.Licitacao))
    await db.execute(delete(models.Leilao))

    await db.execute(
        update(models.Utilizador).values(carteira=10000.0)
    )

    await db.commit()

    await criar_leiloes_padrao(db)


async def obter_utilizador_por_id(db: AsyncSession, utilizador_id: int):
    result = await db.execute(
        select(models.Utilizador).where(models.Utilizador.id == utilizador_id)
    )
    return result.scalars().first()


async def publicar_lance_no_redis(leilao_id: int, anuncio: dict):
    if redis_client:
        await redis_client.publish(f"leilao:{leilao_id}", json.dumps(anuncio))


async def processar_lance(
    leilao_id: int,
    valor: float,
    utilizador_id: int | None = None,
    nome: str | None = None
):
    async with AsyncSessionLocal() as db:
        utilizador = None

        if utilizador_id is not None:
            utilizador = await obter_utilizador_por_id(db, utilizador_id)

        if not utilizador and nome:
            utilizador = await obter_ou_criar_utilizador(db, nome, "bot")

        if not utilizador:
            return {
                "sucesso": False,
                "mensagem": "Utilizador inválido."
            }

        if getattr(utilizador, "carteira", None) is None:
            utilizador.carteira = 10000.0
            await db.commit()
            await db.refresh(utilizador)

        if valor <= 0:
            return {
                "sucesso": False,
                "mensagem": "O lance tem de ser positivo."
            }

        result = await db.execute(
            select(models.Leilao).where(models.Leilao.id == leilao_id)
        )
        leilao = result.scalars().first()

        if not leilao:
            return {
                "sucesso": False,
                "mensagem": "Leilão não encontrado."
            }

        aumento = valor - leilao.preco_atual

        if aumento <= 0:
            return {
                "sucesso": False,
                "mensagem": f"Lance inválido. O valor tem de ser maior que {leilao.preco_atual}€."
            }

        if utilizador.carteira < aumento:
            return {
                "sucesso": False,
                "mensagem": f"Saldo insuficiente. Carteira atual: {utilizador.carteira:.0f}€."
            }

        resultado = await crud.registar_lance(
            db=db,
            leilao_id=leilao_id,
            utilizador_id=utilizador.id,
            valor_lance=valor
        )

        if not resultado["sucesso"]:
            return resultado

        utilizador.carteira -= aumento

        await db.commit()
        await db.refresh(utilizador)

        anuncio = {
            "tipo": "lance",
            "sucesso": True,
            "leilao_id": leilao_id,
            "novo_preco": resultado["novo_preco"],
            "valor": resultado["novo_preco"],
            "utilizador_id": utilizador.id,
            "utilizador": utilizador.nome,
            "carteira": utilizador.carteira,
            "licitacao_id": resultado.get("licitacao_id"),
            "criado_em": resultado.get("criado_em").isoformat() if resultado.get("criado_em") else None,
            "mensagem": f"{utilizador.nome} cobriu a oferta com {resultado['novo_preco']}€"
        }

        await publicar_lance_no_redis(leilao_id, anuncio)

        return anuncio


@app.on_event("startup")
async def startup_event():
    global redis_client

    redis_client = aioredis.from_url(REDIS_URL, decode_responses=True)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await garantir_colunas_extra()

    async with AsyncSessionLocal() as db:
        await criar_leiloes_padrao(db)


@app.get("/", include_in_schema=False)
async def frontend():
    return FileResponse("app/index.html")


@app.get("/style.css", include_in_schema=False)
async def style_css():
    return FileResponse("app/style.css")


@app.get("/script.js", include_in_schema=False)
async def script_js():
    return FileResponse("app/script.js")


@app.get("/api/status")
async def read_root():
    return {
        "status": "API REST Ativa",
        "projeto": "Tema 5 - Leilões Online",
        "ambiente": "Dockerizado"
    }


@app.post("/demo/reset")
async def reset_demo():
    async with AsyncSessionLocal() as db:
        await limpar_demo(db)

    return {
        "sucesso": True,
        "mensagem": "Demo reiniciada. Lances apagados, carteiras repostas e leilões restaurados."
    }


@app.post("/bots/heartbeat")
async def bots_heartbeat():
    global ultimo_heartbeat_bots

    ultimo_heartbeat_bots = datetime.now(timezone.utc)

    return {
        "sucesso": True,
        "bots_ativos": True
    }


@app.get("/bots/status")
async def bots_status():
    return {
        "bots_ativos": bots_estao_ativos()
    }


@app.get("/utilizadores/existe")
async def utilizador_existe(nome: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(models.Utilizador).where(models.Utilizador.nome == nome)
    )
    db_user = result.scalars().first()

    return {"existe": db_user is not None}


@app.post("/entrar", response_model=schemas.UtilizadorResponse)
async def entrar_na_plataforma(
    utilizador: schemas.UtilizadorCreate,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(models.Utilizador).where(models.Utilizador.nome == utilizador.nome)
    )
    db_user = result.scalars().first()

    if db_user:
        if not db_user.password_hash:
            db_user.password_hash = criar_password_hash(utilizador.password)

        if getattr(db_user, "carteira", None) is None:
            db_user.carteira = 10000.0

        await db.commit()
        await db.refresh(db_user)

        if not verificar_password(utilizador.password, db_user.password_hash):
            raise HTTPException(status_code=401, detail="Palavra-passe incorreta.")

        return db_user

    novo_utilizador = models.Utilizador(
        nome=utilizador.nome,
        password_hash=criar_password_hash(utilizador.password),
        carteira=10000.0
    )

    db.add(novo_utilizador)
    await db.commit()
    await db.refresh(novo_utilizador)

    return novo_utilizador


@app.post("/leiloes", response_model=schemas.LeilaoResponse)
async def anunciar_item(
    leilao: schemas.LeilaoCreate,
    dono_id: int,
    db: AsyncSession = Depends(get_db)
):
    novo_leilao = models.Leilao(
        titulo=leilao.titulo,
        descricao=leilao.descricao,
        preco_inicial=leilao.preco_inicial,
        preco_atual=leilao.preco_inicial,
        dono_id=dono_id,
        categoria=leilao.categoria or "Geral",
        localizacao=leilao.localizacao or "Portugal",
        emoji=leilao.emoji or "📦"
    )

    db.add(novo_leilao)
    await db.commit()
    await db.refresh(novo_leilao)

    return novo_leilao


@app.get("/leiloes", response_model=list[schemas.LeilaoResponse])
async def listar_montra(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(models.Leilao).order_by(models.Leilao.id)
    )
    lista_de_leiloes = result.scalars().all()
    return lista_de_leiloes


@app.get("/leiloes/{leilao_id}/historico")
async def historico_leilao(leilao_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(models.Licitacao, models.Utilizador)
        .join(models.Utilizador, models.Licitacao.utilizador_id == models.Utilizador.id)
        .where(models.Licitacao.leilao_id == leilao_id)
        .order_by(models.Licitacao.criado_em.asc(), models.Licitacao.id.asc())
    )

    historico = []

    for licitacao, utilizador in result.all():
        historico.append({
            "id": licitacao.id,
            "valor": licitacao.valor,
            "criado_em": licitacao.criado_em,
            "utilizador_id": utilizador.id,
            "utilizador_nome": utilizador.nome
        })

    return historico


@app.post("/leiloes/{leilao_id}/licitar")
async def licitar(leilao_id: int, lance: schemas.LanceCreate):
    resultado = await processar_lance(
        leilao_id=leilao_id,
        valor=lance.valor,
        utilizador_id=lance.utilizador_id,
        nome=lance.nome
    )

    if not resultado.get("sucesso"):
        raise HTTPException(status_code=400, detail=resultado.get("mensagem", "Erro ao registar lance."))

    return resultado


@app.delete("/leiloes/{leilao_id}")
async def remover_leilao(
    leilao_id: int,
    dono_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(models.Leilao).where(models.Leilao.id == leilao_id)
    )
    leilao = result.scalars().first()

    if not leilao:
        raise HTTPException(status_code=404, detail="Leilão não encontrado.")

    if leilao.dono_id != dono_id:
        raise HTTPException(status_code=403, detail="Só o utilizador que criou o leilão o pode remover.")

    await db.execute(
        delete(models.Licitacao).where(models.Licitacao.leilao_id == leilao_id)
    )
    await db.delete(leilao)
    await db.commit()

    return {"sucesso": True, "mensagem": "Leilão removido com sucesso."}


@app.websocket("/ws/leilao/{leilao_id}")
async def websocket_endpoint(websocket: WebSocket, leilao_id: int):
    await websocket.accept()

    pubsub = redis_client.pubsub()
    await pubsub.subscribe(f"leilao:{leilao_id}")

    async def redis_listener():
        try:
            while True:
                message = await pubsub.get_message(ignore_subscribe_messages=True)

                if message and message["type"] == "message":
                    await websocket.send_text(message["data"])

                await asyncio.sleep(0.1)
        except Exception:
            pass

    listener_task = asyncio.create_task(redis_listener())

    try:
        while True:
            data = await websocket.receive_text()
            texto = data.strip()

            if texto.startswith("ENTROU: "):
                nome = texto.replace("ENTROU: ", "").strip()

                await redis_client.publish(
                    f"leilao:{leilao_id}",
                    json.dumps({
                        "tipo": "entrou",
                        "nome": nome
                    })
                )

                continue

            if texto.startswith("SAIU: "):
                nome = texto.replace("SAIU: ", "").strip()

                await redis_client.publish(
                    f"leilao:{leilao_id}",
                    json.dumps({
                        "tipo": "saiu",
                        "nome": nome
                    })
                )

                continue

            try:
                mensagem_lance = json.loads(texto)

                if isinstance(mensagem_lance, dict) and "valor" in mensagem_lance:
                    resultado = await processar_lance(
                        leilao_id=leilao_id,
                        valor=float(mensagem_lance.get("valor")),
                        utilizador_id=mensagem_lance.get("utilizador_id"),
                        nome=mensagem_lance.get("nome")
                    )

                    if not resultado.get("sucesso"):
                        await websocket.send_text(json.dumps(resultado))

                    continue

            except Exception as erro:
                await websocket.send_text(json.dumps({
                    "sucesso": False,
                    "mensagem": f"Erro ao processar mensagem: {erro}"
                }))

                continue

            await redis_client.publish(
                f"leilao:{leilao_id}",
                json.dumps({
                    "tipo": "mensagem",
                    "texto": texto
                })
            )

    except WebSocketDisconnect:
        listener_task.cancel()
        await pubsub.unsubscribe(f"leilao:{leilao_id}")

        try:
            await pubsub.aclose()
        except Exception:
            pass