"""Três saídas, uma chamada.

- Terminal: o que a plateia vê quando a demo roda sem cockpit.
- eventos.jsonl: o barramento que o cockpit web lê (um JSON por linha).
- auditoria.jsonl: a trilha que fica — cada decisão do agente autônomo.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).parent.parent
EVENTOS = RAIZ / "eventos.jsonl"
AUDITORIA = RAIZ / "auditoria.jsonl"
DEMO_ATUAL = RAIZ / "demo_atual.json"

CINZA, TEAL, AMBAR, VERMELHO, NEGRITO, RESET = "\033[90m", "\033[36m", "\033[33m", "\033[31m", "\033[1m", "\033[0m"


def _agora() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _evento(tipo: str, **dados) -> None:
    with EVENTOS.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"quando": _agora(), "tipo": tipo, **dados}, ensure_ascii=False) + "\n")


def iniciar_demo(nome: str, nivel: str, descricao: str) -> None:
    """Limpa o barramento e anuncia ao cockpit qual demo está no ar."""
    EVENTOS.write_text("", encoding="utf-8")
    DEMO_ATUAL.write_text(json.dumps({"nome": nome, "nivel": nivel, "descricao": descricao, "inicio": _agora()}, ensure_ascii=False), encoding="utf-8")
    print(f"\n{NEGRITO}{'=' * 70}\n{nome}\n{descricao}\n{'=' * 70}{RESET}")
    _evento("sistema", texto=f"{nome} iniciada")


def secao(texto: str) -> None:
    print(f"\n{NEGRITO}— {texto}{RESET}")


def cliente(texto: str, caso: str | None = None) -> None:
    print(f"\n{AMBAR}👤 Cliente:{RESET} {texto}")
    _evento("cliente", texto=texto, caso=caso)


def modelo(texto: str, caso: str | None = None) -> None:
    print(f"\n{TEAL}🤖 Modelo:{RESET} {texto}")
    _evento("modelo", texto=texto, caso=caso)


def aviso(texto: str) -> None:
    print(f"\n{VERMELHO}⚠  {texto}{RESET}")
    _evento("aviso", texto=texto)


def sistema(texto: str) -> None:
    print(f"{CINZA}{texto}{RESET}")
    _evento("sistema", texto=texto)


def log_ferramenta(nome: str, args: dict, resultado: str) -> None:
    """Toda ferramenta passa por aqui: é o 'log de tool calls' que aparece na tela e no cockpit."""
    print(f"   {CINZA}🔧 {nome}({json.dumps(args, ensure_ascii=False)}){RESET}")
    print(f"   {CINZA}   ↳ {resultado[:110]}{RESET}")
    _evento("ferramenta", nome=nome, args=args, resultado=resultado[:300])


def auditar(evento: dict) -> None:
    """Grava uma linha por decisão. Sem isto, não existe agente autônomo em produção."""
    with AUDITORIA.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"quando": _agora(), **evento}, ensure_ascii=False) + "\n")
    _evento("auditoria", **evento)
