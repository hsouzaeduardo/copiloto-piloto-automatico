"""Configuração do Azure OpenAI, para o SDK puro (Demo 1) e para o Agent Framework (Demos 2 e 3).

Variáveis de ambiente (ver .env.example):
  AZURE_OPENAI_ENDPOINT      https://<recurso>.openai.azure.com
  AZURE_OPENAI_DEPLOYMENT    nome do deployment, ex.: gpt-4o-mini
  AZURE_OPENAI_API_VERSION   ex.: 2024-10-21
  AZURE_OPENAI_API_KEY       opcional; sem ela, usa `az login` (AzureCliCredential)
"""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

ENDPOINT = os.environ["AZURE_OPENAI_ENDPOINT"]
DEPLOYMENT = os.environ["AZURE_OPENAI_DEPLOYMENT"]
API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21")
API_KEY = os.getenv("AZURE_OPENAI_API_KEY")


def cliente_sdk():
    """Cliente Azure OpenAI do SDK oficial — usado só na Demo 1, de propósito."""
    from openai import AzureOpenAI

    if API_KEY:
        return AzureOpenAI(azure_endpoint=ENDPOINT, api_key=API_KEY, api_version=API_VERSION)

    from azure.identity import AzureCliCredential, get_bearer_token_provider

    provedor = get_bearer_token_provider(AzureCliCredential(), "https://cognitiveservices.azure.com/.default")
    return AzureOpenAI(azure_endpoint=ENDPOINT, azure_ad_token_provider=provedor, api_version=API_VERSION)


def cliente_maf(**kwargs):
    """Cliente do Microsoft Agent Framework apontando para o Azure OpenAI."""
    from agent_framework.openai import OpenAIChatCompletionClient

    auth = {"api_key": API_KEY} if API_KEY else {"credential": _credencial_azure()}
    return OpenAIChatCompletionClient(
        model=DEPLOYMENT,
        azure_endpoint=ENDPOINT,
        api_version=API_VERSION,
        **auth,
        **kwargs,
    )


def _credencial_azure():
    from azure.identity import AzureCliCredential

    return AzureCliCredential()
