# Jarvis

Un assistente personale: un vault di Obsidian con dentro regole e procedure, che Claude legge e usa.

## Installarlo su un Mac nuovo

1. Installa **Obsidian** (obsidian.md), **VS Code** (code.visualstudio.com) e, dentro VS Code, l'estensione **Claude Code**, entrando con il tuo account Claude.
2. Da questa pagina di GitHub premi **Code**, poi **Download ZIP**, e apri lo ZIP scaricato.
3. Nella cartella che compare, fai clic destro su **Installa Jarvis.command** e scegli **Apri**. La prima volta il Mac chiede conferma perché il file viene da internet.
4. Rispondi alle domande: nome della cartella, nome e email. Il resto lo fa da solo.
5. Apri la cartella in Obsidian e in VS Code, avvia Claude Code, rispondi sì alla domanda sulla fiducia e scrivi `/onboard`.

Su Windows vale ancora la guida manuale, [[SETUP-WINDOWS|SETUP-WINDOWS]].

---

## What this is

A personal AI operating system built in Obsidian, in plain Markdown, so the system outlives any particular model.

**This is a fresh vault.** It has the machinery but none of the content. See [[Maps & Manuals/Me|Me]], which is written during onboarding and which everything else depends on.

## How it fits together

**Maps & Manuals** is the guidance layer: who the user is, how the system works, where things live, and what tools exist. Agents read [[Maps & Manuals/Me|Me]] then [[Maps & Manuals/Active Context|Active Context]] before doing anything.

**Ideaverse** is the content layer: efforts (active projects), Atlas (permanent reference notes), sources, outputs, calendar, and archive. This starts empty and fills up with the user's actual work.

**Skills** is the capability layer: reusable workflows, tool documentation, templates, and data standards.

**scripts** is the machinery: `build_views.py` generates every index table from note frontmatter, `vault_lint.py` enforces the conventions, and a git pre-commit hook blocks commits that break them.

## The rule that makes it work

Frontmatter is the database. Index tables between `<!-- BEGIN GENERATED -->` markers are generated from it and must never be edited by hand. To change what a table says, change the note's frontmatter and rerun `python3 System/scripts/build_views.py`.

## Setup

Start with [[SETUP|SETUP]]. It is an ordered checklist from a bare Mac to a working vault, including the steps that are easy to miss. The last step hands over to `/onboard`, which fills in [[Maps & Manuals/Me|Me]] in conversation with the vault's owner.
