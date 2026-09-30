---
id: salute-della-conoscenza
type: workflow
status: active
domain: ai_os
updated: 2026-09-30
expose: true
summary: "Controllo periodico della conoscenza: contraddizioni, pagine superate o orfane, buchi da colmare."
triggers: "controlla il vault, salute del wiki, ci sono contraddizioni, cosa dovrei approfondire"
---

# Salute della Conoscenza

Un wiki che cresce si guasta in silenzio. Due pagine finiscono per dire cose diverse, una resta ferma a prima che le cose cambiassero, un nome torna in cinque note senza avere una pagina sua. Nessuno di questi problemi si vede leggendo una pagina alla volta.

**Questo controllo è diverso da [[System/Skills/Tools/Vault Lint|Vault Lint]].** Quello guarda se i file sono a posto: collegamenti rotti, blocchi impostazioni mancanti, tabelle rovinate. Questo guarda se la conoscenza è a posto, che è un'altra domanda e non si risponde da sola.

Da fare una volta a settimana, e ogni volta che sono entrate parecchie fonti insieme.

---

## Passi

**1. Chiedi i numeri:**

```bash
python3 System/scripts/wiki.py salute
```

**2. Poi fai la parte che lo script non può fare.** Nell'ordine:

- **Contraddizioni.** Prendi le pagine che coprono lo stesso argomento e leggile davvero, non solo il sommario. Due pagine che dicono cose diverse sono la cosa peggiore che può avere un wiki, perché sembrano vere tutte e due.
- **Affermazioni superate.** Per ogni pagina ferma da mesi: è ferma perché è stabile o perché è rimasta indietro? Guarda se una fonte più recente ha già detto il contrario.
- **Nomi senza pagina.** Lo script elenca sigle e nomi propri che tornano in più pagine. Quali meritano davvero una pagina? Un componente comprato tre volte sì, una parola tornata per caso no.
- **Pagine orfane.** O le colleghi da dove ha senso, o vanno in `Ideaverse/Archive/`. Una pagina che nessuno cita non esiste.
- **Collegamenti mancanti.** Quelli elencati si aggiungono e basta, sono lavoro meccanico.
- **Fonti ferme.** Quello che sta in `Ideaverse/Inbox/` da giorni o è da lavorare o è da buttare.
- **Buchi.** Cosa il vault dovrebbe sapere e non sa. Qui l'esito non è una correzione: è una domanda da segnare con `wiki.py domanda`, e quando vale la pena una [[System/Skills/Workflows/Ricerca Autonoma|Ricerca Autonoma]] che vada a cercarla fuori.

**3. Sistema tu quello che è meccanico**, senza chiedere: collegamenti mancanti, provenienze da aggiungere, sommari sbagliati.

**4. Porta al proprietario solo le decisioni.** Una lista corta di cose che richiedono lui, non l'output dello script. Formato: cosa ho trovato, cosa ho già sistemato, cosa decidi tu.

**5. Registra il controllo:**

```bash
python3 System/scripts/wiki.py log lint "Controllo di salute" --dettaglio "cosa è emerso e cosa hai sistemato"
```

---

## Come si legge il rapporto

| Cosa dice lo script | Cosa vuol dire davvero |
|---|---|
| Pagine orfane | Sono scritte ma irraggiungibili. O si collegano o si archiviano |
| Pagine senza fonte | Nessuno può verificarle. Se non ricordi da dove viene, va scritto che non si sa |
| Collegamenti mancanti | Il wiki è più povero di quello che sembra: le pagine si nominano ma non si toccano |
| Ferme da più di 60 giorni | Da controllare, non da buttare. Alcune sono ferme perché sono giuste |
| Nomi senza pagina | Candidati a diventare pagine. La maggior parte non lo merita, qualcuno sì |

---

## Related

[[System/Skills/Tools/Motore del Wiki|Motore del Wiki]] | [[System/Skills/Workflows/Ingerire una Fonte|Ingerire una Fonte]] | [[System/Skills/Workflows/Interrogare il Vault|Interrogare il Vault]] | [[System/Skills/Workflows/Weekly Maintenance|Weekly Maintenance]] | [[Ideaverse/Atlas/Atlas Log|Atlas Log]]

Da dove viene: l'idea del *LLM Wiki*, un wiki personale che un modello linguistico tiene in ordine da sé, invece di rileggere ogni volta i documenti da capo.
