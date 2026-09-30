#!/bin/bash
# Installa Jarvis su questo Mac. Si apre con un doppio clic.
#
# Fa da solo i passaggi della sezione 3 di SETUP.md: crea la cartella del
# vault in Documenti, ci mette dentro il sistema come System/, lancia
# l'installatore e scrive il nome del proprietario nella configurazione.
#
# Per le prove automatiche, senza finestre: impostare JARVIS_CARTELLA (percorso
# completo del vault da creare), JARVIS_NOME e JARVIS_EMAIL.

set -u

REPO_URL="https://github.com/edoardop06/jarvis.git"
QUI="$(cd "$(dirname "$0")" && pwd)"
SILENZIOSO="${JARVIS_CARTELLA:+1}"

avviso() {
    echo "$1"
    [ -z "$SILENZIOSO" ] && osascript -e "display dialog \"$1\" buttons {\"OK\"} default button 1 with title \"Installa Jarvis\"" >/dev/null 2>&1
    return 0
}

chiedi() {  # domanda, risposta proposta
    osascript -e "text returned of (display dialog \"$1\" default answer \"$2\" with title \"Installa Jarvis\")" 2>/dev/null
}

# 1. git e python3 arrivano con gli strumenti per sviluppatori di Apple.
if ! xcode-select -p >/dev/null 2>&1; then
    xcode-select --install >/dev/null 2>&1
    avviso "Mancano due strumenti di Apple. Si è aperta una finestra per installarli: premi Installa, aspetta che finisca, poi riapri questo file."
    exit 1
fi

# 2. Dove mettere il vault.
if [ -n "$SILENZIOSO" ]; then
    VAULT="$JARVIS_CARTELLA"
else
    NOME_CARTELLA="$(chiedi "Come vuoi chiamare la cartella di Jarvis? Verrà creata dentro Documenti." "Jarvis")" || exit 1
    [ -z "$NOME_CARTELLA" ] && exit 1
    VAULT="$HOME/Documents/$NOME_CARTELLA"
fi
if [ -e "$VAULT" ] && [ -n "$(ls -A "$VAULT" 2>/dev/null)" ]; then
    avviso "La cartella $VAULT esiste già e non è vuota. Non ho toccato niente: riapri questo file e scegli un altro nome."
    exit 1
fi
case "$VAULT" in
    *"Mobile Documents"*|*iCloud*)
        avviso "Quella cartella è sincronizzata con iCloud, che rovina i salvataggi del vault. Scegline un'altra."
        exit 1 ;;
esac

# 3. Chi firma i salvataggi, se questo Mac non lo sa ancora.
NOME="${JARVIS_NOME:-$(git config --global user.name 2>/dev/null)}"
EMAIL="${JARVIS_EMAIL:-$(git config --global user.email 2>/dev/null)}"
if [ -z "$SILENZIOSO" ]; then
    [ -z "$NOME" ] && { NOME="$(chiedi "Il tuo nome e cognome?" "")" || exit 1; }
    [ -z "$EMAIL" ] && { EMAIL="$(chiedi "La tua email?" "")" || exit 1; }
    git config --global user.name "$NOME"
    git config --global user.email "$EMAIL"
fi

# 4. Il sistema dentro System/. Da una copia scaricata con git si porta dietro
#    storia e versioni; da uno ZIP si prova a scaricarlo da GitHub, e solo se
#    non si può si copia com'è.
mkdir -p "$VAULT" || { avviso "Non riesco a creare $VAULT."; exit 1; }
if [ -d "$QUI/.git" ]; then
    git clone -q "$QUI" "$VAULT/System" && git -C "$VAULT/System" remote set-url origin "$REPO_URL"
elif GIT_TERMINAL_PROMPT=0 git clone -q "$REPO_URL" "$VAULT/System" 2>/dev/null; then
    :
else
    rsync -a --exclude ".DS_Store" "$QUI/" "$VAULT/System/"
    echo "Copiato senza collegamento a GitHub: gli aggiornamenti li collegherà l'agente."
fi
[ -f "$VAULT/System/scripts/install_vault.py" ] || { avviso "La copia del sistema non è riuscita. Non ho installato niente."; exit 1; }

# 5. L'installatore vero, poi il nome del proprietario nella configurazione.
cd "$VAULT" || exit 1
python3 System/scripts/install_vault.py || { avviso "L'installazione si è fermata con un errore. Apri la cartella in Claude Code e chiedi all'agente di guardare."; exit 1; }
python3 - "$NOME" <<'PY'
import json, sys
from pathlib import Path
cfg = Path("vault.config.json")
data = json.loads(cfg.read_text(encoding="utf-8"))
data["owner_name"] = sys.argv[1]
cfg.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
PY

avviso "Jarvis è installato in $VAULT. Ora: apri la cartella in Obsidian, aprila anche in VS Code, avvia Claude Code, rispondi sì alla domanda sulla fiducia e scrivi /onboard."
exit 0
