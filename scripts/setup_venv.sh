#!/usr/bin/env bash
# Create and populate a local .venv for this project
set -euo pipefail

PYTHON=${PYTHON:-python3}
VENV_DIR=.venv

echo "Creating virtual environment in ${VENV_DIR} using ${PYTHON}..."
${PYTHON} -m venv ${VENV_DIR}
echo "Activating and installing requirements..."
source ${VENV_DIR}/bin/activate
pip install --upgrade pip
if [ -f requirements.txt ]; then
  pip install -r requirements.txt
fi

echo "Done. Activate with: source ${VENV_DIR}/bin/activate"
