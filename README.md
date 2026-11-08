# Do copiloto ao piloto automático

> Até onde deixar a IA decidir por você?

Demos da palestra sobre **assistentes, agentes e agentes autônomos** resolvendo o dia a dia.
Três cenários, um por nível, com as mesmas peças por baixo: Python, Microsoft Foundry e
Microsoft Agent Framework — e um **cockpit web** para a plateia acompanhar o agente trabalhando.

A tese: a diferença entre os três níveis não é a tecnologia — é o grau de delegação.
Quem decide, quem executa e quem supervisiona.

| Demo | Nível | Cenário | O que acontece | Stack |
| --- | --- | --- | --- | --- |
| `demos/01_assistente_email.py` | Assistente | Responder e-mail | Rascunha a resposta. Não consulta nada, não envia nada. | SDK do Foundry (`get_openai_client`) |
| `demos/02_agente_chamados.py` | Agente | Chamados de TI | Consulta o usuário, busca a base, diagnostica e corrige. **Para e pede aprovação** no reset de senha/MFA. | Agent Framework (`Agent`, `@tool`, `approval_mode`) |
| `demos/03_autonomo_comercial.py` | Agente autônomo | Atendimento comercial | Varre a fila sozinho, reembolsa **até R$ 200** por conta própria, escala o resto. Memória, auditoria e kill switch. | Agent Framework + laço externo |

## Estrutura

```
mundo/              mundo simulado (JSON) + ferramentas dos cenários
  seed.json         e-mails, usuários e tickets de TI, pedidos e fila comercial
  dados.py          carregar / salvar / resetar o mundo
  ferramentas.py    funções Python que viram tools; a alçada do reembolso mora aqui
comum/
  config.py         Foundry: SDK puro (Demo 1) e FoundryChatClient (Demos 2 e 3)
  humano.py         aprovação (terminal ou cockpit) e kill switch
  log.py            terminal + eventos.jsonl (cockpit) + auditoria.jsonl
cockpit/
  server.py         FastAPI: lê eventos e estado, grava aprovações e stop.flag
  index.html        painel: fila, log de tool calls, aprovações, auditoria, kill switch
demos/              os três orquestradores — a única coisa que muda entre os níveis
slides/             o deck da palestra (.pptx)
```

Nenhuma demo toca um sistema real: tudo acontece em `mundo/estado.json`,
recriado a partir do `seed.json` no início de cada demo.

## Como rodar

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                 # endpoint do projeto Foundry + deployment
az login                                             # autenticação: AzureCliCredential, sem chave no código
```

Terminal 1 — o cockpit (abra http://localhost:8000 no navegador, de preferência no telão):

```bash
uvicorn cockpit.server:app --port 8000
```

Terminal 2 — as demos, uma de cada vez:

```bash
python demos/01_assistente_email.py
python demos/02_agente_chamados.py        # aprove pelo cockpit (COCKPIT=1) ou com s/N no terminal
python demos/03_autonomo_comercial.py     # encerre pelo botão KILL SWITCH do cockpit ou com: touch stop.flag
```

Sem cockpit: deixe `COCKPIT=` vazio no `.env` e tudo acontece no terminal.

## O que mostrar em cada demo

**Demo 1 — responde, mas não resolve.** Dois e-mails: segunda via de nota fiscal e remarcar
uma reunião. Os rascunhos são educados e genéricos — ele não tem a nota nem a agenda.
Zero `🔧` no log. O limite não é inteligência, é acesso.

**Demo 2 — o loop.** Ticket de VPN. O log `🔧` mostra a ordem em que o *modelo* escolheu chamar:
usuário → base de conhecimento → diagnóstico → `resetar_senha`. Aí o framework para e o
cockpit mostra o botão **Aprovar**. Isso é `approval_mode="always_require"` na ferramenta,
não um `input()` no meio do código.

**Demo 3 — o laço externo.** O agente de dentro é igual ao da Demo 2. Repare:

- Ninguém o chamou: o gatilho é a fila.
- O caso T-002 pede R$ 450 de reembolso. A ferramenta **recusa** (alçada R$ 200) e o agente escala.
  O guardrail está em `ferramentas.py`, não no prompt.
- O caso T-004 (troca por arrependimento) é ambíguo: ele escala em vez de inventar.
- `memoria/*.json` guarda a sessão de cada caso; `auditoria.jsonl` registra cada decisão.
- **KILL SWITCH** no cockpit (ou `stop.flag`) encerra o loop. Sem isso não existe autonomia responsável.

## Os três níveis em 10 linhas

```python
# Assistente: uma request
resp = openai.responses.create(model=MODEL, instructions=..., input=email)

# Agente: um loop com ferramentas e aprovação
agent = Agent(client, tools=[consultar_usuario, buscar_base, tool(resetar_senha, approval_mode="always_require")])
resposta = await agent.run(ticket, session=session)
while resposta.user_input_requests: ...   # humano aprova, agente continua

# Autônomo: o mesmo loop, com gatilho, memória, alçada e kill switch
while not kill_switch():
    for caso in fila.pendentes():
        session = memoria.carregar(caso)
        await agent.run(caso, session=session)   # reembolsar() recusa acima da alçada
        auditoria.registrar(caso)
```

## Regra para levar para casa

Autonomia se conquista por evidência, não por decreto.
Comece no assistente, meça, suba um nível quando a taxa de erro for aceitável e o processo tiver dono.

---

Henrique Eduardo Souza · Microsoft MVP · [linkedin.com/in/hsouzaeduardo](https://linkedin.com/in/hsouzaeduardo) · [youtube.com/@cloud4developers](https://youtube.com/@cloud4developers)
