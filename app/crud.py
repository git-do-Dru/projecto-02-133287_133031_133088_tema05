from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from . import models


async def registar_lance(db: AsyncSession, leilao_id: int, utilizador_id: int, valor_lance: float):
    result_leilao = await db.execute(
        select(models.Leilao).where(models.Leilao.id == leilao_id)
    )
    leilao = result_leilao.scalars().first()

    if not leilao:
        return {
            "sucesso": False,
            "mensagem": "Leilão não encontrado."
        }

    result_user = await db.execute(
        select(models.Utilizador).where(models.Utilizador.id == utilizador_id)
    )
    utilizador = result_user.scalars().first()

    if not utilizador:
        return {
            "sucesso": False,
            "mensagem": "Utilizador não encontrado."
        }

    if valor_lance <= leilao.preco_atual:
        return {
            "sucesso": False,
            "mensagem": f"Lance inválido. O valor tem de ser maior que {leilao.preco_atual}€."
        }

    aumento = valor_lance - leilao.preco_atual

    if utilizador.carteira is None:
        utilizador.carteira = 10000.0

    if aumento > utilizador.carteira:
        return {
            "sucesso": False,
            "mensagem": f"Saldo insuficiente. Tens {utilizador.carteira:.0f}€ na carteira e precisas de {aumento:.0f}€ para este aumento."
        }

    utilizador.carteira -= aumento
    leilao.preco_atual = valor_lance

    nova_licitacao = models.Licitacao(
        valor=valor_lance,
        leilao_id=leilao_id,
        utilizador_id=utilizador_id
    )

    db.add(nova_licitacao)

    await db.commit()
    await db.refresh(leilao)
    await db.refresh(utilizador)
    await db.refresh(nova_licitacao)

    return {
        "sucesso": True,
        "novo_preco": leilao.preco_atual,
        "carteira": utilizador.carteira,
        "aumento": aumento,
        "licitacao_id": nova_licitacao.id,
        "criado_em": nova_licitacao.criado_em
    }
