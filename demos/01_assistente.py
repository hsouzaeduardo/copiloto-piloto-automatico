"""Demo 1 — Assistente: responde, mas não resolve.

Uma chamada ao modelo com a FAQ no system prompt. Nenhuma ferramenta,
nenhum estado entre perguntas, nenhum loop. É literalmente uma request.

    python demos/01_assistente.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from comum import log
from comum.config import DEPLOYMENT, cliente_sdk
from mundo import dados
from mundo.ferramentas import FAQ

SYSTEM = f"Você é o assistente de atendimento de uma loja online. Responda em português, de forma curta e cordial.\n\n{FAQ}"


def perguntar(client, pergunta: str) -> str:
    """Entrada → modelo → saída. Fim."""
    resp = client.chat.completions.create(
        model=DEPLOYMENT,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": pergunta},
        ],
    )
    return resp.choices[0].message.content


def main() -> None:
    dados.resetar()
    client = cliente_sdk()
    log.titulo("DEMO 1 — ASSISTENTE  (SDK puro, sem ferramentas)")

    for caso in dados.fila_pendente()[:2]:
        log.cliente(f"[pedido {caso['pedido_id']}] {caso['mensagem']}")
        log.modelo(perguntar(client, caso["mensagem"]))

    log.secao("O que observar")
    print("  • Zero chamadas de ferramenta: o modelo não consultou nenhum pedido.")
    print("  • As respostas são corretas segundo a FAQ — e inúteis para estes clientes.")
    print("  • O limite não é inteligência. É acesso.")


if __name__ == "__main__":
    main()
