import asyncio
import websockets
import random
import re
import time

NOMES_LEGAIS = ["Elias", "Maria", "T800", "Geraldo", "Ana", "Carlos", "Zeca", "Joana"]

# Agora o cérebro tem uma "gaveta" para cada sala de leilão!
estado = {
    "1": {"lance_mais_alto": 5500.0, "rodada": 0, "tempo_ultimo_lance": time.time()},
    "2": {"lance_mais_alto": 400.0, "rodada": 0, "tempo_ultimo_lance": time.time()},
    "3": {"lance_mais_alto": 100.0, "rodada": 0, "tempo_ultimo_lance": time.time()}
}

async def escutar_servidor(leilao_id):
    """Fica a escutar as atualizações de uma sala específica"""
    uri = f"ws://localhost:8000/ws/leilao/{leilao_id}"
    try:
        async with websockets.connect(uri, ping_interval=None) as ws:
            while True:
                mensagem = await ws.recv()
                match = re.search(r'(\d+(?:\.\d+)?)€', mensagem)
                
                if match:
                    valor_recebido = float(match.group(1))
                    if valor_recebido > estado[leilao_id]["lance_mais_alto"]:
                        estado[leilao_id]["lance_mais_alto"] = valor_recebido
                        estado[leilao_id]["rodada"] += 1
                        estado[leilao_id]["tempo_ultimo_lance"] = time.time()
                        
    except websockets.exceptions.ConnectionClosed:
        pass

async def bot_licitador(nome_bot, leilao_id, carteira_maxima):
    uri = f"ws://localhost:8000/ws/leilao/{leilao_id}"
    await asyncio.sleep(random.uniform(1, 4))
    
    try:
        async with websockets.connect(uri, ping_interval=None) as websocket:
            await websocket.send(f"ENTROU: {nome_bot}")
            print(f"🟢 {nome_bot} entrou na Sala {leilao_id}! (Orçamento: {carteira_maxima}€)")
            
            while True:
                atraso = random.randint(3, 8) + (estado[leilao_id]["rodada"] * 0.2)
                await asyncio.sleep(atraso)
                
                tempo_passado = time.time() - estado[leilao_id]["tempo_ultimo_lance"]
                if tempo_passado < 3.0:
                    continue
                
                valor_atual = estado[leilao_id]["lance_mais_alto"]
                
                if valor_atual >= carteira_maxima:
                    await websocket.send(f"SAIU: {nome_bot}")
                    print(f"🛑 {nome_bot} saiu da Sala {leilao_id}. Muito caro!")
                    break
                
                meu_novo_lance = valor_atual + random.randint(10, 100)
                if meu_novo_lance > carteira_maxima:
                    meu_novo_lance = carteira_maxima
                
                mensagem = f"{nome_bot} cobriu a oferta com {meu_novo_lance}€"
                await websocket.send(mensagem)
                print(f"💸 [{nome_bot}] ofereceu {meu_novo_lance}€ na Sala {leilao_id}")
                
    except Exception as e:
        print(f"Erro no bot {nome_bot}: {e}")

async def iniciar_invasao():
    print("🤖 A iniciar bots espalhados por todos os leilões...")
    
    # Inicia 3 "ouvidos" (um para cada sala)
    for i in ["1", "2", "3"]:
        asyncio.create_task(escutar_servidor(i))
    
    tarefas_bots = []
    
    # Envia todos os bots da lista para salas aleatórias
    for nome in NOMES_LEGAIS:
        leilao_id = str(random.choice([1, 2, 3]))
        
        # Ajusta o dinheiro da carteira com base no item que eles querem comprar
        if leilao_id == "1": orcamento = random.randint(6000, 7500)   # Rolex
        elif leilao_id == "2": orcamento = random.randint(450, 700)   # PS5
        else: orcamento = random.randint(150, 300)                    # Bicicleta
            
        tarefas_bots.append(bot_licitador(nome, leilao_id, orcamento))
        
    await asyncio.gather(*tarefas_bots)

if __name__ == "__main__":
    try:
        asyncio.run(iniciar_invasao())
    except KeyboardInterrupt:
        print("\n🛑 Bots desligados.")