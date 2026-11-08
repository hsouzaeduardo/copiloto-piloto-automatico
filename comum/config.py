"""Configuração do Microsoft Foundry, para o SDK puro (Demo 1) e para o Agent Framework (Demos 2 e 3).

Variáveis de ambiente (ver .env.example):
  FOUNDRY_PROJECT_ENDPOINT   https://<recurso>.services.ai.azure.com/api/projects/<projeto>
  FOUNDRY_MODEL              nome do deployment, ex.: gpt-4o-mini
  COCKPIT                    1 para aprovar pelo cockpit web; vazio para aprovar no terminal

Autenticação: `az login` (AzureCliCredential). Sem chave de API no código, de propósito —
é o mesmo recado da palestra: o agente age com credencial própria, não com segredo colado.
"""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

PROJECT_ENDPOINT = os.environ["FOUNDRY_PROJECT_ENDPOINT"]
MODEL = os.environ["FOUNDRY_MODEL"]
USAR_COCKPIT = os.getenv("COCKPIT", "").strip() in {"1", "true", "sim"}


def credencial():
    from azure.identity import AzureCliCredential

    return AzureCliCredential()


def cliente_sdk():
    """Cliente OpenAI do projeto Foundry — usado só na Demo 1, de propósito: é uma request."""
    from azure.ai.projects import AIProjectClient

    projeto = AIProjectClient(endpoint=PROJECT_ENDPOINT, credential=credencial())
    return projeto.get_openai_client()


def cliente_maf(**kwargs):
    """Cliente do Microsoft Agent Framework apontando para o modelo do projeto Foundry."""
    from agent_framework.foundry import FoundryChatClient

    return FoundryChatClient(project_endpoint=PROJECT_ENDPOINT, model=MODEL, credential=credencial(), **kwargs)
