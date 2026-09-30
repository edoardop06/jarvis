---
id: motore-del-wiki
type: tool
status: active
domain: ai_os
updated: 2026-09-30
expose: true
summary: "Lo strumento del wiki: ricerca nelle note, citazioni, pagine orfane, collegamenti mancanti."
triggers: "cerca nel vault, chi cita questa nota, pagine orfane, collegamenti mancanti, registro della conoscenza"
---

# Motore del Wiki

`System/scripts/wiki.py` è lo strumento che gli agenti usano per lavorare sul vault senza aprire le note una per una. Solo libreria standard: non va installato niente e funziona anche senza rete.

**Cosa fa e cosa non fa.** Fa solo quello che è meccanico e verificabile: conta, cerca, elenca, confronta date. Non giudica. Se due pagine si contraddicono, se una fonte vale, se un nome merita una pagina sua, quello lo decide l'agente leggendo le pagine che lo script gli mette davanti.

Si lancia sempre dalla cartella del vault. Le pagine nuove le scrive l'agente, non lo script.

---

## Comandi

| Comando | A cosa serve |
|---|---|
| `cerca "domanda"` | Ricerca a punteggio su tutte le note. È il primo passo di qualsiasi risposta |
| `collegamenti NOTA` | Chi cita questa nota e chi cita lei, più i collegamenti rotti |
| `hub` | Le pagine più citate, cioè il centro del vault |
| `orfane` | Pagine che nessuno cita, irraggiungibili navigando |
| `concetti` | Nomi e sigle che tornano in più pagine senza averne una propria |
| `mancanti` | Note che si nominano a vicenda senza collegarsi |
| `vecchie` | Pagine ferme da più di 60 giorni |
| `provenienza` | Pagine Atlas che non dichiarano da dove viene quello che affermano |
| `fonti` | Fonti grezze non ancora lavorate, più cosa aspetta in Inbox |
| `salute` | Tutti i controlli sopra in un rapporto solo |
| `domande` | Le domande aperte, cioè cosa il vault sa di non sapere |
| `domanda "titolo"` | Segna una domanda aperta senza rovinare la tabella a mano |
| `log TIPO "titolo"` | Aggiunge una voce a [[Ideaverse/Atlas/Atlas Log\|Atlas Log]] |
| `ultimi [N]` | Le ultime N voci del registro |

Esempi:

```bash
python3 System/scripts/wiki.py cerca "come si rinnova il passaporto" --n 5
python3 System/scripts/wiki.py cerca "ricette" --dentro Ideaverse/Atlas/
python3 System/scripts/wiki.py collegamenti "Nome della nota"
python3 System/scripts/wiki.py salute
python3 System/scripts/wiki.py log ingest "Titolo della fonte" --pagine "Ideaverse/Atlas/Nota" --dettaglio "cosa è cambiato"
```

---

## Due cose da sapere prima di usarlo

**La ricerca pesa titolo e sommario più del corpo.** Una nota che ha il termine nel titolo sale sopra una che lo nomina dieci volte in mezzo al testo, perché il titolo è quello che l'autore ha deciso che la nota è. Chi contiene la domanda intera come frase sale ancora di più.

**Il registro si scrive solo con `log`.** Il comando aggiunge in fondo e non tocca il resto, e rifiuta di scrivere il collegamento a una pagina che non esiste, così il controllo del vault non si blocca dopo. Non modificare [[Ideaverse/Atlas/Atlas Log|Atlas Log]] a mano.

---

## Related

Le quattro funzioni che lo usano: [[System/Skills/Workflows/Ingerire una Fonte|Ingerire una Fonte]], [[System/Skills/Workflows/Interrogare il Vault|Interrogare il Vault]], [[System/Skills/Workflows/Salute della Conoscenza|Salute della Conoscenza]], [[System/Skills/Workflows/Ricerca Autonoma|Ricerca Autonoma]].

Il controllo strutturale del vault è un'altra cosa e resta [[System/Skills/Tools/Vault Lint|Vault Lint]]: quello guarda se i file sono a posto, questo guarda se la conoscenza è a posto.

Da dove viene: l'idea del *LLM Wiki*, un wiki personale che un modello linguistico tiene in ordine da sé, invece di rileggere ogni volta i documenti da capo.
