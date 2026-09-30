#!/usr/bin/env python3
"""Installa Jarvis su questo computer: Mac, Windows o Linux.

Lo lanciano i tre file "Installa Jarvis" in cima al repository, dopo aver
controllato che git e Python ci siano. Da qui in poi i passaggi sono uguali su
ogni sistema: chiede nome della cartella, nome ed email, mette il sistema dentro
System/, esegue install_vault.py e scrive il nome del proprietario nella
configurazione.

Per le prove automatiche, senza domande: JARVIS_CARTELLA (percorso completo del
vault da creare), JARVIS_NOME e JARVIS_EMAIL.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO_URL = "https://github.com/edoardop06/jarvis.git"
SORGENTE = Path(__file__).resolve().parent.parent

# Cartelle sincronizzate con il cloud: i loro conflitti rovinano i salvataggi.
SINCRONIZZATE = ("icloud", "mobile documents", "onedrive", "dropbox", "google drive", "googledrive")


def git(*args: str, env: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], capture_output=True, text=True, env=env)


def chiedi(domanda: str, proposta: str = "") -> str:
    suggerimento = f" [{proposta}]" if proposta else ""
    return input(f"{domanda}{suggerimento}: ").strip() or proposta


def cartella_base() -> Path:
    home = Path.home()
    # Su Windows Documenti sta spesso dentro OneDrive, la cartella utente no.
    if os.name == "nt":
        return home
    documenti = home / "Documents"
    return documenti if documenti.is_dir() else home


def main() -> int:
    silenzioso = "JARVIS_CARTELLA" in os.environ
    print("Installa Jarvis\n")

    # 1. Dove mettere il vault.
    if silenzioso:
        vault = Path(os.environ["JARVIS_CARTELLA"])
    else:
        base = cartella_base()
        vault = base / chiedi(f"Come vuoi chiamare la cartella di Jarvis? Verrà creata in {base}", "Jarvis")
    vault = vault.expanduser().resolve()

    if any(s in str(vault).lower() for s in SINCRONIZZATE):
        print(f"\n{vault} è sincronizzata con il cloud, che rovina i salvataggi del vault. Scegli un'altra cartella.")
        return 1
    if vault.exists() and any(vault.iterdir()):
        print(f"\nLa cartella {vault} esiste già e non è vuota. Non ho toccato niente: riprova con un altro nome.")
        return 1

    # 2. Chi firma i salvataggi, se questo computer non lo sa ancora.
    nome = os.environ.get("JARVIS_NOME") or git("config", "--global", "user.name").stdout.strip()
    email = os.environ.get("JARVIS_EMAIL") or git("config", "--global", "user.email").stdout.strip()
    if not silenzioso:
        while not nome:
            nome = chiedi("Il tuo nome e cognome")
        while not email:
            email = chiedi("La tua email")
        git("config", "--global", "user.name", nome)
        git("config", "--global", "user.email", email)

    # 3. Il sistema dentro System/. Da una copia scaricata con git si porta dietro
    #    storia e versioni; da uno ZIP si prova a scaricarlo da GitHub, e solo se
    #    non si può si copia com'è.
    vault.mkdir(parents=True, exist_ok=True)
    system = vault / "System"
    if (SORGENTE / ".git").exists() and git("clone", "-q", str(SORGENTE), str(system)).returncode == 0:
        git("-C", str(system), "remote", "set-url", "origin", REPO_URL)
    else:
        shutil.rmtree(system, ignore_errors=True)
        senza_finestre = dict(os.environ, GIT_TERMINAL_PROMPT="0", GCM_INTERACTIVE="never")
        if git("clone", "-q", REPO_URL, str(system), env=senza_finestre).returncode != 0:
            shutil.rmtree(system, ignore_errors=True)
            shutil.copytree(SORGENTE, system, ignore=shutil.ignore_patterns(".DS_Store", "__pycache__"))
            print("Sistema copiato senza collegamento a GitHub: gli aggiornamenti li collegherà l'agente.")
    if not (system / "scripts" / "install_vault.py").exists():
        print("\nLa copia del sistema non è riuscita. Non ho installato niente.")
        return 1

    # 4. L'installatore vero, poi il nome del proprietario nella configurazione.
    if subprocess.run([sys.executable, str(system / "scripts" / "install_vault.py")], cwd=vault).returncode != 0:
        print("\nL'installazione si è fermata con un errore. Apri la cartella in Claude Code e chiedi all'agente di guardare.")
        return 1
    cfg = vault / "vault.config.json"
    dati = json.loads(cfg.read_text(encoding="utf-8"))
    dati["owner_name"] = nome
    cfg.write_text(json.dumps(dati, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"\nJarvis è installato in {vault}")
    print("Ora: apri la cartella in Obsidian, aprila anche in VS Code, avvia Claude Code,")
    print("rispondi sì alla domanda sulla fiducia e scrivi /onboard.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
