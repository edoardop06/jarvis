---
id: atlas-log
type: reference
status: active
domain: ai_os
updated: 2026-09-30
summary: "Registro cronologico della conoscenza: ogni fonte lavorata, ogni risposta archiviata e ogni controllo di salute, in ordine di tempo. Si scrive solo aggiungendo in fondo, con System/scripts/wiki.py log."
---

# Atlas Log

Cosa è successo alla conoscenza di questo vault, in ordine di tempo. Le pagine
dicono cosa è vero adesso, questo registro dice come ci si è arrivati.

**Non si scrive a mano e non si riscrive mai.** Ogni voce la aggiunge
`System/scripts/wiki.py log`, che scrive solo in fondo. Una riga vecchia
corretta a posteriori sembra vera come le altre, e non c'è modo di accorgersene
leggendo.

Le voci cominciano tutte allo stesso modo, `## [data] tipo | titolo`, così si
possono contare e filtrare senza aprire il file. I tipi sono tre: `ingest` per
una fonte lavorata, `query` per una risposta archiviata, `lint` per un
controllo di salute, `ricerca` per una lacuna colmata andando a cercare fuori.

Vedi [[System/Skills/Workflows/Ingerire una Fonte|Ingerire una Fonte]],
[[System/Skills/Workflows/Interrogare il Vault|Interrogare il Vault]] e
[[System/Skills/Workflows/Salute della Conoscenza|Salute della Conoscenza]].

---
