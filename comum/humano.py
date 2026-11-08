"""O humano no loop: aprovação e kill switch.

Com COCKPIT=1 a aprovação vem do navegador (o cockpit grava a decisão num arquivo);
sem cockpit, vem do terminal. O agente não sabe a diferença — e esse é o ponto.
"""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path

from comum import log
from comum.config import USAR_COCKPIT

RAIZ = Path(__file__).parent.parent
APROVACOES = RAIZ / "aprovacoes"
STOP_FLAG = RAIZ / "stop.flag"


def kill_switch() -> bool:
    return STOP_FLAG.exists()


def aprovar(nome_funcao: str, argumentos, caso: str | None = None) -> bool:
    """Pergunta a um humano se a ferramenta pode rodar. Bloqueia até a resposta."""
    log.aviso(f"Aprovação necessária: {nome_funcao}({argumentos})")
    return _aprovar_cockpit(nome_funcao, argumentos, caso) if USAR_COCKPIT else _aprovar_terminal()


def _aprovar_terminal() -> bool:
    return input("   Aprovar? [s/N] ").strip().lower() == "s"


def _aprovar_cockpit(nome_funcao: str, argumentos, caso: str | None) -> bool:
    APROVACOES.mkdir(exist_ok=True)
    pedido_id = uuid.uuid4().hex[:8]
    pedido = APROVACOES / f"{pedido_id}.pedido.json"
    decisao = APROVACOES / f"{pedido_id}.decisao.json"
    pedido.write_text(json.dumps({"id": pedido_id, "funcao": nome_funcao, "args": str(argumentos), "caso": caso}, ensure_ascii=False), encoding="utf-8")
    log.sistema(f"   aguardando decisão no cockpit (pedido {pedido_id})…")
    while not decisao.exists():
        if kill_switch():
            pedido.unlink(missing_ok=True)
            return False
        time.sleep(0.5)
    aprovado = bool(json.loads(decisao.read_text(encoding="utf-8")).get("aprovado"))
    pedido.unlink(missing_ok=True)
    decisao.unlink(missing_ok=True)
    log.sistema(f"   cockpit respondeu: {'APROVADO' if aprovado else 'NEGADO'}")
    return aprovado
