"""Quiz da palestra — celular do jogador, telão e admin num único app.

Estado em memória (uma instância basta para uma palestra). Pontuação estilo Kahoot:
1000 pontos pela resposta certa, menos até 50% conforme a demora.

    uvicorn app:app --reload --port 8080
    /         jogador (celular)
    /telao    placar e distribuição das respostas (projetar)
    /admin    controle do apresentador (token em QUIZ_ADMIN_TOKEN)
"""

from __future__ import annotations

import json
import os
import secrets
import time
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response
from pydantic import BaseModel

PASTA = Path(__file__).parent
PERGUNTAS = json.loads((PASTA / "perguntas.json").read_text(encoding="utf-8"))
TEMPO_LIMITE = int(os.getenv("QUIZ_TEMPO", "30"))
ADMIN_TOKEN = os.getenv("QUIZ_ADMIN_TOKEN", "mvpconf")

app = FastAPI(title="Quiz — Do copiloto ao piloto automático")


class Estado:
    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.fase = "lobby"            # lobby | pergunta | revelado | final
        self.atual: int | None = None  # índice da pergunta
        self.abriu_em: float = 0.0
        self.jogadores: dict[str, dict] = {}        # id -> {nome, pontos}
        self.respostas: dict[int, dict[str, dict]] = {}  # idx -> jogador_id -> {opcao, pontos, tempo}


E = Estado()


def _pagina(nome: str) -> str:
    return (PASTA / "paginas" / nome).read_text(encoding="utf-8")


def _exigir_admin(token: str | None) -> None:
    if token != ADMIN_TOKEN:
        raise HTTPException(401, "token de admin inválido")


def _ranking(limite: int = 10) -> list[dict]:
    ordem = sorted(E.jogadores.values(), key=lambda j: (-j["pontos"], j["nome"].lower()))
    return [{"nome": j["nome"], "pontos": j["pontos"]} for j in ordem[:limite]]


def _tempo_restante() -> int:
    if E.fase != "pergunta":
        return 0
    return max(0, int(TEMPO_LIMITE - (time.time() - E.abriu_em)))


def _distribuicao(idx: int) -> list[int]:
    contagem = [0] * len(PERGUNTAS[idx]["opcoes"])
    for r in E.respostas.get(idx, {}).values():
        contagem[r["opcao"]] += 1
    return contagem


# ------------------------------------------------------------------ páginas

@app.get("/", response_class=HTMLResponse)
def jogador_html() -> str:
    return _pagina("jogador.html")


@app.get("/telao", response_class=HTMLResponse)
def telao_html() -> str:
    return _pagina("telao.html")


@app.get("/admin", response_class=HTMLResponse)
def admin_html() -> str:
    return _pagina("admin.html")


# ------------------------------------------------------------------ jogador

class Entrada(BaseModel):
    nome: str


@app.post("/api/entrar")
def entrar(e: Entrada) -> dict:
    nome = e.nome.strip()[:24] or "Anônimo"
    usados = {j["nome"].lower() for j in E.jogadores.values()}
    base, n = nome, 2
    while nome.lower() in usados:
        nome, n = f"{base} {n}", n + 1
    jid = secrets.token_hex(8)
    E.jogadores[jid] = {"nome": nome, "pontos": 0}
    return {"id": jid, "nome": nome}


@app.get("/api/estado")
def estado(jogador: str | None = None) -> JSONResponse:
    atual = PERGUNTAS[E.atual] if E.atual is not None else None
    minha = E.respostas.get(E.atual, {}).get(jogador) if (E.atual is not None and jogador) else None
    eu = E.jogadores.get(jogador) if jogador else None
    return JSONResponse({
        "fase": E.fase,
        "tempo_limite": TEMPO_LIMITE,
        "tempo_restante": _tempo_restante(),
        "total_perguntas": len(PERGUNTAS),
        "numero": (E.atual + 1) if E.atual is not None else None,
        "pergunta": {"texto": atual["pergunta"], "opcoes": atual["opcoes"]} if atual else None,
        "correta": atual["correta"] if (atual and E.fase in {"revelado", "final"}) else None,
        "explicacao": atual["explicacao"] if (atual and E.fase in {"revelado", "final"}) else None,
        "distribuicao": _distribuicao(E.atual) if (E.atual is not None and E.fase in {"revelado", "final"}) else None,
        "respondidos": len(E.respostas.get(E.atual, {})) if E.atual is not None else 0,
        "jogadores": len(E.jogadores),
        "ranking": _ranking(),
        "minha_resposta": minha,
        "eu": eu,
    })


class Resposta(BaseModel):
    jogador: str
    opcao: int


@app.post("/api/responder")
def responder(r: Resposta) -> dict:
    if E.fase != "pergunta" or E.atual is None:
        raise HTTPException(409, "nenhuma pergunta aberta")
    if r.jogador not in E.jogadores:
        raise HTTPException(404, "jogador desconhecido — entre de novo")
    respostas = E.respostas.setdefault(E.atual, {})
    if r.jogador in respostas:
        return respostas[r.jogador]
    decorrido = time.time() - E.abriu_em
    if decorrido > TEMPO_LIMITE + 2:
        raise HTTPException(409, "tempo esgotado")
    certa = r.opcao == PERGUNTAS[E.atual]["correta"]
    pontos = round(1000 * (1 - min(decorrido, TEMPO_LIMITE) / TEMPO_LIMITE / 2)) if certa else 0
    respostas[r.jogador] = {"opcao": r.opcao, "pontos": pontos, "tempo": round(decorrido, 1)}
    E.jogadores[r.jogador]["pontos"] += pontos
    return respostas[r.jogador]


# ------------------------------------------------------------------ admin

@app.get("/api/admin/perguntas")
def admin_perguntas(x_token: str | None = Header(default=None)) -> list[dict]:
    _exigir_admin(x_token)
    return [{"id": p["id"], "momento": p["momento"], "pergunta": p["pergunta"]} for p in PERGUNTAS]


@app.post("/api/admin/abrir/{numero}")
def abrir(numero: int, x_token: str | None = Header(default=None)) -> dict:
    _exigir_admin(x_token)
    if not 1 <= numero <= len(PERGUNTAS):
        raise HTTPException(404, "pergunta não existe")
    E.atual, E.fase, E.abriu_em = numero - 1, "pergunta", time.time()
    E.respostas.setdefault(E.atual, {})
    return {"ok": True, "fase": E.fase, "numero": numero}


@app.post("/api/admin/revelar")
def revelar(x_token: str | None = Header(default=None)) -> dict:
    _exigir_admin(x_token)
    if E.fase == "pergunta":
        E.fase = "revelado"
    return {"ok": True, "fase": E.fase}


@app.post("/api/admin/final")
def final(x_token: str | None = Header(default=None)) -> dict:
    _exigir_admin(x_token)
    E.fase = "final"
    return {"ok": True, "fase": E.fase}


@app.post("/api/admin/lobby")
def lobby(x_token: str | None = Header(default=None)) -> dict:
    _exigir_admin(x_token)
    E.fase, E.atual = "lobby", None
    return {"ok": True, "fase": E.fase}


@app.post("/api/admin/reset")
def reset(x_token: str | None = Header(default=None)) -> dict:
    _exigir_admin(x_token)
    E.reset()
    return {"ok": True}


@app.get("/qr.png")
def qr_png(request: Request) -> Response:
    """QR code da URL pública do quiz (para o telão e para colar nos slides)."""
    import io

    import qrcode

    base = os.getenv("QUIZ_URL") or str(request.base_url)
    imagem = qrcode.make(base, box_size=12, border=1)
    buf = io.BytesIO()
    imagem.save(buf, format="PNG")
    return Response(buf.getvalue(), media_type="image/png", headers={"Cache-Control": "no-store"})


@app.get("/health")
def health() -> dict:
    return {"ok": True, "fase": E.fase, "jogadores": len(E.jogadores)}
