#!/bin/bash
# Installa Jarvis su un Mac. Si apre con un doppio clic; la prima volta con
# clic destro, Apri, perché il file viene da internet.
#
# Qui si controlla solo che git e Python ci siano: il resto lo fa
# scripts/installa_jarvis.py, uguale su ogni sistema.

cd "$(dirname "$0")" || exit 1

if ! xcode-select -p >/dev/null 2>&1; then
    xcode-select --install >/dev/null 2>&1
    echo "Mancano git e Python, che arrivano con gli strumenti di Apple."
    echo "Si è aperta una finestra per installarli: premi Installa, aspetta che finisca, poi riapri questo file."
    [ -t 0 ] && read -r -p "Premi Invio per chiudere." _
    exit 1
fi

python3 scripts/installa_jarvis.py
esito=$?
[ -t 0 ] && read -r -p "Premi Invio per chiudere." _
exit $esito
