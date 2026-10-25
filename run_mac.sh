#!/bin/bash
# One-command run for macOS/Linux:   bash run_mac.sh            (full pipeline)
#                                    bash run_mac.sh classify   (any single step)
set -e
cd "$(dirname "$0")"
if [ ! -d .venv ]; then
  echo "Setting up a Python environment (first run only)..."
  python3 -m venv .venv
fi
source .venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements-collect.txt
if [ -z "$GROQ_API_KEY" ] && [ -f .env ]; then export $(grep -v '^#' .env | xargs); fi
if [ -z "$GROQ_API_KEY" ]; then
  read -r -s -p "Paste your Groq API key (input hidden): " GROQ_API_KEY; echo
  export GROQ_API_KEY
  echo "GROQ_API_KEY=$GROQ_API_KEY" > .env   # saved locally; .env is git-ignored
fi
python run.py "${1:-all}" "${@:2}"
echo
echo "Done. To view the dashboard locally:  source .venv/bin/activate && streamlit run app.py"
