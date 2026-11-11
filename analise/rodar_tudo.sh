#!/bin/bash
# Recria o ambiente (se necessário) e roda toda a análise em ordem.
# Uso:  bash analise/rodar_tudo.sh
set -e
cd "$(dirname "$0")"
RAIZ=".."
if [ ! -x "$RAIZ/.venv/bin/python" ]; then
  python3 -m venv "$RAIZ/.venv"
  "$RAIZ/.venv/bin/pip" install -q -r requirements.txt
fi
PY="$(cd "$RAIZ" && pwd)/.venv/bin/python"
cd scripts
for s in 01_preparar_dados.py 02_estatistica_descritiva.py 03_ajuste_distribuicoes.py \
         04_parametros_validacao.py 05_panorama_porto.py; do
  echo "==> $s"
  "$PY" "$s" > /dev/null
done
echo "OK — resultados em analise/resultados/"
