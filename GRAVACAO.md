# Roteiro de gravação das demos

Três vídeos curtos (2 a 4 min cada), um por demo, com o **cockpit** ocupando a maior parte da tela
e o **terminal** menor ao lado. O mesmo setup serve para rodar ao vivo.

## Antes de gravar (uma vez)

1. `pip install -r requirements.txt`, `.env` preenchido (`FOUNDRY_PROJECT_ENDPOINT`, `FOUNDRY_MODEL`, `COCKPIT=1`), `az login` feito.
2. Ensaie sem modelo para acertar tela e ritmo: `python demos/ensaio.py 2` (pede aprovação) e `python demos/ensaio.py 3` (termina no kill switch).
3. Layout sugerido (1920×1080): cockpit no navegador à esquerda (~70 %), terminal à direita (~30 %), fonte do terminal 16–18 pt, tema escuro.
   No navegador, esconda a barra de favoritos e use zoom 110 % — o log fica legível no vídeo.
4. Ritmo: `DEMO_RITMO=3` no `.env` (padrão). Suba para 4 se for narrar por cima; `0` para rodar sem pausas.
5. Grave cada demo separadamente; entre uma e outra rode `python preparar.py` (ou deixe — cada demo já reseta o mundo).

## Setup de cada gravação

```bash
# terminal 1 — cockpit (deixe aberto o tempo todo)
python preparar.py --cockpit        # limpa o estado e sobe http://localhost:8000

# terminal 2 — a demo (o que aparece no vídeo)
python demos/01_assistente_email.py
```

Abra http://localhost:8000 antes de dar play. Antes de rodar a demo, o cockpit mostra "aguardando uma demo iniciar…" — bom frame de abertura.

## Demo 1 — E-mail (assistente) · ~2 min

| Momento | O que aparece | O que dizer |
| --- | --- | --- |
| 0:00 | Cockpit vazio, badge cinza "Assistente" ao iniciar | "Um assistente é uma request. Sem ferramentas, sem memória, sem loop." |
| 0:10 | E-mail 1 (segunda via de NF) → rascunho do modelo | "Educado, correto… e inútil: ele não tem a nota." |
| 0:40 | E-mail 2 (remarcar reunião) → rascunho | "Ele não vê a agenda. 'Me diga o melhor horário' — quem decide é você." |
| 1:10 | Painel: **0 tool calls** | "Zero 🔧. O limite não é inteligência, é acesso." |

Plano B: se o Foundry falhar, `python demos/ensaio.py 1` reproduz a demo com rascunhos fixos.

## Demo 2 — Chamado de TI (agente) · ~3 min

| Momento | O que aparece | O que dizer |
| --- | --- | --- |
| 0:00 | Badge "Agente", ticket TI-1101 na fila | "Agora o modelo tem ferramentas e um loop. Ninguém escreveu a ordem das chamadas." |
| 0:15 | 🔧 `consultar_usuario` → senha expirada | "Ele foi olhar o cadastro. Achou a causa." |
| 0:30 | 🔧 `buscar_base_conhecimento` → KB-01 | "Procurou o procedimento." |
| 0:45 | 🔧 `registrar_no_ticket` | "Documentou antes de agir." |
| 1:00 | ⚠ **Aprovação pendente** aparece à direita — o terminal fica parado | "Reset de senha é sensível. O framework PAROU. Isso é `approval_mode='always_require'` na ferramenta, não um `input()` no código." |
| 1:20 | Clique em **Aprovar** | "Human-in-the-loop: eu aprovo, ele continua." |
| 1:30 | 🔧 `resetar_senha` → 🔧 `responder_usuario` → 🤖 resumo | "Resolveu o ticket e devolveu o controle. Ele não decide SE deve agir — nós o chamamos." |

Variação para gravar depois (opcional): clique em **Negar** e mostre o agente contornando sem executar a ação.

## Demo 3 — Atendimento comercial (autônomo) · ~4 min

| Momento | O que aparece | O que dizer |
| --- | --- | --- |
| 0:00 | Badge roxo "Agente autônomo", 5 casos na fila | "Mesmo agente da Demo 2. A diferença está no laço de fora: ninguém o chama, ele varre a fila." |
| 0:15 | T-001: consulta e responde | "Dúvida de prazo. Resolve sozinho." |
| 0:45 | **T-002**: 🔧 `reembolsar(1043, 450)` → **RECUSADO pela ferramenta** → `escalar_para_humano` | "R$ 450 passa da alçada de R$ 200. A ferramenta recusou **em código**. O prompt não tem voto nisso." |
| 1:30 | T-003: reembolso de R$ 95 aplicado; painel **Reembolsos: 1** | "Dentro da alçada, ele age sem perguntar." |
| 2:00 | **T-004**: escalado | "Caso ambíguo. Em vez de inventar política, escala." |
| 2:30 | T-005 resolvido; auditoria mostra 5 decisões; "fila vazia · aguardando" | "Human-ON-the-loop: eu leio o log, não aprovo cada passo. Tudo em `auditoria.jsonl`." |
| 3:00 | Clique em **KILL SWITCH** → "loop encerrado" | "Sem isso não existe autonomia responsável." |

Pontos plantados no `seed.json` (não precisa improvisar): T-002 = R$ 450 (acima da alçada), T-004 = troca por arrependimento (ambíguo).

## Se der errado na hora

- Foundry fora / sem rede: `python demos/ensaio.py N` reproduz o mesmo fluxo no mesmo cockpit, com texto fixo. A plateia vê a mesma coisa.
- Aprovação não aparece no cockpit: confirme `COCKPIT=1` no `.env`; sem isso a pergunta vai para o terminal (`s/N`).
- Loop da Demo 3 não para: crie o arquivo `stop.flag` na raiz do projeto (`touch stop.flag` / `ni stop.flag` no PowerShell).
- Estado sujo (fila já resolvida): `python preparar.py` e rode de novo.
