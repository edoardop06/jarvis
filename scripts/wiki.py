#!/usr/bin/env python3
"""Il motore del wiki di Jarvis: ricerca, collegamenti, salute della conoscenza.

Perche esiste. Il vault e gia un wiki (Sources sono le fonti grezze, Atlas sono
le pagine, gli Index sono il catalogo), ma finora nessuno faceva la parte
noiosa: cercare dentro tutte le note senza aprirle una per una, sapere chi
punta a chi, accorgersi che una pagina e rimasta indietro o che un concetto
ricorre in cinque note senza avere una pagina sua.

Divisione del lavoro. Questo script fa solo cio che e meccanico e verificabile:
conta, cerca, elenca, confronta date. Non giudica. Le contraddizioni fra due
pagine, se una fonte vale, se un concetto merita una nota: quello lo decide
l'agente leggendo le pagine che questo script gli mette davanti.

Solo libreria standard, nessuna installazione. La ricerca e BM25 calcolato al
volo: su un vault di qualche centinaio di note e istantaneo e non ha bisogno di
un indice da tenere aggiornato, che sarebbe l'ennesima cosa che si rompe.

Sta in System/ perche serve a ogni vault. Si lancia dalla cartella del vault:
    python3 System/scripts/wiki.py cerca "domanda"

Comandi:
  cerca "domanda"        ricerca a punteggio su tutto il vault
  collegamenti NOTA      chi punta a questa nota e a chi punta lei
  hub                    le pagine piu collegate, il centro del wiki
  orfane                 pagine che nessuno cita
  concetti               termini ricorrenti senza una pagina propria
  mancanti               note che si nominano a vicenda senza collegarsi
  vecchie                pagine ferme da troppo tempo
  provenienza            pagine Atlas senza una fonte dichiarata
  fonti                  fonti grezze non ancora lavorate
  salute                 tutti i controlli sopra, in un rapporto solo
  domande                le domande aperte, cioe cosa il vault sa di non sapere
  domanda "TITOLO"       aggiunge una domanda aperta
  log TIPO "TITOLO"      aggiunge una riga al registro della conoscenza
  ultimi [N]             le ultime N righe del registro
"""

import argparse
import json
import math
import os
import re
import string
import sys
from collections import Counter, defaultdict
from datetime import date, datetime

VAULT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REGISTRO = os.path.join(VAULT, "Ideaverse/Atlas/Atlas Log.md")

IGNORATE = {".git", ".obsidian", "node_modules", "__pycache__", ".claude"}
# System/template non sono note vive, sono i semi per un vault nuovo.
PERCORSI_ESCLUSI = ("System/template/",)

# Il livello conoscenza: le pagine che il wiki possiede davvero. Inbox e
# Archive restano fuori perche il primo e materiale non ancora letto e il
# secondo e roba messa via di proposito.
CONOSCENZA_ESCLUSE = ("Ideaverse/Inbox/", "Ideaverse/Archive/")

STOPWORD = set("""
il lo la i gli le un uno una del dello della dei degli delle al allo alla ai
agli alle dal dallo dalla dai dagli dalle nel nello nella nei negli nelle sul
sullo sulla sui sugli sulle col coi di a da in con su per tra fra e ed o od ma
se anche come che chi cui non piu meno molto poco tutto tutti tutte ogni
questo questa questi queste quello quella quelli quelle essere sono era erano
serve servono senza quanto quanta quanti quante dentro fuori sopra sotto oltre
verso circa dire detto dice vuole vuoi deve devono puo possono stesso stessa
bene meglio peggio nuovo nuova prima dopo mentre finche cioe ovvero eccetera
stato stata stati state ha hanno avere aveva avevano fare fatto fa si ci vi ne
mi ti gli le loro suo sua suoi sue mio mia miei mie quando dove perche come
cosa qual quale quali gia ancora sempre mai solo anche dopo prima poi quindi
allora invece pero perche
the of and to in a is are was were be been it its this that these those for on
with as by from at or an if not but so than then there here what which who
whom whose when where why how all any each other some such no nor only own
same too very can will just should now do does did doing have has had having
""".split())

# Parole troppo generiche per suggerire una pagina nuova, anche se ricorrono.
RUMORE = set("""
nota note pagina pagine file cartella cartelle vault jarvis agente agenti
sistema lavoro cosa cose modo parte volta esempio caso punto
""".split())


def _nome_proprietario():
    """Il nome del proprietario torna in ogni nota: non e un concetto da pagina."""
    try:
        with open(os.path.join(VAULT, "vault.config.json"), encoding="utf-8") as f:
            return set(str(json.load(f).get("owner_name", "")).lower().split())
    except (OSError, ValueError, AttributeError):
        return set()


RUMORE |= _nome_proprietario()


# ---------------------------------------------------------------- lettura


class Nota:
    def __init__(self, percorso):
        self.percorso = percorso
        self.rel = os.path.relpath(percorso, VAULT).replace(os.sep, "/")
        self.chiave = self.rel[:-3]                      # senza .md
        self.titolo = os.path.basename(self.chiave)
        try:
            self.testo = open(percorso, encoding="utf-8").read()
        except OSError:
            self.testo = ""
        self.fm = _frontmatter(self.testo)

    @property
    def conoscenza(self):
        """Una pagina del wiki vero e proprio, non un indice ne un file di servizio."""
        if not self.rel.startswith("Ideaverse/"):
            return False
        if self.rel.startswith(CONOSCENZA_ESCLUSE):
            return False
        if self.titolo.endswith("Index") or self.titolo == "README":
            return False
        return True

    @property
    def sommario(self):
        return self.fm.get("summary", "")


def _frontmatter(testo):
    dati = {}
    righe = testo.splitlines()
    if not righe or righe[0].strip() != "---":
        return dati
    for riga in righe[1:]:
        if riga.strip() == "---":
            break
        m = re.match(r"^([A-Za-z_]+):\s*(.*)$", riga)
        if m:
            dati[m.group(1)] = m.group(2).strip().strip('"').strip("'")
    return dati


def carica():
    note = []
    for radice, dirs, files in os.walk(VAULT):
        dirs[:] = sorted(d for d in dirs if d not in IGNORATE)
        for nome in sorted(files):
            if not nome.endswith(".md"):
                continue
            p = os.path.join(radice, nome)
            rel = os.path.relpath(p, VAULT).replace(os.sep, "/")
            if rel.startswith(PERCORSI_ESCLUSI):
                continue
            note.append(Nota(p))
    return note


CODICE = re.compile(r"```.*?```", re.DOTALL)
FRONTMATTER = re.compile(r"\A---\n.*?\n---\n", re.DOTALL)
ACCENTI = str.maketrans("àèéìòùÀÈÉÌÒÙ", "aeeiouAEEIOU")
LINK = re.compile(r"\[\[([^|\]\[]+)(?:\|[^\]]*)?\]\]")


def senza_codice(testo):
    return CODICE.sub(" ", testo)


def corpo(nota):
    """Il testo leggibile: senza blocco impostazioni in cima e senza codice."""
    return CODICE.sub(" ", FRONTMATTER.sub("", nota.testo))


def piatta(parola):
    """Senza accenti, per confrontare con le stopword scritte senza."""
    return parola.translate(ACCENTI)


def parole(testo):
    return [p for p in re.findall(r"[0-9a-zA-ZàèéìòùÀÈÉÌÒÙ']{3,}", testo.lower())
            if p not in STOPWORD and piatta(p) not in STOPWORD]


def link_uscenti(nota):
    fuori = []
    for m in LINK.finditer(senza_codice(nota.testo)):
        fuori.append(m.group(1).strip().rstrip("\\").lstrip("/"))
    return fuori


def grafo(note):
    """entranti[chiave] = insieme delle note che la citano."""
    chiavi = {n.chiave for n in note}
    entranti = defaultdict(set)
    uscenti = defaultdict(set)
    for n in note:
        for t in link_uscenti(n):
            if t in chiavi and t != n.chiave:
                entranti[t].add(n.chiave)
                uscenti[n.chiave].add(t)
    return entranti, uscenti


def trova_nota(note, testo):
    """Accetta il percorso completo, il nome del file, o un pezzo di nome."""
    testo = testo.strip().rstrip("/")
    if testo.endswith(".md"):
        testo = testo[:-3]
    esatte = [n for n in note if n.chiave == testo]
    if esatte:
        return esatte[0]
    per_titolo = [n for n in note if n.titolo.lower() == testo.lower()]
    if len(per_titolo) == 1:
        return per_titolo[0]
    parziali = [n for n in note if testo.lower() in n.titolo.lower()]
    if len(parziali) == 1:
        return parziali[0]
    if not parziali:
        print(f"Nessuna nota trovata per '{testo}'.")
        return None
    print(f"Piu di una nota corrisponde a '{testo}':")
    for n in parziali[:12]:
        print("  " + n.chiave)
    return None


# ---------------------------------------------------------------- ricerca


def bm25(note, domanda, quante, dentro=None, k1=1.5, b=0.75):
    corpus = [n for n in note if not dentro or n.rel.startswith(dentro)]
    if not corpus:
        return []
    termini = parole(domanda)
    if not termini:
        return []

    documenti = []
    for n in corpus:
        tf = Counter(parole(senza_codice(n.testo)))
        documenti.append((n, tf, sum(tf.values()) or 1))
    media = sum(d[2] for d in documenti) / len(documenti)

    df = Counter()
    for _, tf, _ in documenti:
        for t in set(termini):
            if tf.get(t):
                df[t] += 1

    frase = domanda.strip().lower()
    risultati = []
    for n, tf, lung in documenti:
        punteggio = 0.0
        trovati = 0
        for t in set(termini):
            if not tf.get(t):
                continue
            trovati += 1
            idf = math.log(1 + (len(documenti) - df[t] + 0.5) / (df[t] + 0.5))
            f = tf[t]
            punteggio += idf * (f * (k1 + 1)) / (f + k1 * (1 - b + b * lung / media))
            # Il titolo e il sommario valgono piu del corpo: sono cio che
            # l'autore ha deciso che la nota e.
            if t in n.titolo.lower():
                punteggio += 2.0 * idf
            if t in n.sommario.lower():
                punteggio += 1.0 * idf
        if not trovati:
            continue
        # Chi contiene la domanda intera vince su chi ha solo le parole sparse.
        if len(frase) > 6 and frase in senza_codice(n.testo).lower():
            punteggio += 4.0
        # Copertura: meglio una nota che tocca tutti i termini.
        punteggio *= (0.5 + 0.5 * trovati / len(set(termini)))
        risultati.append((punteggio, n))
    risultati.sort(key=lambda r: (-r[0], r[1].rel))
    return risultati[:quante]


def righe_rilevanti(nota, domanda, quante=2):
    termini = set(parole(domanda))
    fuori = []
    for riga in corpo(nota).splitlines():
        pulita = riga.strip()
        if len(pulita) < 25 or pulita.startswith(("|", "---", "#")):
            continue
        if termini & set(parole(pulita)):
            fuori.append(pulita[:180])
        if len(fuori) >= quante:
            break
    return fuori


def cmd_cerca(args):
    note = carica()
    esiti = bm25(note, args.domanda, args.n, args.dentro)
    if not esiti:
        print("Nessuna nota contiene questi termini.")
        return
    print(f"{len(esiti)} note per: {args.domanda}\n")
    for i, (punteggio, n) in enumerate(esiti, 1):
        print(f"{i}. {n.chiave}   [{punteggio:.1f}]")
        if n.sommario:
            print(f"   {n.sommario[:200]}")
        for riga in righe_rilevanti(n, args.domanda):
            print(f"   > {riga}")
        print()


# ---------------------------------------------------------------- grafo


def cmd_collegamenti(args):
    note = carica()
    n = trova_nota(note, args.nota)
    if not n:
        sys.exit(1)
    chiavi = {x.chiave for x in note}
    entranti, _ = grafo(note)
    print(n.chiave)
    if n.sommario:
        print(n.sommario)
    fuori = link_uscenti(n)
    print(f"\nPunta a ({len([t for t in fuori if t in chiavi])}):")
    for t in sorted(set(t for t in fuori if t in chiavi)):
        print("  -> " + t)
    rotti = sorted(set(t for t in fuori if "/" in t and t not in chiavi))
    for t in rotti:
        print("  -> " + t + "   ROTTO, la nota non esiste")
    dentro = sorted(entranti.get(n.chiave, ()))
    print(f"\nCitata da ({len(dentro)}):")
    for t in dentro:
        print("  <- " + t)
    if not dentro:
        print("  nessuno. E una pagina orfana: il wiki non ci arriva navigando.")


def cmd_hub(args):
    note = carica()
    entranti, _ = grafo(note)
    classifica = sorted(((len(v), k) for k, v in entranti.items()), reverse=True)
    print("Le pagine piu citate del vault:\n")
    for quanti, chiave in classifica[:args.n]:
        print(f"  {quanti:3d}  {chiave}")


def orfane(note):
    entranti, _ = grafo(note)
    return [n for n in note if n.conoscenza and not entranti.get(n.chiave)]


def cmd_orfane(args):
    fuori = orfane(carica())
    if not fuori:
        print("Nessuna pagina orfana.")
        return
    print(f"{len(fuori)} pagine che nessuno cita:\n")
    for n in fuori:
        print("  " + n.chiave)
        if n.sommario:
            print(f"      {n.sommario[:140]}")


# ------------------------------------------------------- concetti mancanti


def cmd_concetti(args):
    """Nomi propri e termini tecnici che ricorrono e non hanno una pagina loro.

    Il filtro che conta e la maiuscola in mezzo alla frase. Una lista di parole
    da ignorare non finisce mai: dopo "progetto" e "qualsiasi" arriva sempre la
    successiva. Ma un termine che qualcuno scrive maiuscolo mentre sta gia
    scrivendo, o tutto maiuscolo, e quasi sempre un nome: una persona, un
    prodotto, un'azienda, una sigla. Quelli meritano una pagina, "qualsiasi" no.
    """
    note = [n for n in carica() if n.conoscenza]
    titoli = {n.titolo.lower() for n in note}
    presenze = defaultdict(set)
    totali = Counter()
    prove = Counter()          # volte in cui il termine sembra un nome proprio
    inizio_frase = set(".!?:;#|>-*") | set(string.digits)
    for n in note:
        testo = LINK.sub(" ", corpo(n))       # cio che e gia collegato non serve
        for m in re.finditer(r"[0-9a-zA-ZàèéìòùÀÈÉÌÒÙ']{4,}", testo):
            grezza = m.group(0)
            p = grezza.lower()
            if p.isdigit() or p in titoli:
                continue
            if p in STOPWORD or piatta(p) in STOPWORD or p in RUMORE:
                continue
            presenze[p].add(n.chiave)
            totali[p] += 1
            precedente = testo[:m.start()].rstrip()
            capoverso = (not precedente) or precedente[-1] in inizio_frase
            if grezza.isupper() or (grezza[0].isupper() and not capoverso):
                prove[p] += 1
    candidati = [(len(v), totali[p], p) for p, v in presenze.items()
                 if len(v) >= args.min and prove[p] >= 2]
    candidati.sort(reverse=True)
    if not candidati:
        print("Nessun nome ricorrente senza pagina propria.")
        return
    print("Nomi e sigle che tornano in piu pagine e non hanno una nota loro.")
    print("Ognuno e un candidato a diventare una pagina del wiki.\n")
    for quante, volte, p in candidati[:args.n]:
        dove = ", ".join(sorted(x.split("/")[-1] for x in presenze[p])[:4])
        print(f"  {p:<22} {quante} pagine, {volte} volte   ({dove})")


def collegamenti_mancanti(note):
    """Note che si nominano per esteso senza collegarsi. Il caso classico e una
    pagina scritta prima che l'altra esistesse."""
    pagine = [n for n in note if n.conoscenza and len(n.titolo) >= 5]
    fuori = []
    for n in note:
        if not n.rel.startswith("Ideaverse/") or n.rel.startswith(CONOSCENZA_ESCLUSE):
            continue
        gia = set(link_uscenti(n))
        senza_link = LINK.sub(" ", corpo(n))
        for p in pagine:
            if p.chiave == n.chiave or p.chiave in gia:
                continue
            # Maiuscole comprese, di proposito. "montaggio" in mezzo a una frase
            # e una parola italiana, "Montaggio" e il nome di una nota.
            if re.search(r"\b" + re.escape(p.titolo) + r"\b", senza_link):
                fuori.append((n.chiave, p.chiave))
    return fuori


def cmd_mancanti(args):
    fuori = collegamenti_mancanti(carica())
    if not fuori:
        print("Nessun collegamento mancante evidente.")
        return
    print(f"{len(fuori)} punti dove una nota ne nomina un'altra senza collegarla:\n")
    for da, a in fuori[:args.n]:
        print(f"  {da}")
        print(f"      nomina {a}")


# ---------------------------------------------------------------- tempo


def cmd_vecchie(args):
    oggi = date.today()
    righe = []
    for n in carica():
        if not n.conoscenza:
            continue
        grezza = n.fm.get("updated", "")
        try:
            quando = datetime.strptime(grezza[:10], "%Y-%m-%d").date()
        except ValueError:
            righe.append((99999, n, "senza data"))
            continue
        giorni = (oggi - quando).days
        if giorni >= args.giorni:
            righe.append((giorni, n, grezza[:10]))
    righe.sort(reverse=True)
    if not righe:
        print(f"Nessuna pagina ferma da piu di {args.giorni} giorni.")
        return
    print(f"{len(righe)} pagine ferme da piu di {args.giorni} giorni:\n")
    for giorni, n, quando in righe:
        eta = "?" if giorni == 99999 else f"{giorni} giorni"
        print(f"  {eta:<12} {n.chiave}   ({quando})")


def senza_fonte(note):
    fuori = []
    for n in note:
        if not n.rel.startswith("Ideaverse/Atlas/") or not n.conoscenza:
            continue
        if n.rel == "Ideaverse/Atlas/Atlas Log.md":
            continue          # e il registro, elenca fonti, non le cita
        testo = corpo(n)
        # "Da dove viene" e il modo in cui il vault scrive davvero questa
        # sezione, in italiano. Senza riconoscerlo ogni pagina scritta bene
        # risultava senza fonte, e il controllo suonava falso allarme.
        ha_fonte = ("Ideaverse/Sources/" in testo
                    or "http://" in testo or "https://" in testo
                    or re.search(r"(?im)^#+\s*(fonti|fonte|source|da dove viene|provenienza)",
                                 testo))
        if not ha_fonte:
            fuori.append(n)
    return fuori


def cmd_provenienza(args):
    fuori = senza_fonte(carica())
    if not fuori:
        print("Ogni pagina Atlas dichiara da dove viene.")
        return
    print(f"{len(fuori)} pagine Atlas senza fonte dichiarata:\n")
    for n in fuori:
        print("  " + n.chiave)


def cmd_fonti(args):
    note = carica()
    fonti = [n for n in note
             if n.rel.startswith("Ideaverse/Sources/") and not n.titolo.endswith("Index")]
    inbox = [n for n in note if n.rel.startswith("Ideaverse/Inbox/") and n.titolo != "README"]
    grezze = [n for n in fonti if n.fm.get("status", "raw") != "processed"]
    print(f"Fonti in archivio: {len(fonti)}. Non ancora lavorate: {len(grezze)}.")
    for n in grezze:
        print("  " + n.chiave)
    altri = sorted(os.listdir(os.path.join(VAULT, "Ideaverse/Inbox")))
    altri = [a for a in altri if not a.startswith(".") and a != "README.md"]
    if altri:
        print(f"\nIn Inbox, in attesa di essere letti ({len(altri)}):")
        for a in altri:
            print("  " + a)
    elif inbox:
        print("\nInbox vuota.")


# ---------------------------------------------------------------- salute


def cmd_salute(args):
    note = carica()
    entranti, uscenti = grafo(note)
    pagine = [n for n in note if n.conoscenza]
    archi = sum(len(v) for v in uscenti.values())

    print("SALUTE DEL WIKI")
    print("=" * 62)
    print(f"Note nel vault: {len(note)}   di cui pagine di conoscenza: {len(pagine)}")
    print(f"Collegamenti fra note: {archi}")
    if pagine:
        ricevute = sum(len(entranti.get(n.chiave, ())) for n in pagine)
        print(f"Citazioni ricevute in media da una pagina di conoscenza: "
              f"{ricevute / len(pagine):.1f}")

    print("\nCENTRO DEL WIKI, le pagine piu citate")
    for quanti, chiave in sorted(((len(v), k) for k, v in entranti.items()), reverse=True)[:5]:
        print(f"  {quanti:3d}  {chiave}")

    o = orfane(note)
    print(f"\nPAGINE ORFANE, nessuno le cita ({len(o)})")
    for n in o[:15]:
        print("  " + n.chiave)

    s = senza_fonte(note)
    print(f"\nPAGINE SENZA FONTE DICHIARATA ({len(s)})")
    for n in s[:15]:
        print("  " + n.chiave)

    m = collegamenti_mancanti(note)
    print(f"\nCOLLEGAMENTI MANCANTI, si nominano senza collegarsi ({len(m)})")
    for da, a in m[:10]:
        print(f"  {da}  ->  {a}")

    print("\nPAGINE FERME DA PIU DI 60 GIORNI")
    oggi = date.today()
    vecchie = []
    for n in pagine:
        try:
            quando = datetime.strptime(n.fm.get("updated", "")[:10], "%Y-%m-%d").date()
        except ValueError:
            continue
        if (oggi - quando).days >= 60:
            vecchie.append(((oggi - quando).days, n.chiave))
    for giorni, chiave in sorted(vecchie, reverse=True)[:10]:
        print(f"  {giorni:4d} giorni  {chiave}")
    if not vecchie:
        print("  nessuna")

    print()
    cmd_fonti(args)
    print("\nDOMANDE APERTE")
    cmd_domande(args)

    print("\nNOMI SENZA PAGINA")
    args.min, args.n = 3, 12
    cmd_concetti(args)
    print("\n" + "=" * 62)
    print("Questo e il conteggio. Il giudizio no: contraddizioni fra pagine,")
    print("affermazioni superate e concetti che meritano davvero una nota si")
    print("decidono leggendo le pagine elencate qui sopra.")


# ------------------------------------------------------- domande aperte


INDICE_ATLAS = os.path.join(VAULT, "Ideaverse/Atlas/Atlas Index.md")
TESTATA_BACKLOG = "| Note title | Topic area | Source or trigger |"


def _righe_backlog(testo):
    """Le righe della tabella del backlog, senza testata ne separatore."""
    if TESTATA_BACKLOG not in testo:
        return None, None
    inizio = testo.index(TESTATA_BACKLOG)
    righe = testo[inizio:].splitlines()
    fuori = []
    for i, riga in enumerate(righe[2:], start=2):
        if not riga.startswith("|"):
            return fuori, inizio + sum(len(r) + 1 for r in righe[:i])
        fuori.append(riga)
    return fuori, len(testo)


def cmd_domande(args):
    """Cosa il vault sa di non sapere.

    Sta nel backlog dell'Atlas Index e non in un file nuovo, perche quella
    tabella esiste gia per questo: le pagine che varrebbe la pena avere e per
    cui manca il materiale. Una domanda aperta e esattamente quello.
    """
    if not os.path.exists(INDICE_ATLAS):
        print("Atlas Index non esiste.")
        return
    righe, _ = _righe_backlog(open(INDICE_ATLAS, encoding="utf-8").read())
    if righe is None:
        print("La tabella delle domande aperte non c'e piu dentro Atlas Index.")
        return
    if not righe:
        print("Nessuna domanda aperta. Il vault non ha lacune segnate.")
        return
    print(f"{len(righe)} domande aperte:\n")
    for riga in righe:
        celle = [c.strip() for c in riga.strip().strip("|").split("|")]
        while len(celle) < 3:
            celle.append("")
        print(f"  {celle[0]}")
        print(f"      area: {celle[1] or 'non detta'}")
        print(f"      perche: {celle[2] or 'non detto'}")


def cmd_domanda(args):
    testo = open(INDICE_ATLAS, encoding="utf-8").read()
    righe, fine = _righe_backlog(testo)
    if righe is None:
        print("La tabella delle domande aperte non c'e piu dentro Atlas Index.")
        sys.exit(1)
    for c in (args.titolo, args.area, args.perche):
        if "|" in c:
            print("Niente barre verticali dentro il testo: romperebbero la tabella.")
            sys.exit(1)
    riga = f"| {args.titolo} | {args.area} | {args.perche} |\n"
    testo = testo[:fine] + riga + testo[fine:]
    with open(INDICE_ATLAS, "w", encoding="utf-8") as f:
        f.write(testo)
    print(f"Domanda aperta registrata: {args.titolo}")


# ---------------------------------------------------------------- registro


INTESTAZIONE_REGISTRO = """---
id: atlas-log
type: reference
status: active
domain: ai_os
updated: {oggi}
summary: "Registro cronologico della conoscenza: ogni fonte lavorata, ogni risposta archiviata e ogni controllo di salute, in ordine di tempo. Si scrive solo aggiungendo in fondo, con System/scripts/wiki.py log."
---

# Atlas Log

Cosa \u00e8 successo alla conoscenza di questo vault, in ordine di tempo. Le pagine
dicono cosa \u00e8 vero adesso, questo registro dice come ci si \u00e8 arrivati.

**Non si scrive a mano e non si riscrive mai.** Ogni voce la aggiunge
`System/scripts/wiki.py log`, che scrive solo in fondo. Una riga vecchia
corretta a posteriori sembra vera come le altre, e non c'\u00e8 modo di accorgersene
leggendo.

Le voci cominciano tutte allo stesso modo, `## [data] tipo | titolo`, cos\u00ec si
possono contare e filtrare senza aprire il file. I tipi sono tre: `ingest` per
una fonte lavorata, `query` per una risposta archiviata, `lint` per un
controllo di salute, `ricerca` per una lacuna colmata andando a cercare fuori.

Vedi [[System/Skills/Workflows/Ingerire una Fonte|Ingerire una Fonte]],
[[System/Skills/Workflows/Interrogare il Vault|Interrogare il Vault]] e
[[System/Skills/Workflows/Salute della Conoscenza|Salute della Conoscenza]].

---
"""


def _assicura_registro():
    if not os.path.exists(REGISTRO):
        with open(REGISTRO, "w", encoding="utf-8") as f:
            f.write(INTESTAZIONE_REGISTRO.format(oggi=date.today().isoformat()))


def _timbra(testo, oggi):
    return re.sub(r"(?m)^updated:.*$", f"updated: {oggi}", testo, count=1)


def cmd_log(args):
    _assicura_registro()
    note = carica()
    chiavi = {n.chiave for n in note}
    pagine = []
    for grezza in (args.pagine or []):
        p = grezza.strip().lstrip("[").rstrip("]").split("|")[0].strip()
        if p.endswith(".md"):
            p = p[:-3]
        if p not in chiavi:
            print(f"Rifiutato: la pagina '{p}' non esiste. Il registro non puo")
            print("contenere collegamenti rotti, il controllo del vault li blocca.")
            sys.exit(1)
        pagine.append(p)

    oggi = date.today().isoformat()
    righe = [f"\n## [{oggi}] {args.tipo} | {args.titolo}\n"]
    if pagine:
        righe.append("- Pagine toccate: "
                     + ", ".join(f"[[{p}|{p.split('/')[-1]}]]" for p in pagine) + "\n")
    if args.dettaglio:
        righe.append(f"- {args.dettaglio}\n")

    testo = open(REGISTRO, encoding="utf-8").read()
    testo = _timbra(testo, oggi) + "".join(righe)
    with open(REGISTRO, "w", encoding="utf-8") as f:
        f.write(testo)
    print(f"Registrato: [{oggi}] {args.tipo} | {args.titolo}")


def cmd_ultimi(args):
    if not os.path.exists(REGISTRO):
        print("Il registro non esiste ancora.")
        return
    voci = []
    corrente = None
    for riga in open(REGISTRO, encoding="utf-8"):
        if riga.startswith("## ["):
            corrente = [riga.rstrip()]
            voci.append(corrente)
        elif corrente is not None and riga.startswith("- "):
            corrente.append("   " + riga.rstrip())
    for voce in voci[-args.n:]:
        print("\n".join(voce))
        print()
    if not voci:
        print("Il registro e vuoto.")


# ---------------------------------------------------------------- comandi


def main():
    p = argparse.ArgumentParser(
        description="Il motore del wiki di Jarvis.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("Comandi:")[1] if "Comandi:" in __doc__ else "")
    sub = p.add_subparsers(dest="comando", required=True)

    c = sub.add_parser("cerca", help="ricerca a punteggio su tutto il vault")
    c.add_argument("domanda")
    c.add_argument("--n", type=int, default=8)
    c.add_argument("--dentro", default=None,
                   help="limita a un percorso, es. Ideaverse/Atlas/")
    c.set_defaults(func=cmd_cerca)

    c = sub.add_parser("collegamenti", help="chi cita questa nota e chi cita lei")
    c.add_argument("nota")
    c.set_defaults(func=cmd_collegamenti)

    c = sub.add_parser("hub", help="le pagine piu citate")
    c.add_argument("--n", type=int, default=15)
    c.set_defaults(func=cmd_hub)

    c = sub.add_parser("orfane", help="pagine che nessuno cita")
    c.set_defaults(func=cmd_orfane)

    c = sub.add_parser("concetti", help="termini ricorrenti senza pagina propria")
    c.add_argument("--min", type=int, default=3, help="in quante pagine deve comparire")
    c.add_argument("--n", type=int, default=25)
    c.set_defaults(func=cmd_concetti)

    c = sub.add_parser("mancanti", help="note che si nominano senza collegarsi")
    c.add_argument("--n", type=int, default=30)
    c.set_defaults(func=cmd_mancanti)

    c = sub.add_parser("vecchie", help="pagine ferme da troppo tempo")
    c.add_argument("--giorni", type=int, default=60)
    c.set_defaults(func=cmd_vecchie)

    c = sub.add_parser("provenienza", help="pagine Atlas senza fonte dichiarata")
    c.set_defaults(func=cmd_provenienza)

    c = sub.add_parser("fonti", help="fonti grezze non ancora lavorate")
    c.set_defaults(func=cmd_fonti)

    c = sub.add_parser("salute", help="rapporto completo")
    c.set_defaults(func=cmd_salute)

    c = sub.add_parser("domande", help="le domande aperte del vault")
    c.set_defaults(func=cmd_domande)

    c = sub.add_parser("domanda", help="registra una domanda aperta")
    c.add_argument("titolo", help="la pagina che dovrebbe esistere")
    c.add_argument("--area", default="", help="di cosa parla")
    c.add_argument("--perche", default="", help="la domanda a cui non si sa rispondere")
    c.set_defaults(func=cmd_domanda)

    c = sub.add_parser("log", help="aggiunge una voce al registro")
    c.add_argument("tipo", choices=["ingest", "query", "lint", "ricerca"])
    c.add_argument("titolo")
    c.add_argument("--pagine", nargs="*", default=[],
                   help="percorsi completi delle note toccate")
    c.add_argument("--dettaglio", default="")
    c.set_defaults(func=cmd_log)

    c = sub.add_parser("ultimi", help="ultime voci del registro")
    c.add_argument("n", nargs="?", type=int, default=5)
    c.set_defaults(func=cmd_ultimi)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
