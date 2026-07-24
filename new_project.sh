#!/usr/bin/env bash
set -e

echo "=================================================="
echo "  ✨ CREATION D'UN NOUVEAU PROJET AGENTIC BUILDER"
echo "=================================================="
echo ""

PNAME="$1"
if [ -z "$PNAME" ]; then
    read -p "Entrez le nom de votre nouveau projet (ex: mon-agent) : " PNAME
fi

if [ -z "$PNAME" ]; then
    echo "[!] Aucun nom de projet fourni. Annulation."
    exit 1
fi

echo ""
echo "[>] Génération du projet dans ../$PNAME ..."
echo ""

python scripts/create_project.py "../$PNAME"
