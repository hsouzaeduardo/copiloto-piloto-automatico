# Quiz da palestra

Quiz ao vivo, estilo Kahoot, para as três perguntas do deck. Um único app FastAPI com três telas:

| URL | Quem usa | O que mostra |
| --- | --- | --- |
| `/` | plateia, no celular | entra com um nome, responde A/B/C, vê se acertou e a pontuação |
| `/telao` | projetor | lobby com QR code, pergunta com cronômetro e contagem de respostas, distribuição das respostas, placar final |
| `/admin` | você, no celular ou segundo monitor | abre cada pergunta, revela, mostra o placar final, zera |

Pontuação: 1000 pontos pela resposta certa, caindo até 500 conforme a demora (30 s por pergunta).
Estado em memória — basta uma instância e aguenta uma plateia de evento com folga.

## Publicar no Azure (App Service, um comando)

Pré-requisitos: `az login` feito e uma assinatura selecionada.

```bash
cd quiz
./deploy.sh quiz-copiloto                      # bash / macOS / WSL
.\deploy.ps1 -App quiz-copiloto                # PowerShell
```

Parâmetros opcionais: resource group (padrão `rg-quiz-copiloto`), região (`brazilsouth`) e token de admin (`mvpconf`).
O nome do app precisa ser único em `*.azurewebsites.net`. O script cria App Service Linux B1 (Python 3.12),
configura o startup do uvicorn, as variáveis e imprime as URLs:

```
Jogadores : https://quiz-copiloto.azurewebsites.net/
Telão     : https://quiz-copiloto.azurewebsites.net/telao
Admin     : https://quiz-copiloto.azurewebsites.net/admin   (token: mvpconf)
QR code   : https://quiz-copiloto.azurewebsites.net/qr.png
```

Para republicar depois de uma mudança, rode o mesmo comando. Para apagar tudo: `az group delete -n rg-quiz-copiloto`.

Alternativa em container (Container Apps ou qualquer host Docker): `docker build -t quiz . && docker run -p 8080:8080 -e QUIZ_ADMIN_TOKEN=... quiz`.

## Variáveis

| Variável | Padrão | Para quê |
| --- | --- | --- |
| `QUIZ_ADMIN_TOKEN` | `mvpconf` | senha da tela `/admin` — troque no deploy |
| `QUIZ_TEMPO` | `30` | segundos por pergunta |
| `QUIZ_URL` | URL da requisição | URL codificada no QR (útil atrás de proxy) |

## No dia

1. Abra `/telao` no projetor antes da palestra começar (o lobby com o QR já serve de slide de espera) e `/admin` no celular.
2. Nos três slides de quiz do deck, cole o `qr.png` (baixe de `/qr.png`) no quadrado branco. O mesmo QR vale para as três perguntas.
3. No momento do quiz: **Abrir pergunta N** → 30 s → **Revelar resposta** (o telão mostra a distribuição e o placar) → volte aos slides.
4. Depois da pergunta 3: **Placar final**. Ganhador no telão.
5. Para testar antes: `uvicorn app:app --port 8080` local e abra as três URLs; **Zerar tudo** no admin limpa os testes.

As perguntas estão em `perguntas.json` — edite e republique para mudar.
