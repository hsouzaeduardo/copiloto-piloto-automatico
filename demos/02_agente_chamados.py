"""Demo 2 — Agente: chamados de TI.

Um ticket de VPN. O agente consulta o usuário, busca na base de conhecimento,
registra o diagnóstico e corrige — mas `resetar_senha` e `resetar_mfa` são
ações sensíveis marcadas com approval_mode="always_require": o framework PARA
e espera um humano (terminal ou cockpit).

    python demos/02_agente_chamados.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agent_framework import Agent, Message, tool

from comum import humano, log
from comum.config import cliente_maf
from mundo import dados, ferramentas

INSTRUCOES = """Você é um agente de suporte de TI de primeiro nível.
Para cada ticket: consulte o usuário, busque a base de conhecimento, registre o diagnóstico
no ticket, aplique a correção indicada e responda o usuário com `responder_usuario`.
Só execute ações sensíveis quando a base de conhecimento indicar. Responda em português."""

TOOLS = [
    tool(ferramentas.consultar_usuario),
    tool(ferramentas.buscar_base_conhecimento),
    tool(ferramentas.registrar_no_ticket),
    tool(ferramentas.responder_usuario),
    # Human-in-the-loop: o framework PARA antes de executar e devolve o controle.
    tool(ferramentas.resetar_senha, approval_mode="always_require"),
    tool(ferramentas.resetar_mfa, approval_mode="always_require"),
]


async def atender(agent: Agent, ticket: dict) -> None:
    log.cliente(f"[{ticket['id']} · {ticket['usuario_id']}] {ticket['mensagem']}", caso=ticket["id"])
    session = agent.create_session()
    resposta = await agent.run(
        f"Ticket {ticket['id']} do usuário {ticket['usuario_id']}: {ticket['mensagem']}", session=session
    )

    # Enquanto o agente pedir aprovações, um humano decide e o agente continua.
    while resposta.user_input_requests:
        decisoes = [
            Message(role="user", contents=[
                req.to_function_approval_response(humano.aprovar(req.function_call.name, req.function_call.arguments, ticket["id"]))
            ])
            for req in resposta.user_input_requests
            if req.function_call is not None
        ]
        resposta = await agent.run(decisoes, session=session)

    log.modelo(resposta.text, caso=ticket["id"])
    dados.marcar("tickets", ticket["id"], "resolvido")


async def main() -> None:
    dados.resetar()
    log.iniciar_demo("DEMO 2 — AGENTE", "agente", "Chamados de TI · Agent Framework + ferramentas + aprovação humana")

    agent = Agent(client=cliente_maf(), name="SuporteTI", instructions=INSTRUCOES, tools=TOOLS)
    for ticket in dados.pendentes("tickets"):
        await atender(agent, ticket)

    log.secao("O que observar")
    print("  • O log 🔧 mostra as ferramentas na ordem em que o MODELO escolheu chamar.")
    print("  • No reset de senha, o framework parou e esperou o 'sim'. É propriedade da ferramenta, não um input() no meio do código.")
    print("  • O agente resolveu a tarefa e devolveu o controle. Ele não decide SE deve agir: nós o chamamos.")


if __name__ == "__main__":
    asyncio.run(main())
