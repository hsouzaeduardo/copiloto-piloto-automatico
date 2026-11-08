"""Log no terminal (o que a plateia vê) e trilha de auditoria (o que fica gravado)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

AUDITORIA = Path(__file__).parent.parent / "auditoria.jsonl"

CINZA, TEAL, AMBAR, VERMELHO, NEGRITO, RESET = "\033[90m", "\033[36m", "\033[33m", "\033[31m", "\033[1m", "\033[0m"


def titulo(texto: str) -> None:
    print(f"\n{NEGRITO}{'=' * 70}\n{texto}\n{'=' * 70}{RESET}")


def secao(texto: str) -> None:
    print(f"\n{NEGRITO}— {texto}{RESET}")


def cliente(texto: str) -> None:
    print(f"\n{AMBAR}👤 Cliente:{RESET} {texto}")


def modelo(texto: str) -> None:
    print(f"\n{TEAL}🤖 Modelo:{RESET} {texto}")


def aviso(texto: str) -> None:
    print(f"\n{VERMELHO}⚠  {texto}{RESET}")


def log_ferramenta(nome: str, args: dict, resultado: str) -> None:
    """Toda ferramenta passa por aqui: é o 'log de tool calls' que aparece na tela."""
    print(f"   {CINZA}🔧 {nome}({json.dumps(args, ensure_ascii=False)}){RESET}")
    print(f"   {CINZA}   ↳ {resultado[:110]}{RESET}")


def auditar(evento: dict) -> None:
    """Grava uma linha JSON por decisão. Sem isto, não existe agente autônomo em produção."""
    evento = {"quando": datetime.now(timezone.utc).isoformat(timespec="seconds"), **evento}
    with AUDITORIA.open("a", encoding="utf-8") as f:
        f.write(json.dumps(evento, ensure_ascii=False) + "\n")
