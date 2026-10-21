#!/usr/bin/env bash
# Registry-free deploy to Azure Container Apps (Consumption, scale to zero, max 1 replica).
# Runs the public python:3.12-slim image and fetches this repo's tarball at start, so no ACR (no registry cost).
# Reads AZURE_OPENAI_* from .env; the key is stored as a Container Apps secret, never printed.
set -euo pipefail
cd "$(dirname "$0")/.."
RG=${RG:-rg-matchmind}; LOC=${LOC:-swedencentral}; APP=${APP:-matchmind}; ENV_NAME=${ENV_NAME:-matchmind-env}
REF=${REF:-main}; REPO=${REPO:-TheNeuralWars/matchmind}
set -a; [ -f .env ] && . ./.env; set +a
az extension add -n containerapp --upgrade -y -o none 2>/dev/null || true
az provider register -n Microsoft.App --wait -o none; az provider register -n Microsoft.OperationalInsights --wait -o none
az group create -n "$RG" -l "$LOC" -o none
az containerapp env show -n "$ENV_NAME" -g "$RG" -o none 2>/dev/null || \
  az containerapp env create -n "$ENV_NAME" -g "$RG" -l "$LOC" --logs-destination none -o none
# One python argument ("-c<code>" form, so az's arg parser doesn't eat "-c"): fetch tarball, extract, run the server.
BOOT="-cimport io,os,glob,runpy,sys,tarfile,urllib.request as u; tarfile.open(fileobj=io.BytesIO(u.urlopen('https://codeload.github.com/$REPO/tar.gz/$REF').read())).extractall('/srv'); d=glob.glob('/srv/*')[0]; os.chdir(d); sys.path.insert(0,d); runpy.run_module('matchmind.server', run_name='__main__')"
ARGS=(-n "$APP" -g "$RG" --image python:3.12-slim --command python --args "$BOOT" --cpu 0.25 --memory 0.5Gi --min-replicas 0 --max-replicas 1)
if az containerapp show -n "$APP" -g "$RG" -o none 2>/dev/null; then
  az containerapp secret set -n "$APP" -g "$RG" --secrets aoai-key="${AZURE_OPENAI_API_KEY:-none}" -o none
  az containerapp update "${ARGS[@]}" -o none
else
  az containerapp create "${ARGS[@]}" --environment "$ENV_NAME" --ingress external --target-port 8000 \
    --secrets aoai-key="${AZURE_OPENAI_API_KEY:-none}" \
    --env-vars AZURE_OPENAI_ENDPOINT="${AZURE_OPENAI_ENDPOINT:-}" AZURE_OPENAI_DEPLOYMENT="${AZURE_OPENAI_DEPLOYMENT:-}" \
               AZURE_OPENAI_API_VERSION="${AZURE_OPENAI_API_VERSION:-2024-10-21}" AZURE_OPENAI_API_KEY=secretref:aoai-key -o none
fi
echo "https://$(az containerapp show -n "$APP" -g "$RG" --query properties.configuration.ingress.fqdn -o tsv)"
