"""Mundo simulado: pedidos, estoque e fila de atendimento num JSON.

Nenhuma demo fala com um sistema real. Tudo o que o agente "faz" acontece
neste arquivo, o que torna as demos reproduzíveis e seguras para rodar ao vivo.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

PASTA = Path(__file__).parent
SEED = PASTA / "seed.json"
ESTADO = PASTA / "estado.json"


def resetar() -> None:
    """Volta o mundo ao estado inicial (chame antes de cada demo)."""
    shutil.copyfile(SEED, ESTADO)


def carregar() -> dict:
    if not ESTADO.exists():
        resetar()
    return json.loads(ESTADO.read_text(encoding="utf-8"))


def salvar(mundo: dict) -> None:
    ESTADO.write_text(json.dumps(mundo, ensure_ascii=False, indent=2), encoding="utf-8")


def fila_pendente() -> list[dict]:
    return [c for c in carregar()["fila"] if c["status"] == "pendente"]


def marcar_caso(caso_id: str, status: str) -> None:
    mundo = carregar()
    for caso in mundo["fila"]:
        if caso["id"] == caso_id:
            caso["status"] = status
    salvar(mundo)
