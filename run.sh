#!/usr/bin/env bash
set -e

echo "=================================================="
echo "  🚀 AGENTIC BUILDER — 1-CLICK LAUNCHER (Linux/macOS)"
echo "=================================================="

# Activate virtualenv if present
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

# Check if state exists for resume
if [ -f ".agent/state.json" ]; then
    echo ""
    read -p "[i] Une session précédente /grill-me en attente a été détectée. Reprendre ? (o/n) : " choice
    if [[ "$choice" =~ ^[Oo]$ ]]; then
        python src/main.py --resume
        exit 0
    fi
fi

TASK="$1"
if [ -z "$TASK" ]; then
    echo ""
    read -p "Entrez la tâche à exécuter par l'agent : " TASK
fi

if [ -z "$TASK" ]; then
    echo "[!] Aucune tâche entrée. Annulation."
    exit 1
fi

echo ""
echo "[>] Lancement de l'agent pour la tâche : \"$TASK\""
echo ""
python src/main.py "$TASK"
