"""Mundo simulado: e-mails, usuários e tickets de TI, pedidos e fila comercial — tudo num JSON.

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
    """Volta o mundo ao estado inicial (chame no início de cada demo)."""
    shutil.copyfile(SEED, ESTADO)


def carregar() -> dict:
    if not ESTADO.exists():
        resetar()
    return json.loads(ESTADO.read_text(encoding="utf-8"))


def salvar(mundo: dict) -> None:
    ESTADO.write_text(json.dumps(mundo, ensure_ascii=False, indent=2), encoding="utf-8")


def pendentes(lista: str) -> list[dict]:
    """Itens com status 'pendente' em `tickets` (Demo 2) ou `fila` (Demo 3)."""
    return [c for c in carregar()[lista] if c["status"] == "pendente"]


def marcar(lista: str, item_id: str, status: str) -> None:
    mundo = carregar()
    for item in mundo[lista]:
        if item["id"] == item_id:
            item["status"] = status
    salvar(mundo)
