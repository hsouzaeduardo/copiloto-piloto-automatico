"""Demo 3 — Agente autônomo: roda a fila, resolve e escala.

O agente de dentro é o MESMO da Demo 2. A autonomia está no laço externo:
- gatilho próprio: ele varre a fila, ninguém o chama;
- memória persistente por caso (sessão salva em disco);
- alçada checada no código da ferramenta, não no prompt;
- orçamento de chamadas por caso;
- trilha de auditoria em auditoria.jsonl;
- kill switch: crie um arquivo `stop.flag` na raiz e o loop encerra.

    python demos/03_autonomo.py
    # em outro terminal, para parar:  touch stop.flag
"""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agent_framework import Agent, AgentSession, FunctionInvocationConfiguration, tool

from comum import log
from comum.config import cliente_maf
from mundo import dados, ferramentas
from mundo.ferramentas import FAQ

RAIZ = Path(__file__).parent.parent
STOP_FLAG = RAIZ / "stop.flag"
MEMORIA = RAIZ / "memoria"

ALCADA_REEMBOLSO = 200.00       # R$ — acima disso a FERRAMENTA recusa
MAX_CHAMADAS_POR_CASO = 8       # orçamento: evita loop infinito e fatura surpresa
INTERVALO_SEGUNDOS = 5          # "gatilho": frequência com que a fila é verificada

INSTRUCOES = f"""Você é um agente autônomo de atendimento. Ninguém revisa suas respostas antes do envio.
Para cada caso: consulte o pedido, aplique a política, abra chamado se houver problema,
responda o cliente com `responder_cliente`.
Você pode reembolsar até R$ {ALCADA_REEMBOLSO:.2f} por conta própria. Se a ferramenta recusar um
reembolso ou se o caso for ambíguo (não coberto claramente pela política), use `escalar_para_humano`
e informe ao cliente que um atendente dará continuidade. Nunca invente políticas. Responda em português.

{FAQ}"""

TOOLS = [
    tool(ferramentas.consultar_pedido),
    tool(ferramentas.consultar_estoque),
    tool(ferramentas.abrir_chamado),
    tool(ferramentas.responder_cliente),
    tool(ferramentas.fabricar_reembolso_com_alcada(ALCADA_REEMBOLSO)),   # guardrail no código
    tool(ferramentas.escalar_para_humano),                               # substitui a aprovação
]


def kill_switch() -> bool:
    return STOP_FLAG.exists()


def memoria_carregar(agent: Agent, caso_id: str) -> AgentSession:
    arquivo = MEMORIA / f"{caso_id}.json"
    if arquivo.exists():
        return AgentSession.from_dict(json.loads(arquivo.read_text(encoding="utf-8")))
    return agent.create_session(session_id=caso_id)


def memoria_salvar(session: AgentSession, caso_id: str) -> None:
    MEMORIA.mkdir(exist_ok=True)
    (MEMORIA / f"{caso_id}.json").write_text(json.dumps(session.to_dict(), ensure_ascii=False), encoding="utf-8")


async def processar(agent: Agent, caso: dict) -> None:
    log.cliente(f"[{caso['id']} · pedido {caso['pedido_id']}] {caso['mensagem']}")
    session = memoria_carregar(agent, caso["id"])
    escalacoes_antes = len(dados.carregar()["escalacoes"])

    resposta = await agent.run(f"Pedido {caso['pedido_id']}. Cliente diz: {caso['mensagem']}", session=session)

    memoria_salvar(session, caso["id"])
    escalado = len(dados.carregar()["escalacoes"]) > escalacoes_antes
    dados.marcar_caso(caso["id"], "escalado" if escalado else "resolvido")
    log.modelo(resposta.text)
    log.auditar({"caso": caso["id"], "pedido": caso["pedido_id"], "desfecho": "escalado" if escalado else "resolvido",
                 "resposta": resposta.text})


async def main() -> None:
    dados.resetar()
    STOP_FLAG.unlink(missing_ok=True)
    log.titulo(f"DEMO 3 — AGENTE AUTÔNOMO  (alçada R$ {ALCADA_REEMBOLSO:.0f} · orçamento {MAX_CHAMADAS_POR_CASO} chamadas · stop.flag para parar)")

    cliente = cliente_maf(
        function_invocation_configuration=FunctionInvocationConfiguration(max_function_calls=MAX_CHAMADAS_POR_CASO),
    )
    agent = Agent(client=cliente, name="AtendimentoAutonomo", instructions=INSTRUCOES, tools=TOOLS)

    while not kill_switch():
        pendentes = dados.fila_pendente()
        if not pendentes:
            print(f"\n{log.CINZA}fila vazia · aguardando {INTERVALO_SEGUNDOS}s (touch stop.flag para encerrar){log.RESET}")
            await asyncio.sleep(INTERVALO_SEGUNDOS)
            continue
        for caso in pendentes:
            if kill_switch():
                break
            await processar(agent, caso)

    log.aviso("stop.flag detectado — loop encerrado.")
    mundo = dados.carregar()
    log.secao("Resumo")
    print(f"  • Resolvidos: {sum(c['status'] == 'resolvido' for c in mundo['fila'])}   "
          f"Escalados: {len(mundo['escalacoes'])}   Reembolsos: {sum(p['reembolsado'] for p in mundo['pedidos'].values())}")
    print(f"  • Auditoria: {log.AUDITORIA.name}   Memória: memoria/*.json")
    log.secao("O que observar")
    print("  • Ninguém chamou o agente: o gatilho é a fila.")
    print("  • O reembolso de R$ 450 foi RECUSADO pela ferramenta — o guardrail está no código, não no prompt.")
    print("  • Casos ambíguos foram escalados, não inventados. Human-ON-the-loop: você lê o log, não aprova cada passo.")


if __name__ == "__main__":
    asyncio.run(main())
