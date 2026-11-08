# Do copiloto ao piloto automático

> Até onde deixar a IA decidir por você?

Demos da palestra sobre **assistentes, agentes e agentes autônomos** resolvendo o dia a dia
de um atendimento. O mesmo cenário, as mesmas ferramentas, três orquestradores diferentes.

A tese: a diferença entre os três níveis não é a tecnologia — é o grau de delegação.
Quem decide, quem executa e quem supervisiona.

| Demo | Nível | O que acontece | Stack |
| --- | --- | --- | --- |
| `demos/01_assistente.py` | Assistente | Responde a partir da FAQ. Não consulta nada, não faz nada. | Azure OpenAI SDK puro |
| `demos/02_agente.py` | Agente | Consulta o pedido, abre chamado, responde. **Para e pede aprovação** no reembolso. | Microsoft Agent Framework |
| `demos/03_autonomo.py` | Agente autônomo | Varre a fila sozinho, reembolsa **até R$ 200** por conta própria, escala o resto. Memória, auditoria e kill switch. | Microsoft Agent Framework |

## Estrutura

```
mundo/            mundo simulado (JSON) + ferramentas compartilhadas
  seed.json       estado inicial: pedidos, estoque, fila de atendimento
  dados.py        carregar / salvar / resetar o mundo
  ferramentas.py  consultar_pedido, abrir_chamado, responder_cliente, reembolsar, escalar_para_humano
comum/
  config.py       cliente Azure OpenAI (SDK puro e Agent Framework)
  log.py          log de tool calls no terminal + trilha de auditoria (auditoria.jsonl)
demos/            os três orquestradores — a única coisa que muda entre os níveis
slides/           o deck da palestra (.pptx)
```

Nenhuma demo toca um sistema real: tudo acontece em `mundo/estado.json`,
que é recriado a partir do `seed.json` no início de cada demo.

## Como rodar

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                 # preencha endpoint e deployment
```

Autenticação: com `AZURE_OPENAI_API_KEY` preenchida, usa a chave; sem ela, usa `az login`.

```bash
python demos/01_assistente.py
python demos/02_agente.py        # responda s/N quando ele pedir aprovação
python demos/03_autonomo.py      # em outro terminal: touch stop.flag  (ou crie o arquivo) para encerrar
```

## O que mostrar em cada demo

**Demo 1 — responde, mas não resolve.** As respostas são boas e genéricas. Zero `🔧` no log.
O limite não é inteligência, é acesso.

**Demo 2 — o loop.** O log `🔧` mostra a ordem em que o *modelo* escolheu chamar as ferramentas.
No reembolso, o framework para e espera o `s`. Isso é `approval_mode="always_require"` na
ferramenta, não um `input()` no meio do código.

**Demo 3 — o laço externo.** O agente de dentro é o mesmo da Demo 2. Repare:

- Ninguém o chamou: o gatilho é a fila.
- O caso T-002 pede R$ 450 de reembolso. A ferramenta **recusa** (alçada R$ 200) e o agente escala.
  O guardrail está em `ferramentas.py`, não no prompt.
- O caso T-004 (troca por arrependimento) é ambíguo: ele escala em vez de inventar.
- `memoria/*.json` guarda a sessão de cada caso; `auditoria.jsonl` registra cada decisão.
- `stop.flag` encerra o loop. Sem kill switch não existe autonomia responsável.

## Os três níveis em 10 linhas

```python
# Assistente: uma request
resp = client.chat.completions.create(model=..., messages=[system, user])

# Agente: um loop com ferramentas e aprovação
agent = Agent(client, tools=[consultar, abrir_chamado, responder, tool(reembolsar, approval_mode="always_require")])
resposta = await agent.run(pedido, session=session)
while resposta.user_input_requests: ...  # humano aprova, agente continua

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
