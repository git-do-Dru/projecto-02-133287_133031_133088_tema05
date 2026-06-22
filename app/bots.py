import asyncio
import json
import random
import time
import urllib.request

import websockets


NOMES_BOTS = [
    "Elias",
    "Maria",
    "T800",
    "Geraldo",
    "Ana",
    "Carlos",
    "Zeca",
    "Joana",
    "Rui",
    "Marta",
    "Nuno",
    "Sofia",
    "Duarte",
    "Ines",
    "Miguel",
    "Beatriz",
    "Tiago",
    "Rita",
    "Leonor",
    "Francisco",
    "Carolina",
    "Pedro",
    "Matilde",
    "Tomás",
    "Diana",
    "Henrique",
    "Madalena",
    "Simão"
]

API_BASE = "http://localhost:8000"
WS_BASE = "ws://localhost:8000"

PROBABILIDADE_ALL_IN = 0.12
MULTIPLICADOR_ORCAMENTO = 1.45
TEMPO_MINIMO_NA_SALA = 90
TEMPO_MAXIMO_NA_SALA = 210
INTERVALO_ENTRE_LANCES_MIN = 8
INTERVALO_ENTRE_LANCES_MAX = 20
INTERVALO_NOVA_VAGA_BOTS = 18
BOTS_MIN_POR_LEILAO = 1
BOTS_MAX_POR_LEILAO = 3
TEMPO_OBSERVAR_SE_MUITO_CARO_MIN = 25
TEMPO_OBSERVAR_SE_MUITO_CARO_MAX = 70

estado = {}
contador_bots = 0


def pedido_json(url, metodo="GET", dados=None, timeout=5):
    try:
        body = None
        headers = {}

        if dados is not None:
            body = json.dumps(dados).encode("utf-8")
            headers["Content-Type"] = "application/json"

        req = urllib.request.Request(url, data=body, headers=headers, method=metodo)

        with urllib.request.urlopen(req, timeout=timeout) as resposta:
            conteudo = resposta.read().decode("utf-8")
            return json.loads(conteudo) if conteudo else None
    except Exception as erro:
        print(f"⚠️ Erro no pedido {metodo} {url}: {erro}")
        return None


def enviar_heartbeat():
    pedido_json(f"{API_BASE}/bots/heartbeat", metodo="POST", dados={})


def carregar_leiloes():
    leiloes = pedido_json(f"{API_BASE}/leiloes")

    if leiloes:
        return leiloes

    print("⚠️ Não consegui carregar os leilões pela API. Vou tentar novamente em breve.")
    return []


def calcular_orcamento(leilao):
    titulo = str(leilao.get("titulo", "")).lower()
    categoria = str(leilao.get("categoria", "")).lower()
    preco_atual = float(leilao.get("preco_atual") or leilao.get("preco_inicial") or 100)

    if "rolex" in titulo or "luxo" in categoria:
        return min(10000, random.randint(7000, 10000))

    if "playstation" in titulo or "gaming" in categoria:
        return random.randint(650, 1800)

    if "bicicleta" in titulo or "desporto" in categoria:
        return random.randint(350, 1800)

    if "macbook" in titulo or "portátil" in titulo or "tecnologia" in categoria:
        return random.randint(1700, 5200)

    if "bmw" in titulo or "carro" in titulo or "automóveis" in categoria:
        return min(10000, random.randint(9000, 10000))

    if "samsung" in titulo or "televisão" in titulo or "imagem" in categoria:
        return random.randint(850, 2600)

    if "fender" in titulo or "guitarra" in titulo or "música" in categoria:
        return random.randint(1000, 3200)

    return min(10000, int(preco_atual * random.uniform(1.8, 3.2)))


def preparar_estado(leiloes):
    for leilao in leiloes:
        leilao_id = str(leilao["id"])
        preco_atual = float(leilao.get("preco_atual") or leilao.get("preco_inicial") or 0)

        if leilao_id not in estado:
            estado[leilao_id] = {
                "lance_mais_alto": preco_atual,
                "rodada": 0,
                "tempo_ultimo_lance": time.time()
            }
        else:
            estado[leilao_id]["lance_mais_alto"] = max(estado[leilao_id]["lance_mais_alto"], preco_atual)


async def heartbeat_loop():
    while True:
        enviar_heartbeat()
        await asyncio.sleep(2)


async def escutar_servidor(leilao_id):
    uri = f"{WS_BASE}/ws/leilao/{leilao_id}"

    while True:
        try:
            async with websockets.connect(uri, ping_interval=None) as ws:
                while True:
                    mensagem = await ws.recv()

                    try:
                        dados = json.loads(mensagem)

                        if dados.get("tipo") == "lance":
                            valor = float(dados.get("novo_preco") or dados.get("valor"))

                            if valor > estado[leilao_id]["lance_mais_alto"]:
                                estado[leilao_id]["lance_mais_alto"] = valor
                                estado[leilao_id]["rodada"] += 1
                                estado[leilao_id]["tempo_ultimo_lance"] = time.time()

                        continue
                    except Exception:
                        pass
        except Exception:
            await asyncio.sleep(3)


async def bot_licitador(nome_bot, leilao, carteira_maxima):
    leilao_id = str(leilao["id"])
    uri = f"{WS_BASE}/ws/leilao/{leilao_id}"
    inicio = time.time()
    tempo_na_sala = random.randint(TEMPO_MINIMO_NA_SALA, TEMPO_MAXIMO_NA_SALA)

    await asyncio.sleep(random.uniform(3, 12))

    try:
        async with websockets.connect(uri, ping_interval=None) as websocket:
            await websocket.send(f"ENTROU: {nome_bot}")
            print(f"🟢 {nome_bot} entrou na Sala {leilao_id}! Orçamento máximo: {carteira_maxima}€")

            while True:
                await asyncio.sleep(random.uniform(INTERVALO_ENTRE_LANCES_MIN, INTERVALO_ENTRE_LANCES_MAX))

                valor_atual = float(estado[leilao_id]["lance_mais_alto"])
                tempo_passado = time.time() - inicio

                if tempo_passado > tempo_na_sala:
                    await websocket.send(f"SAIU: {nome_bot}")
                    print(f"🚪 {nome_bot} saiu da Sala {leilao_id} depois de ficar ativo durante bastante tempo.")
                    break

                if valor_atual >= carteira_maxima:
                    tempo_a_observar = random.randint(TEMPO_OBSERVAR_SE_MUITO_CARO_MIN, TEMPO_OBSERVAR_SE_MUITO_CARO_MAX)
                    print(f"👀 {nome_bot} ficou a observar a Sala {leilao_id} durante {tempo_a_observar}s porque ficou muito caro.")
                    await asyncio.sleep(tempo_a_observar)
                    await websocket.send(f"SAIU: {nome_bot}")
                    print(f"🛑 {nome_bot} saiu da Sala {leilao_id}. Muito caro!")
                    break

                if random.random() < PROBABILIDADE_ALL_IN:
                    margem = random.randint(0, 60)
                    meu_novo_lance = carteira_maxima - margem
                else:
                    aumento = random.randint(10, 95)
                    meu_novo_lance = valor_atual + aumento

                if meu_novo_lance <= valor_atual:
                    meu_novo_lance = valor_atual + 10

                if meu_novo_lance > carteira_maxima:
                    meu_novo_lance = carteira_maxima

                mensagem = {
                    "tipo": "lance",
                    "nome": nome_bot,
                    "valor": round(float(meu_novo_lance), 2)
                }

                await websocket.send(json.dumps(mensagem))

                print(f"💸 [{nome_bot}] ofereceu {meu_novo_lance}€ na Sala {leilao_id}")

                estado[leilao_id]["lance_mais_alto"] = float(meu_novo_lance)
                estado[leilao_id]["tempo_ultimo_lance"] = time.time()

                if meu_novo_lance >= carteira_maxima and random.random() < 0.25:
                    tempo_a_observar = random.randint(20, 60)
                    print(f"🏁 {nome_bot} fez all-in, mas ainda fica a observar a Sala {leilao_id} durante {tempo_a_observar}s.")
                    await asyncio.sleep(tempo_a_observar)
                    await websocket.send(f"SAIU: {nome_bot}")
                    print(f"🏁 {nome_bot} saiu da Sala {leilao_id} após all-in.")
                    break

    except Exception as erro:
        print(f"Erro no bot {nome_bot}: {erro}")


def gerar_nome_bot(base):
    global contador_bots
    contador_bots += 1
    return f"{base}_{contador_bots}"


async def vaga_de_bots():
    leiloes = carregar_leiloes()

    if not leiloes:
        return

    preparar_estado(leiloes)

    nomes_disponiveis = NOMES_BOTS.copy()
    random.shuffle(nomes_disponiveis)

    for leilao in leiloes:
        quantidade = random.randint(BOTS_MIN_POR_LEILAO, BOTS_MAX_POR_LEILAO)

        for _ in range(quantidade):
            if not nomes_disponiveis:
                nomes_disponiveis = NOMES_BOTS.copy()
                random.shuffle(nomes_disponiveis)

            nome_base = nomes_disponiveis.pop()
            nome = gerar_nome_bot(nome_base)

            orcamento_base = calcular_orcamento(leilao)
            orcamento = int(orcamento_base * random.uniform(1.0, MULTIPLICADOR_ORCAMENTO))
            orcamento = min(10000, max(50, orcamento))

            asyncio.create_task(bot_licitador(nome, leilao, orcamento))


async def iniciar_bots():
    print("🤖 Bots ativos continuamente.")
    print("💡 Agora há mais bots, eles entram em todos os leilões e ficam mais tempo nas salas.")
    print("💡 Mantém este terminal aberto enquanto quiseres que os leilões estejam operacionais.")

    asyncio.create_task(heartbeat_loop())

    leiloes = carregar_leiloes()
    preparar_estado(leiloes)

    for leilao in leiloes:
        asyncio.create_task(escutar_servidor(str(leilao["id"])))

    while True:
        await vaga_de_bots()
        await asyncio.sleep(INTERVALO_NOVA_VAGA_BOTS)


if __name__ == "__main__":
    try:
        asyncio.run(iniciar_bots())
    except KeyboardInterrupt:
        print("\n🛑 Bots desligados.")