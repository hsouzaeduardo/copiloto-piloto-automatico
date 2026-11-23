"""Prepara o ambiente para gravar: limpa o estado da demo anterior e, se pedido, sobe o cockpit.

    python preparar.py            # só limpa
    python preparar.py --cockpit  # limpa e sobe o cockpit em http://localhost:8000
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

RAIZ = Path(__file__).parent
ARQUIVOS = ["eventos.jsonl", "auditoria.jsonl", "demo_atual.json", "stop.flag", "mundo/estado.json"]
PASTAS = ["memoria", "aprovacoes"]

for a in ARQUIVOS:
    (RAIZ / a).unlink(missing_ok=True)
for p in PASTAS:
    shutil.rmtree(RAIZ / p, ignore_errors=True)
print("estado limpo:", ", ".join(ARQUIVOS + [p + "/" for p in PASTAS]))

env = RAIZ / ".env"
if not env.exists():
    print("AVISO: .env não encontrado — copie .env.example e preencha FOUNDRY_PROJECT_ENDPOINT e FOUNDRY_MODEL (o ensaio roda sem isso).")

if "--cockpit" in sys.argv:
    import uvicorn

    print("cockpit em http://localhost:8000  (Ctrl+C para parar)")
    uvicorn.run("cockpit.server:app", host="127.0.0.1", port=8000)
