# Changelog

## 2.1.0 — Pubblicazione GitHub Pages

- rimossi la configurazione e gli artefatti specifici del precedente servizio di hosting;
- aggiunto il workflow GitHub Actions per build, test e deploy automatico di `dist/`;
- introdotto `.nojekyll` nell'output statico;
- esclusa `dist/` dal versionamento perché viene ricostruita in modo riproducibile;
- aggiornati test, report e documentazione operativa.

## 2.0.0 — Rifattorizzazione completa

- separati `src/support/` e `src/processing/`;
- sostituiti gli script numerati con entry point essenziali;
- introdotto il modello intermedio `ContractRecord`;
- corretta la preparazione delle date di aggiudicazione e di esecuzione;
- eliminate dichiarazioni obsolete sulla copertura delle fonti;
- aggiunte analisi territoriali, cronologiche ed economiche;
- introdotto `output_data/analysis.json` come fonte comune per sito e report;
- creato sito statico responsivo con Jinja2, ricerca, filtri, ordinamento e SVG locali;
- copiati download e asset dentro `dist/`;
- aggiunto controllo automatico dei collegamenti interni;
- ampliato il report LaTeX con frammenti generati;
- aggiunti `.gitignore`, test `pytest` e documentazione operativa.
