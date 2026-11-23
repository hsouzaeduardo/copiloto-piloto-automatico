# Publica o quiz no Azure App Service (Linux, Python) com um comando.
# Uso: .\deploy.ps1 -App quiz-copiloto [-Rg rg-quiz-copiloto] [-Loc brazilsouth] [-Token mvpconf]
param([Parameter(Mandatory)][string]$App, [string]$Rg = "rg-quiz-copiloto", [string]$Loc = "brazilsouth", [string]$Token = "mvpconf")
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

az webapp up --name $App --resource-group $Rg --location $Loc --runtime "PYTHON:3.12" --sku B1 --os-type Linux
az webapp config set --name $App --resource-group $Rg --startup-file "python -m uvicorn app:app --host 0.0.0.0 --port 8000"
az webapp config appsettings set --name $App --resource-group $Rg --settings QUIZ_ADMIN_TOKEN=$Token QUIZ_URL="https://$App.azurewebsites.net/" QUIZ_TEMPO=30 SCM_DO_BUILD_DURING_DEPLOYMENT=true | Out-Null
az webapp restart --name $App --resource-group $Rg | Out-Null

Write-Host ""
Write-Host "Jogadores : https://$App.azurewebsites.net/"
Write-Host "Telão     : https://$App.azurewebsites.net/telao"
Write-Host "Admin     : https://$App.azurewebsites.net/admin   (token: $Token)"
Write-Host "QR code   : https://$App.azurewebsites.net/qr.png"
