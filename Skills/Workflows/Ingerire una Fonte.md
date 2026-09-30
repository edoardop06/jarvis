---
id: ingerire-una-fonte
type: workflow
status: active
domain: ai_os
updated: 2026-09-30
expose: true
summary: "Portare una fonte nuova nel wiki: aggiorna le pagine esistenti e dichiara le contraddizioni."
triggers: "ho letto questo articolo, ingerisci, lavora questa fonte, aggiungi al wiki, leggi questo pdf"
---

# Ingerire una Fonte

Quando arriva materiale nuovo: un articolo, un video, una scheda tecnica, un vocale, la foto di un documento, una conversazione da salvare.

**Il punto di questa funzione.** Una fonte non diventa una nota. Diventa una modifica in più punti del vault: qualche pagina cresce, qualche affermazione vecchia viene corretta, ogni tanto nasce una pagina nuova, e resta scritto da dove viene tutto. Sono due lavori diversi: chi ingerisce guarda cosa esiste già, chi archivia guarda solo il file che ha in mano.

**Prima di crearla, cercala.** Il modo più semplice di rovinare un wiki è creare la seconda pagina sullo stesso argomento. La ricerca non è facoltativa.

---

## Passi

**1. Leggi la fonte per intero.** Non a campione. Se è un vocale o un'immagine in `Ideaverse/Inbox/`, trascrivila o guardala prima di scrivere qualsiasi cosa.

**2. Non toccare mai il file grezzo.** Le fonti sono immutabili: sono l'unica cosa nel vault che non è stata scritta da un agente, e valgono proprio per quello.

**3. Dì al proprietario cosa hai trovato, in tre o quattro punti, e prosegui.** Non aspettare risposta per iniziare. Fermati e chiedi solo in un caso: la fonte contraddice qualcosa che il vault dà già per vero.

**4. Cerca cosa il vault sa già**, una ricerca per ogni argomento principale della fonte:

```bash
python3 System/scripts/wiki.py cerca "argomento della fonte"
```

**5. Crea la scheda della fonte** in `Ideaverse/Sources/`, con il nome `YYYY-MM-DD - Argomento.md` e il blocco impostazioni in cima (`id`, `type: source`, `status: raw`, `domain`, `updated`, `summary`). Dentro: cosa è, da dove viene, il collegamento all'originale, e cosa contiene di utile. Questa non è la pagina di conoscenza, è la ricevuta della fonte.

**6. Aggiorna le pagine che esistono già.** Una fonte seria ne tocca diverse. Le regole di scrittura di una pagina Atlas non le riscrivo qui, stanno in [[System/Skills/Workflows/Process Source into Atlas|Process Source into Atlas]].

**7. Crea una pagina nuova solo se un concetto non ha casa.** Se ce l'ha, il posto giusto è dentro la pagina esistente. Una pagina nuova nasce già collegata da almeno un'altra, altrimenti nasce orfana e nessuno la trova più.

**8. Le contraddizioni si dichiarano, non si sovrascrivono.** Quando la fonte nuova dice il contrario di quello che c'è scritto, tieni tutte e due le versioni con la data e la fonte di ciascuna, scrivi quale sembra valere adesso e perché, e diglielo. Cancellare la versione vecchia fa sparire l'unico indizio che qualcosa è cambiato.

**9. Ogni affermazione deve avere una provenienza.** In fondo alla pagina, il collegamento alla scheda della fonte. Una pagina senza fonte fra sei mesi non è distinguibile da una cosa inventata.

**10. Collega.** Poi controlla di non averne dimenticato nessuno:

```bash
python3 System/scripts/wiki.py mancanti
```

**11. Segna la fonte come lavorata**: `status: processed`, e nella scheda i collegamenti alle pagine che ha prodotto.

**12. Registra cosa hai fatto:**

```bash
python3 System/scripts/wiki.py log ingest "Titolo della fonte" --pagine "Ideaverse/Atlas/Prima" "Ideaverse/Atlas/Seconda" --dettaglio "cosa è cambiato in una riga"
```

**13. Chiudi.** Rigenera le tabelle automatiche, fai il controllo del vault, salva.

---

## Prima di dire che hai finito

- La fonte grezza è ancora dov'era e intatta.
- Nessuna pagina duplica una che esiste già.
- Ogni pagina toccata dice da dove viene quello che afferma.
- Nessuna pagina nuova è orfana.
- Le contraddizioni trovate sono scritte, non risolte in silenzio.
- La voce è nel registro.

---

## Related

[[System/Skills/Tools/Motore del Wiki|Motore del Wiki]] | [[System/Skills/Workflows/Interrogare il Vault|Interrogare il Vault]] | [[System/Skills/Workflows/Salute della Conoscenza|Salute della Conoscenza]] | [[System/Skills/Workflows/Capture|Capture]] | [[Ideaverse/Atlas/Atlas Log|Atlas Log]]

Da dove viene: l'idea del *LLM Wiki*, un wiki personale che un modello linguistico tiene in ordine da sé, invece di rileggere ogni volta i documenti da capo.
