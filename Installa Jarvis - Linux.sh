#!/usr/bin/env bash
# Installa Jarvis su Linux. Da un terminale aperto in questa cartella:
#     bash "Installa Jarvis - Linux.sh"
#
# Qui si controlla solo che git e Python ci siano, installandoli se mancano: il
# resto lo fa scripts/installa_jarvis.py, uguale su ogni sistema.

cd "$(dirname "$0")" || exit 1

manca=""
command -v git >/dev/null 2>&1 || manca="$manca git"
command -v python3 >/dev/null 2>&1 || manca="$manca python3"

if [ -n "$manca" ]; then
    if command -v apt-get >/dev/null 2>&1; then installa="sudo apt-get install -y$manca"
    elif command -v dnf >/dev/null 2>&1; then installa="sudo dnf install -y$manca"
    elif command -v zypper >/dev/null 2>&1; then installa="sudo zypper install -y$manca"
    elif command -v pacman >/dev/null 2>&1; then installa="sudo pacman -S --noconfirm${manca/python3/python}"
    else
        echo "Mancano:$manca. Installali con il gestore dei pacchetti del tuo sistema, poi rilancia questo file."
        exit 1
    fi
    echo "Mancano:$manca. Li installo con: $installa"
    echo "Ti verrà chiesta la password del computer."
    $installa || { echo "Installazione non riuscita."; exit 1; }
fi

python3 scripts/installa_jarvis.py
esito=$?
[ -t 0 ] && read -r -p "Premi Invio per chiudere." _
exit $esito
