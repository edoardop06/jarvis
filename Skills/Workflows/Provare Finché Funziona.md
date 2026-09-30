---
id: provare-finche-funziona
type: workflow
status: active
domain: ai_os
updated: 2026-09-30
expose: true
summary: "Far funzionare una cosa provando: misura decisa prima, un cambio per volta, stop dopo tre prove a vuoto."
triggers: "fallo funzionare, non funziona, prova finché non funziona, rendilo più veloce, sistemalo"
---

# Provare Finché Funziona

Quando il proprietario vuole che una cosa funzioni e non è ovvio come: uno script, un collegamento, un'impostazione, un pezzo di un processo di lavoro.

**Il punto di questa funzione.** Provare non è il problema, provare a caso lo è. Senza un modo di riconoscere la riuscita non si smette mai, senza un registro dei tentativi al settimo si rifà il secondo, e senza una regola di uscita si può girare a vuoto per ore facendo sembrare che si stia lavorando.

**Due fasi, in quest'ordine, mai insieme.** Prima farla funzionare. Poi, solo se ha senso, renderla efficiente. Chi ottimizza qualcosa che ancora non funziona sta perdendo tempo due volte.

---

## Le regole

**1. Prima di toccare qualsiasi cosa, decidi come si riconosce che funziona.** Un comando che finisce bene, un numero da confrontare, un fatto che si può guardare. Se non si riesce a scrivere, il problema non è ancora chiaro abbastanza per provare a risolverlo, e va chiarito prima.

**2. Un cambiamento per tentativo.** Due insieme e non si sa quale dei due ha funzionato. È la regola che si viola sempre quando si ha fretta, ed è sempre quella che fa perdere più tempo.

**3. Chi non migliora viene annullato.** Se il banco dichiara quali file sono in gioco, prima di ogni tentativo ne viene conservata una copia, e un tentativo che peggiora la misura o rompe tutto rimette i file com'erano. È questa la cosa che rende il provare gratis: si può osare una strada improbabile, perché se va male non lascia niente dietro. Senza questo, dopo dieci tentativi non si sa più in che stato sia la cosa.

**4. La misura si prende sempre allo stesso modo**, stesso comando e stesso tempo massimo. Due misure prese in condizioni diverse non si possono confrontare, e allora tutto il resto non serve a niente.

**5. Ogni tentativo si scrive, anche e soprattutto quelli falliti.** Un tentativo fallito registrato è una strada che nessuno rifarà più. Un tentativo fallito dimenticato è una strada che si rifà tra due settimane.

**6. Tre tentativi senza un miglioramento e si smette.** Non è arrendersi: è il segnale che il problema è posto male. Si torna dal proprietario con cosa è stato provato, cosa si è capito, e le strade che restano. Continuare oltre è testardaggine, e la paga lui in tempo.

**7. Si prova solo su cose ripetibili e senza conseguenze.** Mai in ciclo su cose che escono fuori: mandare messaggi, pubblicare, comprare, cancellare, scrivere a un cliente. Se la prova richiede una di queste, si prepara tutto e si chiede al proprietario.

**8. L'efficienza si tocca solo dopo, e solo se c'è un numero.** "Più veloce" senza una misura è aria. Con una misura è un fatto, e si vede subito quando smettere: quando i tentativi non spostano più il numero.

**9. Quando il banco si chiude, quello che si è imparato va nel vault.** Altrimenti la prossima volta si ricomincia da zero, che è esattamente la cosa che questo sistema esiste per evitare.

---

## Passi

**1. Scrivi l'obiettivo in una riga** e il modo di misurarlo. Poi apri il banco, dentro la cartella del progetto a cui la cosa appartiene:

```bash
python3 System/scripts/banco.py apri "Ideaverse/Efforts/Categoria/Progetto/Banco - nome" --obiettivo "cosa deve fare" --misura "il comando che dice se funziona" --soglia "quando si considera riuscito" --direzione minore --tocca "percorso/del/file.py"
```

`--tocca` elenca i file che i tentativi cambiano, separati da punto e virgola: è quello che permette di annullare da soli i tentativi andati male. `--direzione` dice se fra due misure vince la più bassa, come i secondi, o la più alta, come una percentuale di riuscita.

Se la cosa non appartiene a nessun progetto, la categoria si chiede al proprietario, come dice [[Maps & Manuals/Vault Map|Vault Map]].

**2. Misura prima di toccare niente.** Il primo tentativo si chiama "punto di partenza" e non cambia nulla: serve ad avere il numero con cui confrontare tutti gli altri. Senza, "è migliorato" resta un'impressione.

**3. Cambia una cosa sola. Poi misura:**

```bash
python3 System/scripts/banco.py prova "percorso del banco" --cambio "cosa ho cambiato stavolta"
```

Il comando lo esegue lo strumento e registra l'esito da solo. Non scrivere tu nella tabella: "funziona" deve essere una misura, non un'opinione dell'agente che ha appena scritto il codice.

Lo strumento dice da solo se il tentativo è stato tenuto o annullato. Non discuterci: se dice annullato, i file sono già tornati com'erano e quella strada è chiusa.

**4. Ogni tre o quattro tentativi, guarda se stai migliorando o girando:**

```bash
python3 System/scripts/banco.py stato "percorso del banco"
```

Quando dice che sono passati tre tentativi senza miglioramenti, ci si ferma. È l'unica regola di uscita e non si tratta.

**5. Quando funziona, fermati e dillo.** Non passare all'efficienza di iniziativa propria: quasi sempre "funziona" è già tutto quello che serviva.

**6. Se l'efficienza serve davvero**, riparti dallo stesso banco con la misura numerica (secondi, righe, euro, passaggi) e continua a provare finché il numero non smette di muoversi.

**7. Chiudi il banco.** Riempi "Cosa si è imparato" in fondo alla nota, porta la lezione dentro il wiki se vale oltre questo caso, e registrala:

```bash
python3 System/scripts/wiki.py log ricerca "Banco: nome" --dettaglio "cosa funziona adesso e cosa si è imparato"
```

---

## Lasciarlo lavorare da solo

Con l'annullamento automatico attivo, i tentativi si possono incatenare senza stare a guardare: l'agente cambia, misura, tiene o butta, e ricomincia. È il modo in cui si mandano avanti decine di tentativi mentre il proprietario fa altro.

Vale solo con tutte e tre queste condizioni, e se ne manca una non si parte:

- **I file in gioco sono dichiarati**, altrimenti un tentativo sbagliato resta lì.
- **La misura non ha conseguenze fuori.** Non manda, non pubblica, non compra, non scrive a nessuno. Un ciclo che sbaglia lo fa cinquanta volte.
- **C'è un limite di tentativi deciso prima**, e la regola dei tre senza miglioramento resta in piedi dentro il ciclo.

Alla fine si consegna il riassunto, non i cinquanta tentativi: quelli stanno nella nota per chi vuole guardarli.

---

## Cosa consegnare

- **Funziona o no**, detto in una riga, con il fatto che lo dimostra.
- **Quanti tentativi** e cosa è servito. Non l'elenco completo, quello sta nella nota.
- **Cosa resta fragile**, se resta qualcosa. Una cosa che funziona per caso va detto che funziona per caso.

---

## Related

[[System/Skills/Tools/Motore del Wiki|Motore del Wiki]] | [[System/Skills/Workflows/Ricerca Autonoma|Ricerca Autonoma]] | [[System/Skills/Workflows/Ingerire una Fonte|Ingerire una Fonte]] | [[System/Skills/Workflows/Fable Mode|Fable Mode]] | [[Ideaverse/Atlas/Atlas Log|Atlas Log]]

Lo strumento è `System/scripts/banco.py`. Tiene la nota del banco, esegue la misura e conta i tentativi dall'ultimo miglioramento.

**Da dove viene.** L'idea è quella di *autoresearch*: un agente cambia il codice, misura sempre con lo stesso tempo, tiene o butta il cambiamento e ricomincia. Da lì vengono il punto di partenza misurato, il tempo uguale per tutti i tentativi e l'annullamento automatico. La regola dei tre tentativi e il fermarsi a parlare con il proprietario sono invece di Jarvis, perché qui non si lavora da soli per una notte intera su un problema solo.

**Da non confondere con [[System/Skills/Workflows/Ricerca Autonoma|Ricerca Autonoma]]:** quella va a cercare fuori quello che il vault non sa, questa prova finché una cosa funziona.
