"""Ritmo da gravação: pausa entre eventos para o cockpit respirar na tela.

DEMO_RITMO (segundos, padrão 3). Use 0 para rodar sem pausas.
"""

from __future__ import annotations

import asyncio
import os
import time

RITMO = float(os.getenv("DEMO_RITMO", "3"))


async def pausa(segundos: float | None = None) -> None:
    await asyncio.sleep(RITMO if segundos is None else min(segundos, RITMO) if RITMO else 0)


def pausa_sync(segundos: float | None = None) -> None:
    time.sleep(RITMO if segundos is None else min(segundos, RITMO) if RITMO else 0)
