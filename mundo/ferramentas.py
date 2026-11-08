"""Ferramentas do mundo simulado, agrupadas por cenário.

São funções Python comuns. O que muda entre as demos não é a ferramenta,
é quem a chama e com que permissão:

- Demo 1 (assistente, e-mail): nenhuma ferramenta é exposta ao modelo.
- Demo 2 (agente, chamados de TI): leitura livre; `resetar_senha` e `resetar_mfa`
  exigem aprovação humana (approval_mode="always_require").
- Demo 3 (autônomo, atendimento comercial): `reembolsar` tem alçada checada no
  código e `escalar_para_humano` substitui a aprovação.
"""

from __future__ import annotations

from typing import Annotated

from comum.log import log_ferramenta
from mundo import dados

# ======================================================================
# Cenário 2 — Chamados de TI
# ======================================================================

def consultar_usuario(usuario_id: Annotated[str, "Identificador do usuário, ex.: U-204"]) -> str:
    """Consulta o cadastro do usuário: setor, MFA, senha expirada, último login."""
    usuario = dados.carregar()["usuarios"].get(usuario_id)
    resultado = f"Usuário {usuario_id}: {usuario}" if usuario else f"Usuário {usuario_id} não encontrado."
    log_ferramenta("consultar_usuario", {"usuario_id": usuario_id}, resultado)
    return resultado


def buscar_base_conhecimento(termo: Annotated[str, "Palavras-chave do problema, ex.: VPN credenciais"]) -> str:
    """Busca artigos na base de conhecimento de TI."""
    termos = termo.lower().split()
    artigos = [a for a in dados.carregar()["base_conhecimento"] if any(t in (a["titulo"] + a["solucao"]).lower() for t in termos)]
    resultado = "\n".join(f"{a['id']} — {a['titulo']}: {a['solucao']}" for a in artigos) or "Nenhum artigo encontrado."
    log_ferramenta("buscar_base_conhecimento", {"termo": termo}, resultado)
    return resultado


def registrar_no_ticket(
    ticket_id: Annotated[str, "Número do ticket, ex.: TI-1101"],
    diagnostico: Annotated[str, "Diagnóstico em uma frase"],
) -> str:
    """Registra o diagnóstico no ticket."""
    mundo = dados.carregar()
    for t in mundo["tickets"]:
        if t["id"] == ticket_id:
            t["diagnostico"] = diagnostico
    dados.salvar(mundo)
    resultado = f"Diagnóstico registrado no ticket {ticket_id}."
    log_ferramenta("registrar_no_ticket", {"ticket_id": ticket_id, "diagnostico": diagnostico}, resultado)
    return resultado


def resetar_senha(usuario_id: Annotated[str, "Identificador do usuário"]) -> str:
    """Redefine a senha de rede do usuário e envia uma senha temporária. Ação sensível."""
    mundo = dados.carregar()
    usuario = mundo["usuarios"].get(usuario_id)
    if not usuario:
        resultado = f"Usuário {usuario_id} não encontrado."
    else:
        usuario["senha_expirada"] = False
        dados.salvar(mundo)
        resultado = f"Senha de {usuario['nome']} redefinida; senha temporária enviada para {usuario['email']}."
    log_ferramenta("resetar_senha", {"usuario_id": usuario_id}, resultado)
    return resultado


def resetar_mfa(usuario_id: Annotated[str, "Identificador do usuário"]) -> str:
    """Remove o dispositivo MFA do usuário para novo cadastro. Ação sensível."""
    mundo = dados.carregar()
    usuario = mundo["usuarios"].get(usuario_id)
    if not usuario:
        resultado = f"Usuário {usuario_id} não encontrado."
    else:
        usuario["mfa_ativo"] = False
        dados.salvar(mundo)
        resultado = f"MFA de {usuario['nome']} resetado; novo cadastro liberado."
    log_ferramenta("resetar_mfa", {"usuario_id": usuario_id}, resultado)
    return resultado


def responder_usuario(
    ticket_id: Annotated[str, "Número do ticket"],
    mensagem: Annotated[str, "Resposta ao usuário, em português, objetiva e com os próximos passos"],
) -> str:
    """Envia a resposta ao usuário que abriu o ticket."""
    mundo = dados.carregar()
    mundo["mensagens_enviadas"].append({"ticket_id": ticket_id, "mensagem": mensagem})
    dados.salvar(mundo)
    resultado = f"Resposta enviada ao usuário do ticket {ticket_id}."
    log_ferramenta("responder_usuario", {"ticket_id": ticket_id, "mensagem": mensagem[:80] + "..."}, resultado)
    return resultado


# ======================================================================
# Cenário 3 — Atendimento comercial
# ======================================================================

POLITICA_COMERCIAL = """Política de atendimento da loja:
- Prazo de entrega padrão: 5 a 8 dias úteis após a confirmação do pagamento.
- Pedidos extraviados: após 5 dias além da previsão, o cliente tem direito a reembolso integral.
- Produtos com defeito ou avaria: devolução e reembolso em até 7 dias após a entrega.
- Trocas por arrependimento (produto correto, cliente mudou de ideia): aceitas em até 7 dias, sem reembolso, só troca.
- Alteração de data de entrega: possível enquanto o pedido estiver em trânsito.
"""


class ForaDaAlcada(Exception):
    """Levantada quando um reembolso ultrapassa o limite permitido ao agente."""


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


def fabricar_reembolso_com_alcada(alcada: float):
    """Devolve uma versão de `reembolsar` limitada a `alcada` reais (Demo 3)."""

    def reembolsar(
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

    return reembolsar


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
