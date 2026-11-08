"""Ferramentas compartilhadas pelas três demos.

São funções Python comuns. O que muda entre as demos não é a ferramenta,
é quem a chama e com que permissão:

- Demo 1 (assistente): nenhuma ferramenta é exposta ao modelo.
- Demo 2 (agente): todas expostas; `reembolsar` exige aprovação humana.
- Demo 3 (autônomo): todas expostas; `reembolsar` tem alçada no código
  e `escalar_para_humano` substitui a aprovação.
"""

from __future__ import annotations

from typing import Annotated

from comum.log import log_ferramenta
from mundo import dados

FAQ = """Política de atendimento da loja:
- Prazo de entrega padrão: 5 a 8 dias úteis após a confirmação do pagamento.
- Pedidos extraviados: após 5 dias além da previsão, o cliente tem direito a reembolso integral.
- Produtos com defeito ou avaria: devolução e reembolso em até 7 dias após a entrega.
- Trocas por arrependimento (produto correto, cliente mudou de ideia): aceitas em até 7 dias, sem reembolso, só troca.
- Alteração de data de entrega: possível enquanto o pedido estiver em trânsito.
"""


class ForaDaAlcada(Exception):
    """Levantada quando um reembolso ultrapassa o limite permitido ao agente."""


# ---------------------------------------------------------------- leitura

def consultar_pedido(pedido_id: Annotated[str, "Número do pedido, ex.: 1042"]) -> str:
    """Consulta o status, valor e previsão de entrega de um pedido."""
    pedido = dados.carregar()["pedidos"].get(pedido_id)
    resultado = f"Pedido {pedido_id}: {pedido}" if pedido else f"Pedido {pedido_id} não encontrado."
    log_ferramenta("consultar_pedido", {"pedido_id": pedido_id}, resultado)
    return resultado


def consultar_estoque(sku: Annotated[str, "Código do produto, ex.: FONE-X2"]) -> str:
    """Consulta a quantidade em estoque de um produto."""
    item = dados.carregar()["estoque"].get(sku)
    resultado = f"Estoque {sku}: {item}" if item else f"SKU {sku} não encontrado."
    log_ferramenta("consultar_estoque", {"sku": sku}, resultado)
    return resultado


# ----------------------------------------------------------------- escrita

def abrir_chamado(
    pedido_id: Annotated[str, "Número do pedido"],
    motivo: Annotated[str, "Resumo do problema em uma frase"],
) -> str:
    """Registra um chamado de atendimento vinculado ao pedido."""
    mundo = dados.carregar()
    chamado_id = f"CH-{len(mundo['chamados']) + 1:03d}"
    mundo["chamados"].append({"id": chamado_id, "pedido_id": pedido_id, "motivo": motivo})
    dados.salvar(mundo)
    resultado = f"Chamado {chamado_id} aberto para o pedido {pedido_id}."
    log_ferramenta("abrir_chamado", {"pedido_id": pedido_id, "motivo": motivo}, resultado)
    return resultado


def responder_cliente(
    pedido_id: Annotated[str, "Número do pedido"],
    mensagem: Annotated[str, "Texto da resposta ao cliente, em português, cordial e objetivo"],
) -> str:
    """Envia a resposta final ao cliente."""
    mundo = dados.carregar()
    mundo["mensagens_enviadas"].append({"pedido_id": pedido_id, "mensagem": mensagem})
    dados.salvar(mundo)
    resultado = f"Mensagem enviada ao cliente do pedido {pedido_id}."
    log_ferramenta("responder_cliente", {"pedido_id": pedido_id, "mensagem": mensagem[:80] + "..."}, resultado)
    return resultado


def _aplicar_reembolso(pedido_id: str, valor: float, alcada: float | None) -> str:
    """Núcleo do reembolso. A alçada é checada AQUI, em código — não no prompt."""
    if alcada is not None and valor > alcada:
        raise ForaDaAlcada(f"R$ {valor:.2f} excede a alçada de R$ {alcada:.2f}")
    mundo = dados.carregar()
    pedido = mundo["pedidos"].get(pedido_id)
    if not pedido:
        return f"Pedido {pedido_id} não encontrado."
    if pedido["reembolsado"]:
        return f"Pedido {pedido_id} já havia sido reembolsado."
    if valor > pedido["valor"]:
        return f"Valor R$ {valor:.2f} maior que o valor do pedido (R$ {pedido['valor']:.2f}). Reembolso negado."
    pedido["reembolsado"] = True
    pedido["status"] = "reembolsado"
    dados.salvar(mundo)
    return f"Reembolso de R$ {valor:.2f} aplicado ao pedido {pedido_id}."


def reembolsar(
    pedido_id: Annotated[str, "Número do pedido"],
    valor: Annotated[float, "Valor em reais a reembolsar"],
) -> str:
    """Reembolsa o cliente. Ação financeira irreversível."""
    resultado = _aplicar_reembolso(pedido_id, valor, alcada=None)
    log_ferramenta("reembolsar", {"pedido_id": pedido_id, "valor": valor}, resultado)
    return resultado


def fabricar_reembolso_com_alcada(alcada: float):
    """Devolve uma versão de `reembolsar` limitada a `alcada` reais (Demo 3)."""

    def reembolsar_com_alcada(
        pedido_id: Annotated[str, "Número do pedido"],
        valor: Annotated[float, "Valor em reais a reembolsar"],
    ) -> str:
        """Reembolsa o cliente dentro da alçada do agente. Acima da alçada, a ferramenta recusa."""
        try:
            resultado = _aplicar_reembolso(pedido_id, valor, alcada=alcada)
        except ForaDaAlcada as erro:
            resultado = f"RECUSADO pela ferramenta: {erro}. Use escalar_para_humano."
        log_ferramenta("reembolsar", {"pedido_id": pedido_id, "valor": valor, "alcada": alcada}, resultado)
        return resultado

    reembolsar_com_alcada.__name__ = "reembolsar"
    return reembolsar_com_alcada


def escalar_para_humano(
    pedido_id: Annotated[str, "Número do pedido"],
    motivo: Annotated[str, "Por que este caso precisa de um humano"],
) -> str:
    """Encaminha o caso para a fila de um atendente humano."""
    mundo = dados.carregar()
    mundo["escalacoes"].append({"pedido_id": pedido_id, "motivo": motivo})
    dados.salvar(mundo)
    resultado = f"Pedido {pedido_id} escalado para um humano."
    log_ferramenta("escalar_para_humano", {"pedido_id": pedido_id, "motivo": motivo}, resultado)
    return resultado
