---
id: interrogare-il-vault
type: workflow
status: active
domain: ai_os
updated: 2026-09-30
expose: true
summary: "Rispondere dalle note con le fonti citate, e archiviare le risposte che valgono."
triggers: "cosa so di, cosa avevamo detto, dove ho scritto, riassumimi, secondo il vault"
---

# Interrogare il Vault

Quando il proprietario fa una domanda a cui il vault può rispondere: un confronto, un riassunto, una cosa detta mesi fa, un "come funzionava quella cosa".

**Il punto di questa funzione.** Una buona risposta costa lavoro e di solito muore nella chat. Se vale, diventa una pagina, e la volta dopo è già lì. È così che il vault cresce anche nelle settimane in cui non entra nessuna fonte nuova.

---

## Passi

**1. Cerca prima di aprire.** Non aprire note a caso e non fidarti della memoria della conversazione:

```bash
python3 System/scripts/wiki.py cerca "la domanda, con le parole di chi la fa"
```

**2. Leggi i sommari, apri solo quello che serve.** Il sommario in cima a ogni nota esiste per decidere se aprirla. Aprirle tutte è la cosa che rende le risposte lente e confuse.

**3. Segui i collegamenti di quello che apri.** La risposta buona spesso sta in una nota vicina, non nella prima:

```bash
python3 System/scripts/wiki.py collegamenti "Nome della nota"
```

**4. Rispondi citando.** Ogni affermazione presa dal vault porta il collegamento alla pagina da cui viene. Serve a chi legge per verificare senza chiedere.

**5. Di' anche cosa il vault non sa.** Una lacuna dichiarata vale più di una risposta completa a metà. Se manca una fonte per rispondere bene, dillo e proponi quale. Se la lacuna conta, segnala con `wiki.py domanda` e proponi una [[System/Skills/Workflows/Ricerca Autonoma|Ricerca Autonoma]].

**6. Decidi se la risposta va archiviata.** Il test è uno:

> Fra tre mesi, questa risposta servirebbe a qualcuno che non ha fatto la domanda?

- **Sì, ed è conoscenza permanente** (come funziona una cosa, un confronto, una regola del settore): diventa una pagina in `Ideaverse/Atlas/`.
- **Sì, ed è un documento finito** (una tabella, un confronto, una lettera): va in `Ideaverse/Outputs/`.
- **Sì, ma riguarda un progetto solo**: va dentro la nota di quel progetto.
- **No**: non archiviare niente. Non tutte le domande meritano una pagina, e un vault pieno di risposte usa e getta è peggio di uno vuoto.

**7. Se archivi, collega.** La pagina nuova va citata dalle pagine su cui si basa, non solo il contrario. Una pagina che nessuno cita non la ritrova più nessuno.

**8. Registra solo quello che hai archiviato:**

```bash
python3 System/scripts/wiki.py log query "La domanda" --pagine "Ideaverse/Atlas/Pagina nuova" --dettaglio "cosa risponde"
```

---

## Cosa non archiviare mai

- Le risposte di servizio: stato di una cosa, conferme, "fatto".
- Quello che è già scritto altrove. Meglio aggiungere due righe alla pagina che esiste.
- I progetti vecchi tirati dentro per fare da contesto. Vale la regola della memoria in [[Maps & Manuals/Me|Me]]: la memoria serve a rispondere meglio adesso, non a riportare il proprietario su un lavoro in sospeso.

---

## Related

[[System/Skills/Tools/Motore del Wiki|Motore del Wiki]] | [[System/Skills/Workflows/Ingerire una Fonte|Ingerire una Fonte]] | [[System/Skills/Workflows/Salute della Conoscenza|Salute della Conoscenza]] | [[Ideaverse/Atlas/Atlas Log|Atlas Log]]

Da dove viene: l'idea del *LLM Wiki*, un wiki personale che un modello linguistico tiene in ordine da sé, invece di rileggere ogni volta i documenti da capo.
