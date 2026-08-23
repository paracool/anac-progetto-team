# Changelog

## 2.3.0 — Fonti web qualificate e doppio modello misto

- catalogate 26 risorse istituzionali o primarie, con copertura dei 15 CIG del dataset;
- distinti i riscontri diretti dai collegamenti per lotto, accordo quadro, CUP, procedura, fase antecedente o contesto;
- aggiunto un caricatore bloccante che verifica copertura, metadati, URL e duplicati del catalogo;
- introdotto l’elemento misto `fonteWeb`, con titolo, ente, fase, nesso e dato utile intercalati al testo;
- serializzate le fonti web negli XML ed esposte nelle pagine di dettaglio con link ufficiali e provenienza;
- collegato `B6DD95EE23` al fascicolo ufficiale contenente determina, disciplinare, verbale, graduatoria ed esito;
- aggiunti metriche di copertura, manifesto scaricabile, documentazione e test di regressione.

## 2.2.0 — Fonti collegate e navigazione d’esame

- generalizzata l’associazione delle fonti ai CIG tramite nome del file o contenuto testuale estraibile;
- collegata la lettera di invito/disciplinare al CIG `B6DD95EE23`, mantenendo anche il PDF ANAC canonico;
- sostituita la pagina autonoma “Metodologia” con “Progetto e metodo”, comprensiva della documentazione;
- rinominate le voci di navigazione ambigue e rimossa la voce generica “PDF”;
- resa esplicita la descrizione di ogni documento collegato nelle pagine di dettaglio;
- sintetizzata la relazione di progetto entro il limite di tre pagine;
- aggiunti test sul mapping generalizzato, sulla navigazione e sui download documentali.

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
