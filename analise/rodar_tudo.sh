#!/bin/bash
# Recria o ambiente (se necessário) e roda a análise em ordem:
#   1) limpeza -> tabela limpa   2) panorama por tipo de navio   3) gráficos (a partir da tabela limpa)
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
for s in 1_limpeza_dados.py 2_panorama_porto.py 3_graficos.py; do
  echo "==> $s"
  "$PY" "$s" > /dev/null
done
rm -rf __pycache__
echo "OK — resultados em analise/resultados/"
