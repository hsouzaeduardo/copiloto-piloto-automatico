"""Ensaio — roda qualquer demo SEM modelo, com as chamadas roteirizadas.

Serve para testar o cockpit, o enquadramento da tela e o ritmo da gravação
sem gastar token nem depender de rede. Usa as mesmas ferramentas, o mesmo log,
a mesma aprovação (cockpit ou terminal) e o mesmo kill switch das demos reais.
Só o "modelo" é fingido.

    python demos/ensaio.py 1      # e-mail
    python demos/ensaio.py 2      # chamados de TI (pede aprovação)
    python demos/ensaio.py 3      # comercial autônomo (encerra com kill switch)
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from comum import humano, log
from comum.ritmo import pausa
from mundo import dados, ferramentas as f


async def ensaio_1() -> None:
    dados.resetar()
    log.iniciar_demo("DEMO 1 — ASSISTENTE (ensaio)", "assistente", "Responder e-mail · sem ferramentas")
    rascunhos = {
        "E-001": "Olá, Fernanda! Obrigado pela mensagem. Vou verificar a segunda via da nota fiscal do pedido 7731 e te envio ainda hoje. Abraço, Henrique",
        "E-002": "Oi, Ricardo! Sem problema. Me diga qual horário de sexta de manhã fica melhor para você que eu confirmo. Se preferir, podemos deixar para a semana que vem. Abraço, Henrique",
    }
    for email in dados.carregar()["emails"]:
        log.cliente(f"[{email['id']}] {email['assunto']} — {email['corpo']}", caso=email["id"])
        await pausa(2.5)
        log.modelo(rascunhos[email["id"]], caso=email["id"])
        await pausa()


async def ensaio_2() -> None:
    dados.resetar()
    log.iniciar_demo("DEMO 2 — AGENTE (ensaio)", "agente", "Chamados de TI · ferramentas + aprovação humana")
    for t in dados.pendentes("tickets"):
        log.cliente(f"[{t['id']} · {t['usuario_id']}] {t['mensagem']}", caso=t["id"])
        await pausa(2)
        f.consultar_usuario(t["usuario_id"]); await pausa(1.5)
        f.buscar_base_conhecimento("VPN credenciais"); await pausa(1.5)
        f.registrar_no_ticket(t["id"], "Senha de rede expirada (KB-01)"); await pausa(1.5)
        if humano.aprovar("resetar_senha", {"usuario_id": t["usuario_id"]}, t["id"]):
            f.resetar_senha(t["usuario_id"]); await pausa(1)
            f.responder_usuario(t["id"], "Oi, Paula! Sua senha de rede tinha expirado. Redefini e enviei uma senha temporária para o seu e-mail. Troque no primeiro acesso e a VPN volta a funcionar.")
            log.modelo("Ticket TI-1101 resolvido: senha expirada, redefinida com aprovação. Usuária orientada por e-mail.", caso=t["id"])
        else:
            f.responder_usuario(t["id"], "Oi, Paula! Identifiquei que sua senha de rede expirou. Um analista vai redefini-la e te avisar em seguida.")
            log.modelo("Reset de senha NEGADO pelo humano. Ticket TI-1101 segue com o diagnóstico registrado para um analista.", caso=t["id"])
        dados.marcar("tickets", t["id"], "resolvido")
        await pausa()


ROTEIRO_3 = {
    "T-001": [("consultar_pedido", {"pedido_id": "1042"}),
              ("responder_cliente", {"pedido_id": "1042", "mensagem": "Oi, Ana! Seu fone está em trânsito com previsão de entrega para 12/11, dentro do prazo de 5 a 8 dias úteis. Qualquer novidade eu te aviso."})],
    "T-002": [("consultar_pedido", {"pedido_id": "1043"}),
              ("abrir_chamado", {"pedido_id": "1043", "motivo": "Pedido extraviado há 5 dias além da previsão"}),
              ("reembolsar", {"pedido_id": "1043", "valor": 450.0}),
              ("escalar_para_humano", {"pedido_id": "1043", "motivo": "Reembolso de R$ 450 acima da alçada de R$ 200"}),
              ("responder_cliente", {"pedido_id": "1043", "mensagem": "Oi, Bruno! Confirmei o extravio e você tem direito ao reembolso integral. Como o valor passa da minha alçada, um atendente vai concluir o reembolso e te avisar hoje."})],
    "T-003": [("consultar_pedido", {"pedido_id": "1044"}),
              ("abrir_chamado", {"pedido_id": "1044", "motivo": "Produto entregue com avaria"}),
              ("reembolsar", {"pedido_id": "1044", "valor": 95.0}),
              ("responder_cliente", {"pedido_id": "1044", "mensagem": "Oi, Carla! Sinto muito pela avaria. O reembolso de R$ 95,00 já foi aplicado e você verá o estorno em até 5 dias úteis."})],
    "T-004": [("consultar_pedido", {"pedido_id": "1046"}),
              ("escalar_para_humano", {"pedido_id": "1046", "motivo": "Troca por arrependimento com pedido de reembolso: não coberto claramente pela política"}),
              ("responder_cliente", {"pedido_id": "1046", "mensagem": "Oi, Elisa! Trocas por arrependimento são aceitas em até 7 dias. Para confirmar as opções no seu caso, encaminhei para um atendente, que te responde em breve."})],
    "T-005": [("consultar_pedido", {"pedido_id": "1045"}),
              ("responder_cliente", {"pedido_id": "1045", "mensagem": "Oi, Diego! Seu pedido ainda está em trânsito, então dá para alterar a data. Registrei a entrega para sexta-feira. Boa viagem!"})],
}
RESUMO_3 = {
    "T-001": "Dúvida de prazo respondida com os dados do pedido.",
    "T-002": "Extravio confirmado; reembolso de R$ 450 recusado pela ferramenta (alçada R$ 200) → escalado.",
    "T-003": "Avaria confirmada; reembolso de R$ 95 aplicado dentro da alçada.",
    "T-004": "Caso ambíguo (troca + reembolso) → escalado em vez de inventar.",
    "T-005": "Alteração de data de entrega registrada.",
}


async def ensaio_3() -> None:
    dados.resetar()
    humano.STOP_FLAG.unlink(missing_ok=True)
    log.iniciar_demo("DEMO 3 — AGENTE AUTÔNOMO (ensaio)", "autonomo", "Atendimento comercial · alçada R$ 200 · kill switch para parar")
    reembolsar = f.fabricar_reembolso_com_alcada(200.0)
    funcoes = {"consultar_pedido": f.consultar_pedido, "abrir_chamado": f.abrir_chamado, "responder_cliente": f.responder_cliente,
               "reembolsar": reembolsar, "escalar_para_humano": f.escalar_para_humano}

    while not humano.kill_switch():
        pendentes = dados.pendentes("fila")
        if not pendentes:
            log.sistema("fila vazia · aguardando 5s (KILL SWITCH no cockpit ou stop.flag para encerrar)")
            await asyncio.sleep(5)
            continue
        for caso in pendentes:
            if humano.kill_switch():
                break
            log.cliente(f"[{caso['id']} · pedido {caso['pedido_id']}] {caso['mensagem']}", caso=caso["id"])
            await pausa(2)
            escalado = False
            for nome, args in ROTEIRO_3[caso["id"]]:
                funcoes[nome](**args)
                escalado |= nome == "escalar_para_humano"
                await pausa(1.3)
            desfecho = "escalado" if escalado else "resolvido"
            dados.marcar("fila", caso["id"], desfecho)
            log.modelo(RESUMO_3[caso["id"]], caso=caso["id"])
            log.auditar({"caso": caso["id"], "pedido": caso["pedido_id"], "desfecho": desfecho, "resposta": RESUMO_3[caso["id"]]})
            await pausa()
    log.aviso("kill switch acionado — loop encerrado.")


if __name__ == "__main__":
    qual = sys.argv[1] if len(sys.argv) > 1 else "1"
    asyncio.run({"1": ensaio_1, "2": ensaio_2, "3": ensaio_3}[qual]())
