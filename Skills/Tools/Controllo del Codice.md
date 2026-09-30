---
id: controllo-del-codice
type: tool
status: active
domain: ai_os
updated: 2026-09-30
expose: true
summary: "Rilegge il codice appena cambiato: lo strumento decide quali file guardare e con quale lista di controlli, la rilettura la fa l'agente."
triggers: "controlla il codice, rileggi il codice, controllo del codice, revisione del codice, code review, ocr, open code review, ho cambiato il programma, prima di salvare il codice, cerca errori nel programma"
---

# Controllo del Codice

Serve a rileggere il codice dopo che è stato cambiato, cercando gli errori che
chi ha appena scritto una cosa non vede, perché ha in testa quello che voleva
fare e non quello che ha scritto.

Lo strumento sotto è **OpenCodeReview**, un programma libero di Alibaba
(licenza Apache-2.0). La ricetta per installarlo sta in
`System/scripts/controllo_codice/`, accanto al lanciatore `controlla`.

**Non è un secondo cervello che giudica al posto dell'agente.** Fa due cose
meccaniche, e le fa meglio di un agente lasciato libero: decide **quali file**
di una modifica vanno guardati, e per ognuno tira fuori la **lista dei
controlli** giusta per il linguaggio in cui è scritto. La rilettura vera la fa
l'agente, con l'abbonamento che il proprietario ha già.

---

## A cosa serve davvero, in due righe

Quando un agente scrive tanto codice in una volta tende a tagliare gli
angoli: guarda bene i primi file e passa sopra gli ultimi, e quando segnala un
problema spesso sbaglia la riga. Questo strumento toglie quella libertà: l'elenco
dei file arriva da un conto sul salvataggio, non da una scelta dell'agente,
quindi nessun file resta fuori per stanchezza.

Nel vault ha un vantaggio in più: **scarta da sé tutte le note**. Su un
salvataggio che tocca quaranta note e tre programmi, mette sul tavolo solo i
tre programmi.

---

## La prima volta: installarlo

Serve **Node.js** (nodejs.org). Il programma non sta nei salvataggi, perché
pesa una quarantina di megabyte e cambia a seconda del computer: si installa
una volta per macchina, e lo fa l'agente.

```bash
npm install --prefix System/scripts/controllo_codice
System/scripts/controllo_codice/controlla --version
```

Se il secondo comando risponde con un numero di versione, è pronto. Se Node.js
manca, lo si dice al proprietario: installarlo è una sua scelta.

---

## Come si usa

Si chiede all'agente, a parole: *"controlla il codice"*, oppure *"controlla
l'ultimo salvataggio"*, oppure *"controlla le modifiche a quel programma"*.

| Come lo chiedi | Cosa controlla |
|---|---|
| "controlla il codice" | Tutto quello che è stato cambiato e non è ancora salvato |
| "controlla l'ultimo salvataggio" | L'ultimo salvataggio fatto |
| "controlla le modifiche a …" | Solo i file di quel programma |

Va chiamato ogni volta, e non parte da solo: **questa è una scelta, non una
mancanza.** Farlo partire a ogni salvataggio vorrebbe dire far rileggere il
codice anche quando il salvataggio tocca solo note, che in un vault è il caso
più frequente, e allungare ogni salvataggio per niente.

**Il momento giusto per chiamarlo** è appena un programma è stato cambiato e
prima di salvare, cioè quando l'errore costa ancora poco.

---

## Il giro completo, per l'agente

Tre passi. Il lanciatore è `System/scripts/controllo_codice/controlla` e vuole
sempre `--color never`, altrimenti l'uscita arriva sporca di codici di colore.
Su Windows si lancia con `sh`, dalla shell di Git.

**1. Chiedere quali file.** Senza argomenti guarda il lavoro non ancora
salvato. Con `--commit <hash>` un salvataggio solo. Con `--from <ramo> --to
<ramo>` un intervallo.

```bash
System/scripts/controllo_codice/controlla delegate preview --color never
```

Risponde con la modalità, il riferimento, il messaggio del salvataggio come
contesto, e l'elenco dei file. Quelli barrati sono esclusi, con il motivo:
`unsupported_ext` sono le note, `binary` le immagini e i file compilati.
Restano i file di codice, e solo quelli vanno avanti.

**2. Chiedere la lista dei controlli**, passando tutti i file rimasti in una
volta sola:

```bash
System/scripts/controllo_codice/controlla delegate rule <file1> <file2> ...
```

Arriva una lista per gruppo di linguaggio. Per Python copre argomenti mutabili
di default, confronti con `is` al posto di `==`, `except` più larghi di quello
che gestiscono, casi limite sulle liste vuote, eccezioni inghiottite in
silenzio. **La parte che conta di più è quella che dice quando non
segnalare:** va rispettata, perché è lì che si evitano i falsi allarmi.

**3. Leggere le differenze e giudicare.** Per ogni file si prende il pezzo
cambiato, secondo la modalità del primo passo:

| Modalità | Comando |
|---|---|
| Lavoro non salvato | `git diff HEAD -- <file>` (i file nuovi si leggono interi) |
| Un salvataggio | `git show <hash> -- <file>` |
| Intervallo | `git diff <merge_base>..<to> -- <file>` |

Si commenta **solo il codice cambiato**, cioè le righe aggiunte. Poi ogni
problema si classifica: **alto** per errori veri, buchi di sicurezza, perdite
di dati; **medio** per dubbi ragionevoli e cose che dipendono dal contesto;
**basso** da buttare in silenzio, perché sono pignolerie o probabili falsi
allarmi. Quello che si aggiusta si aggiusta, il resto si spiega al proprietario
con il livello di dettaglio che la sua scheda in [[Maps & Manuals/Me|Me]] chiede.

---

## Quello che non si usa, e perché

Lo strumento ha anche un secondo modo di funzionare, `ocr review`, in cui fa
il controllo per conto suo. Per farlo però vuole **un'intelligenza artificiale
sua, a consumo, con una chiave a pagamento**: una spesa in più oltre
all'abbonamento già attivo, per un lavoro che l'agente presente sa già fare.
Se un giorno servisse, si accende con `controlla config provider` e non tocca
niente di quello scritto qui.

C'è anche `controlla scan`, che rilegge file interi invece delle sole
modifiche. Utile una volta sola su un programma vecchio che nessuno ha mai
riletto, non nel giro di tutti i giorni.

---

## Dove sta il resto

- La ricetta dell'installazione: `System/scripts/controllo_codice/package.json`
- Il progetto originale: <https://github.com/alibaba/open-code-review>
