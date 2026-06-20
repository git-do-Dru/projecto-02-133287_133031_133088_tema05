from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from . import models

async def registar_lance(db: AsyncSession, leilao_id: int, utilizador_id: int, valor_lance: float):
    
    # 1. Procurar o leilão na base de dados
    result = await db.execute(select(models.Leilao).where(models.Leilao.id == leilao_id))
    leilao = result.scalars().first()

    if not leilao:
        return {"sucesso": False, "mensagem": "Leilão não encontrado."}

    # 2. A Regra de Ouro: Validar se o lance é válido (maior que o preço atual)
    if valor_lance <= leilao.preco_atual:
        return {"sucesso": False, "mensagem": f"Lance inválido. O valor tem de ser maior que {leilao.preco_atual}€."}

    # 3. Atualizar o preço do leilão
    leilao.preco_atual = valor_lance

    # 4. Criar o registo (recibo) na tabela de licitações
    nova_licitacao = models.Licitacao(
        valor=valor_lance,
        leilao_id=leilao_id,
        utilizador_id=utilizador_id
    )
    db.add(nova_licitacao)

    # 5. Guardar TUDO no PostgreSQL
    await db.commit()
    await db.refresh(leilao)

    return {"sucesso": True, "novo_preco": leilao.preco_atual}