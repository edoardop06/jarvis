#!/usr/bin/env python3
"""Il banco di prova di Jarvis: prova una cosa finche funziona, e tiene il conto.

Perche esiste. Quando si sta facendo funzionare qualcosa, l'agente prova,
cambia, riprova. Senza un posto dove segnare cosa e stato provato succedono
sempre le stesse tre cose: al settimo tentativo si rifa il secondo, non si sa
piu se si sta migliorando o girando a vuoto, e alla fine della sessione tutto
quello che si e imparato sparisce insieme alla chat.

Cosa fa. Tiene una nota per ogni cosa che si sta facendo funzionare, con
l'obiettivo scritto, il comando che dice se funziona, e la tabella di tutti i
tentativi. Il comando lo esegue lui e ne registra l'esito, cosi "funziona" e un
fatto misurato e non un'opinione dell'agente.

Tiene o butta. Se il banco dichiara quali file sono in gioco, prima di ogni
tentativo ne conserva una copia. Se il tentativo peggiora la misura o rompe
tutto, rimette i file com'erano. E la meccanica che rende il provare gratis:
l'agente puo osare, perche un tentativo sbagliato non lascia danni.

Cosa non fa. Non decide quando fermarsi. Dice quanti tentativi sono passati
dall'ultimo miglioramento, che e il numero che serve per decidere, ma la
decisione sta nella funzione che lo usa.

Solo libreria standard.

Comandi:
  apri NOTA --obiettivo "..." --misura "COMANDO"   prepara un banco di prova
  prova NOTA --cambio "cosa ho cambiato"           misura, e tiene o butta
  stato NOTA                                       come sta andando
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import date

VAULT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Le copie di sicurezza stanno fuori dalle note: sono stato della macchina, non
# conoscenza, e logs/ e gia escluso dai salvataggi.
ISTANTANEE = os.path.join(VAULT, "logs", "banchi")

TESTATA = "| # | Data | Cosa e stato cambiato | Esito | Misura | Tenuto |"

MODELLO = """---
id: banco-{slug}
type: banco
status: active
domain: {dominio}
updated: {oggi}
direzione: {direzione}
file: {file}
summary: "Banco di prova: {obiettivo_breve} Ogni tentativo con cosa e stato cambiato e cosa e successo, cosi non si riprova due volte la stessa cosa."
---

# Banco di prova: {nome}

**Obiettivo.** {obiettivo}

**Funziona quando.** {soglia}

**Come si misura.** Questo comando viene eseguito a ogni tentativo, sempre
uguale e con lo stesso tempo massimo, altrimenti i tentativi non sono
confrontabili. Se finisce bene la cosa funziona, e l'ultima riga che stampa
finisce nella colonna Misura. Fra due misure vince la {parola_direzione}.

```bash
{misura}
```

---

## Tentativi

Questa tabella si scrive solo aggiungendo in fondo, con
`System/scripts/banco.py prova`. I tentativi falliti valgono quanto quelli
riusciti: sono la ragione per cui nessuno rifara quella strada. La colonna
Tenuto dice se il cambiamento e rimasto o se i file sono stati rimessi
com'erano.

{testata}
|---|---|---|---|---|---|

---

## Cosa si e imparato

Da riempire quando il banco si chiude, in due o tre righe. E la parte che
sopravvive: la tabella dice cosa e stato fatto, questa dice cosa vale la pena
ricordare.
"""


def percorso(dato):
    p = dato if dato.endswith(".md") else dato + ".md"
    if not os.path.isabs(p):
        p = os.path.join(VAULT, p)
    return p


def cella(testo, quanto=90):
    """Niente barre verticali e niente a capo, o la tabella si rompe."""
    testo = " ".join(str(testo).split()).replace("|", "/")
    return testo[:quanto] if len(testo) <= quanto else testo[:quanto - 1] + "…"


def frontmatter(testo):
    dati = {}
    righe = testo.splitlines()
    if not righe or righe[0].strip() != "---":
        return dati
    for riga in righe[1:]:
        if riga.strip() == "---":
            break
        m = re.match(r"^([A-Za-z_]+):\s*(.*)$", riga)
        if m:
            dati[m.group(1)] = m.group(2).strip().strip('"')
    return dati


def file_in_gioco(fm):
    grezzi = [x.strip() for x in fm.get("file", "").split(";") if x.strip()]
    fuori = []
    for g in grezzi:
        p = g if os.path.isabs(g) else os.path.join(VAULT, g)
        fuori.append(p)
    return fuori


def cartella_istantanea(percorso_nota):
    slug = re.sub(r"[^a-z0-9]+", "-", os.path.basename(percorso_nota)[:-3].lower()).strip("-")
    return os.path.join(ISTANTANEE, slug)


def salva_istantanea(percorso_nota, file):
    d = cartella_istantanea(percorso_nota)
    os.makedirs(d, exist_ok=True)
    for i, f in enumerate(file):
        if os.path.exists(f):
            shutil.copy2(f, os.path.join(d, f"{i}-" + os.path.basename(f)))


def rimetti_istantanea(percorso_nota, file):
    d = cartella_istantanea(percorso_nota)
    rimessi = []
    for i, f in enumerate(file):
        copia = os.path.join(d, f"{i}-" + os.path.basename(f))
        if os.path.exists(copia):
            shutil.copy2(copia, f)
            rimessi.append(os.path.basename(f))
    return rimessi


def leggi_misura(testo):
    m = re.search(r"```bash\n(.*?)\n```", testo, re.DOTALL)
    return m.group(1).strip() if m else None


def righe_tentativi(testo):
    if TESTATA not in testo:
        return None, None
    righe = testo[testo.index(TESTATA):].splitlines()
    fuori = []
    for i, riga in enumerate(righe[2:], start=2):
        if not riga.startswith("|"):
            break
        fuori.append(riga)
    else:
        i = len(righe)
    fine = testo.index(TESTATA) + sum(len(r) + 1 for r in righe[:i])
    return fuori, fine


def numero(cella_misura):
    m = re.search(r"-?\d+[.,]?\d*", cella_misura.replace(",", "."))
    return float(m.group(0)) if m else None


def cmd_apri(args):
    p = percorso(args.nota)
    if os.path.exists(p):
        print(f"Esiste gia: {os.path.relpath(p, VAULT)}. Usa 'prova' per aggiungere un tentativo.")
        sys.exit(1)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    nome = os.path.basename(p)[:-3]
    slug = re.sub(r"[^a-z0-9]+", "-", nome.lower()).strip("-")
    breve = args.obiettivo.strip()
    if not breve.endswith("."):
        breve += "."
    with open(p, "w", encoding="utf-8") as f:
        f.write(MODELLO.format(
            slug=slug, nome=nome, oggi=date.today().isoformat(),
            dominio=args.dominio, obiettivo=args.obiettivo,
            obiettivo_breve=cella(breve, 120),
            soglia=args.soglia or "Il comando qui sotto finisce bene.",
            misura=args.misura, testata=TESTATA,
            direzione=args.direzione, file=args.tocca,
            parola_direzione="piu bassa" if args.direzione == "minore" else "piu alta"))
    print(f"Banco aperto: {os.path.relpath(p, VAULT)}")
    file = file_in_gioco({"file": args.tocca})
    if file:
        salva_istantanea(p, file)
        print(f"Conservata una copia di {len(file)} file. Un tentativo che "
              f"peggiora le cose viene annullato da solo.")
    else:
        print("Nessun file dichiarato con --tocca: i tentativi non verranno "
              "annullati da soli. Va bene solo se stai cambiando cose fuori dai file.")


def cmd_prova(args):
    p = percorso(args.nota)
    if not os.path.exists(p):
        print(f"Non esiste: {os.path.relpath(p, VAULT)}. Aprilo prima con 'apri'.")
        sys.exit(1)
    testo = open(p, encoding="utf-8").read()
    misura = leggi_misura(testo)
    if not misura:
        print("Questo banco non dice come si misura. Manca il blocco di comando.")
        sys.exit(1)
    righe, fine = righe_tentativi(testo)
    if righe is None:
        print("La tabella dei tentativi non c'e piu.")
        sys.exit(1)

    n = len(righe) + 1
    print(f"Tentativo {n}, misura in corso:\n  {misura}\n")
    inizio = time.time()
    try:
        esito = subprocess.run(misura, shell=True, cwd=VAULT, timeout=args.timeout,
                               capture_output=True, text=True)
        durata = time.time() - inizio
        uscita = (esito.stdout or "") + (esito.stderr or "")
        righe_uscita = [r for r in uscita.splitlines() if r.strip()]
        ultima = righe_uscita[-1] if righe_uscita else ""
        funziona = esito.returncode == 0
    except subprocess.TimeoutExpired:
        durata = time.time() - inizio
        ultima = f"nessuna risposta entro {args.timeout} secondi"
        funziona = False

    fm = frontmatter(testo)
    file = file_in_gioco(fm)
    verso = fm.get("direzione", "minore")
    valore = numero(ultima)

    # Il metro di paragone e il migliore fra i tentativi tenuti finora.
    precedente = None
    for r in righe:
        celle = [c.strip() for c in r.strip().strip("|").split("|")]
        if len(celle) >= 6 and celle[3] == "funziona" and celle[5] == "tenuto":
            v = numero(celle[4])
            if v is None:
                continue
            if precedente is None or (v < precedente if verso == "minore" else v > precedente):
                precedente = v

    if not funziona:
        tenuto = False
        perche = "non funziona"
    elif valore is None or precedente is None:
        tenuto = True
        perche = "funziona, ed e il primo termine di paragone"
    elif (valore < precedente) if verso == "minore" else (valore > precedente):
        tenuto = True
        perche = f"migliora: {valore:g} contro {precedente:g}"
    else:
        tenuto = False
        perche = f"non migliora: {valore:g} contro {precedente:g}"

    rimessi = []
    if file:
        if tenuto:
            salva_istantanea(p, file)
        else:
            rimessi = rimetti_istantanea(p, file)

    riga = (f"| {n} | {date.today().isoformat()} | {cella(args.cambio)} "
            f"| {'funziona' if funziona else 'no'} | {cella(ultima, 60)} ({durata:.1f}s) "
            f"| {'tenuto' if tenuto else 'annullato'} |\n")
    testo = re.sub(r"(?m)^updated:.*$", f"updated: {date.today().isoformat()}", testo, count=1)
    _, fine = righe_tentativi(testo)
    testo = testo[:fine] + riga + testo[fine:]
    with open(p, "w", encoding="utf-8") as f:
        f.write(testo)

    print("FUNZIONA" if funziona else "NON FUNZIONA ANCORA")
    if ultima:
        print(f"  {ultima[:200]}")
    print(f"  {durata:.1f} secondi. Registrato come tentativo {n}.")
    print(f"  {'TENUTO' if tenuto else 'ANNULLATO'}: {perche}.")
    if rimessi:
        print(f"  Rimessi com'erano: {', '.join(rimessi)}.")
    elif not tenuto and not file:
        print("  Il banco non dichiara file, quindi il cambiamento resta dov'e: "
              "annullalo tu.")
    if not funziona:
        sys.exit(2)


def cmd_stato(args):
    p = percorso(args.nota)
    testo = open(p, encoding="utf-8").read()
    righe, _ = righe_tentativi(testo)
    if not righe:
        print("Nessun tentativo ancora.")
        return
    dati = []
    for r in righe:
        celle = [c.strip() for c in r.strip().strip("|").split("|")]
        while len(celle) < 5:
            celle.append("")
        dati.append(celle)

    verso = frontmatter(testo).get("direzione", "minore")
    riusciti = [d for d in dati if d[3] == "funziona"]
    annullati = [d for d in dati if len(d) >= 6 and d[5] == "annullato"]
    print(f"Tentativi: {len(dati)}. Riusciti: {len(riusciti)}. Annullati: {len(annullati)}.")
    print(f"Ultimo: {dati[-1][1]}, {dati[-1][2]} -> {dati[-1][3]}")
    if not riusciti:
        print("\nNon ha mai funzionato. Il conto dei tentativi a vuoto e "
              f"{len(dati)}.")
        return
    print(f"Ha funzionato la prima volta al tentativo {riusciti[0][0]}.")

    # Fase efficienza: fra i tentativi riusciti, il numero nella misura conta.
    valori = [(int(d[0]), numero(d[4])) for d in riusciti if numero(d[4]) is not None]
    if len(valori) < 2:
        print("Non c'e ancora un numero da confrontare fra un tentativo e l'altro.")
        return
    migliore, indice_migliore = valori[0][1], valori[0][0]
    for n, v in valori[1:]:
        if (v < migliore) if verso == "minore" else (v > migliore):
            migliore, indice_migliore = v, n
    # Contano tutti i tentativi dopo il migliore, non solo quelli riusciti:
    # anche una prova che rompe tutto e tempo passato senza migliorare.
    dopo = len([d for d in dati if int(d[0]) > indice_migliore])
    print(f"Misura migliore: {migliore:g}, al tentativo {indice_migliore}.")
    print(f"Tentativi dopo l'ultimo miglioramento: {dopo}.")
    if dopo >= 3:
        print("\nTre tentativi senza migliorare. Qui si smette di provare e si "
              "porta la scelta al proprietario.")


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="comando", required=True)

    c = sub.add_parser("apri", help="prepara un banco di prova")
    c.add_argument("nota", help="percorso della nota, dentro la cartella del progetto")
    c.add_argument("--obiettivo", required=True)
    c.add_argument("--misura", required=True, help="il comando che dice se funziona")
    c.add_argument("--soglia", default="", help="quando si considera riuscito")
    c.add_argument("--dominio", default="ai_os")
    c.add_argument("--direzione", choices=["minore", "maggiore"], default="minore",
                   help="se fra due misure vince la piu bassa o la piu alta")
    c.add_argument("--tocca", default="",
                   help="i file che i tentativi cambiano, separati da punto e virgola. "
                        "Senza questi, un tentativo sbagliato non si annulla da solo")
    c.set_defaults(func=cmd_apri)

    c = sub.add_parser("prova", help="esegue la misura e registra il tentativo")
    c.add_argument("nota")
    c.add_argument("--cambio", required=True, help="cosa e stato cambiato stavolta")
    c.add_argument("--timeout", type=int, default=300,
                   help="il tempo massimo, uguale per tutti i tentativi, "
                        "altrimenti le misure non sono confrontabili")
    c.set_defaults(func=cmd_prova)

    c = sub.add_parser("stato", help="come sta andando")
    c.add_argument("nota")
    c.set_defaults(func=cmd_stato)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
