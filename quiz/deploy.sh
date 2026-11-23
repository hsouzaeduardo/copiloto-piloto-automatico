#!/usr/bin/env bash
# Publica o quiz no Azure App Service (Linux, Python) com um comando.
# Uso: ./deploy.sh <nome-do-app> [resource-group] [regiao] [token-admin]
set -euo pipefail
APP="${1:?nome do app, ex.: quiz-copiloto}"
RG="${2:-rg-quiz-copiloto}"
LOC="${3:-brazilsouth}"
TOKEN="${4:-mvpconf}"
cd "$(dirname "$0")"

az webapp up --name "$APP" --resource-group "$RG" --location "$LOC" --runtime "PYTHON:3.12" --sku B1 --os-type Linux
az webapp config set --name "$APP" --resource-group "$RG" \
  --startup-file "python -m uvicorn app:app --host 0.0.0.0 --port 8000"
az webapp config appsettings set --name "$APP" --resource-group "$RG" --settings \
  QUIZ_ADMIN_TOKEN="$TOKEN" QUIZ_URL="https://$APP.azurewebsites.net/" QUIZ_TEMPO=30 SCM_DO_BUILD_DURING_DEPLOYMENT=true >/dev/null
az webapp restart --name "$APP" --resource-group "$RG" >/dev/null

echo
echo "Jogadores : https://$APP.azurewebsites.net/"
echo "Telão     : https://$APP.azurewebsites.net/telao"
echo "Admin     : https://$APP.azurewebsites.net/admin   (token: $TOKEN)"
echo "QR code   : https://$APP.azurewebsites.net/qr.png"
