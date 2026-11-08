"""Demo 1 — Assistente: responder e-mail.

Uma chamada ao modelo por e-mail. Nenhuma ferramenta, nenhum estado,
nenhum loop. Ele escreve um rascunho — e é você quem envia.

    python demos/01_assistente_email.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from comum import log
from comum.config import MODEL, cliente_sdk
from mundo import dados

INSTRUCOES = (
    "Você é o assistente de e-mail de Henrique, executivo de IA. Escreva um rascunho de resposta "
    "em português, cordial e curto, pronto para ele revisar e enviar. Não invente dados que você não tem."
)


def rascunhar(client, email: dict) -> str:
    """Entrada → modelo → saída. Fim."""
    resp = client.responses.create(
        model=MODEL,
        instructions=INSTRUCOES,
        input=f"De: {email['de']}\nAssunto: {email['assunto']}\n\n{email['corpo']}",
    )
    return resp.output_text


def main() -> None:
    dados.resetar()
    client = cliente_sdk()
    log.iniciar_demo("DEMO 1 — ASSISTENTE", "assistente", "Responder e-mail · SDK do Foundry, sem ferramentas")

    for email in dados.carregar()["emails"]:
        log.cliente(f"[{email['id']}] {email['assunto']} — {email['corpo']}", caso=email["id"])
        log.modelo(rascunhar(client, email), caso=email["id"])

    log.secao("O que observar")
    print("  • Zero 🔧 no log: ele não consultou a nota fiscal nem a agenda.")
    print("  • Os rascunhos são educados e genéricos: 'vou verificar', 'me diga o melhor horário'.")
    print("  • Quem decide, executa e supervisiona: você, você e você. O modelo só sugere.")


if __name__ == "__main__":
    main()
