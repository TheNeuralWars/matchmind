#!/usr/bin/env bash
# Deploys to Azure Container Apps (Consumption plan: monthly free grant of vCPU-s/GiB-s/requests).
# Uses `az containerapp up --source .` (builds in ACR; ACR Basic is NOT free — prefer a free Azure for Students /
# sponsored credit subscription, or build with GitHub Actions and push to GHCR instead). Set budget alerts first.
set -euo pipefail
RG=${RG:-matchmind-rg}; LOC=${LOC:-westeurope}; APP=${APP:-matchmind}
az group create -n "$RG" -l "$LOC" -o none
az containerapp up -n "$APP" -g "$RG" -l "$LOC" --source . --ingress external --target-port 8000 \
  --env-vars AZURE_OPENAI_ENDPOINT="${AZURE_OPENAI_ENDPOINT:-}" AZURE_OPENAI_DEPLOYMENT="${AZURE_OPENAI_DEPLOYMENT:-}" \
  AZURE_OPENAI_API_KEY="${AZURE_OPENAI_API_KEY:-}"
az containerapp update -n "$APP" -g "$RG" --min-replicas 0 --max-replicas 1 -o none
