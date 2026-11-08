"""Cockpit web: painel de observação das demos.

Lê os mesmos arquivos que as demos escrevem (eventos.jsonl, estado do mundo,
pedidos de aprovação) e devolve ao navegador. Dois botões escrevem de volta:
aprovar/negar uma ferramenta e o kill switch.

    uvicorn cockpit.server:app --reload --port 8000
    # ou: python cockpit/server.py
"""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

RAIZ = Path(__file__).parent.parent
EVENTOS = RAIZ / "eventos.jsonl"
AUDITORIA = RAIZ / "auditoria.jsonl"
DEMO_ATUAL = RAIZ / "demo_atual.json"
ESTADO = RAIZ / "mundo" / "estado.json"
APROVACOES = RAIZ / "aprovacoes"
STOP_FLAG = RAIZ / "stop.flag"
INDEX = Path(__file__).parent / "index.html"

app = FastAPI(title="Cockpit — Do copiloto ao piloto automático")


def _jsonl(caminho: Path, ultimos: int = 300) -> list[dict]:
    if not caminho.exists():
        return []
    linhas = caminho.read_text(encoding="utf-8").splitlines()[-ultimos:]
    return [json.loads(l) for l in linhas if l.strip()]


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return INDEX.read_text(encoding="utf-8")


@app.get("/api/estado")
def estado() -> JSONResponse:
    mundo = json.loads(ESTADO.read_text(encoding="utf-8")) if ESTADO.exists() else {}
    pendentes = []
    if APROVACOES.exists():
        for p in sorted(APROVACOES.glob("*.pedido.json")):
            pendentes.append(json.loads(p.read_text(encoding="utf-8")))
    return JSONResponse({
        "demo": json.loads(DEMO_ATUAL.read_text(encoding="utf-8")) if DEMO_ATUAL.exists() else None,
        "eventos": _jsonl(EVENTOS),
        "aprovacoes_pendentes": pendentes,
        "stop": STOP_FLAG.exists(),
        "fila": mundo.get("fila", []),
        "tickets": mundo.get("tickets", []),
        "emails": mundo.get("emails", []),
        "escalacoes": mundo.get("escalacoes", []),
        "reembolsos": sum(1 for p in mundo.get("pedidos", {}).values() if p.get("reembolsado")),
        "auditoria": len(_jsonl(AUDITORIA, 10_000)),
    })


class Decisao(BaseModel):
    id: str
    aprovado: bool


@app.post("/api/aprovar")
def aprovar(d: Decisao) -> dict:
    APROVACOES.mkdir(exist_ok=True)
    (APROVACOES / f"{d.id}.decisao.json").write_text(json.dumps({"aprovado": d.aprovado}), encoding="utf-8")
    return {"ok": True}


@app.post("/api/stop")
def stop() -> dict:
    STOP_FLAG.touch()
    return {"ok": True, "stop": True}


@app.post("/api/rearmar")
def rearmar() -> dict:
    STOP_FLAG.unlink(missing_ok=True)
    return {"ok": True, "stop": False}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("cockpit.server:app", host="127.0.0.1", port=8000, reload=True)
