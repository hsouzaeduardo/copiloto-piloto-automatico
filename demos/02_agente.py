"""Demo 2 — Agente: consulta, age e pede aprovação.

Mesmo cenário da Demo 1, agora com o Microsoft Agent Framework:
- as funções do mundo viram ferramentas (`@tool`);
- `reembolsar` é marcada com approval_mode="always_require";
- o loop de execução é do framework; o humano entra só no reembolso.

    python demos/02_agente.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agent_framework import Agent, Message, tool

from comum import log
from comum.config import cliente_maf
from mundo import dados, ferramentas
from mundo.ferramentas import FAQ

INSTRUCOES = f"""Você é um agente de atendimento de uma loja online.
Para cada mensagem de cliente: consulte o pedido, decida conforme a política,
registre um chamado quando houver problema, e responda o cliente com
`responder_cliente`. Só reembolse quando a política permitir. Responda em português.

{FAQ}"""

TOOLS = [
    tool(ferramentas.consultar_pedido),
    tool(ferramentas.consultar_estoque),
    tool(ferramentas.abrir_chamado),
    tool(ferramentas.responder_cliente),
    # Human-in-the-loop: o framework PARA antes de executar e devolve o controle.
    tool(ferramentas.reembolsar, approval_mode="always_require"),
]


def pedir_aprovacao(chamada) -> bool:
    log.aviso(f"Aprovação necessária: {chamada.name}({chamada.arguments})")
    return input("   Aprovar? [s/N] ").strip().lower() == "s"


async def atender(agent: Agent, caso: dict) -> None:
    log.cliente(f"[pedido {caso['pedido_id']}] {caso['mensagem']}")
    session = agent.create_session()
    resposta = await agent.run(f"Pedido {caso['pedido_id']}. Cliente diz: {caso['mensagem']}", session=session)

    # Enquanto o agente pedir aprovações, respondemos e deixamos ele continuar.
    while resposta.user_input_requests:
        aprovacoes = [
            Message(role="user", contents=[req.to_function_approval_response(pedir_aprovacao(req.function_call))])
            for req in resposta.user_input_requests
            if req.function_call is not None
        ]
        resposta = await agent.run(aprovacoes, session=session)

    log.modelo(resposta.text)
    dados.marcar_caso(caso["id"], "resolvido")


async def main() -> None:
    dados.resetar()
    log.titulo("DEMO 2 — AGENTE  (Agent Framework + ferramentas + aprovação)")

    agent = Agent(client=cliente_maf(), name="AtendimentoAgent", instructions=INSTRUCOES, tools=TOOLS)

    # Dois casos: um só precisa de informação; o outro pede reembolso.
    for caso in dados.fila_pendente()[:2]:
        await atender(agent, caso)

    log.secao("O que observar")
    print("  • O log 🔧 mostra as ferramentas na ordem em que o MODELO escolheu chamar.")
    print("  • No reembolso, o framework parou e esperou o 'sim'. Isso é propriedade da ferramenta, não um input() no meio do código.")
    print("  • O agente resolveu a tarefa e devolveu o controle. Ele não decide SE deve agir: nós o chamamos.")


if __name__ == "__main__":
    asyncio.run(main())
