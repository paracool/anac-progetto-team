# Prompt utilizzati e documentati

## Prompt 1 — Analisi della struttura del progetto

Analizza le specifiche del progetto TEAM e verifica che la struttura del progetto distingua correttamente tra fonti originali, directory XML di input, DTD, script Python, output HTML/CSS e report finale. Evidenzia eventuali elementi non conformi e proponi correzioni minime senza introdurre requisiti non presenti nelle specifiche.

## Prompt 2 — Modellazione XML dei CIG

A partire da un CSV ANAC con CIG e da JSON di dettaglio disponibili per alcuni CIG, progetta un modello XML descrittivo per rappresentare un singolo contratto pubblico. Il modello deve evitare una semplice struttura tabellare, deve includere contenuto misto, deve mantenere il collegamento alle fonti originali e deve poter essere validato con DTD.

## Prompt 3 — DTD e validazione

Dato il modello XML dei contratti pubblici, costruisci una DTD semplice ma coerente. Alcune sezioni devono essere opzionali perché non tutti i CIG hanno JSON dettagliato, aggiudicazione, CPV o PDF. La descrizione documentale deve consentire contenuto misto con elementi interni come tipologia, oggetto, categoria, termine e luogo.

## Prompt 4 — Allineamento agli esempi di laboratorio

Riscrivi gli script Python in modo che seguano l’impostazione degli esempi di laboratorio: uso di `lxml.etree`, variabile `DOCS_DIR`, scansione della directory XML, parsing, validazione DTD e generazione di HTML. Integra inoltre uno script di verifica microdata e uno script di analisi PDF con librerie viste nel corso.

## Prompt 5 — Revisione del report

Revisiona il report LaTeX del progetto affinché descriva in modo sintetico la fase di preparazione, la directory XML di input, la validazione, gli output prodotti, le librerie Python utilizzate e i limiti del lavoro. Il testo deve restare nel perimetro del corso e non trasformarsi in una relazione sugli appalti pubblici.

## Prompt 6 — Rifattorizzazione, analisi e pubblicazione statica

È stato richiesto di analizzare integralmente il progetto, separare il codice di supporto dalle elaborazioni, introdurre un modello intermedio dei record, implementare analisi territoriali, cronologiche ed economiche, trasformare l'output in un sito statico responsivo e accessibile, predisporre la pubblicazione automatizzata, ampliare il report LaTeX e aggiungere test automatici.

Gli output generati sono stati verificati mediante esecuzione della pipeline completa, validazione DTD, confronto dei conteggi delle fonti, controllo automatico dei collegamenti nella directory `dist/`, test `pytest`, verifica dei microdata e compilazione LaTeX quando disponibile. Le metriche del report non sono state trascritte manualmente: derivano da `output_data/analysis.json` e dai frammenti in `report/generated/`.

## Prompt 7 — Ricerca e qualificazione delle fonti web

Per ogni CIG presente nell’archivio, reperisci documenti, determine o altre fonti web autorevoli riferibili alla gara. Le risorse devono arricchire le fonti originarie e consolidare il content model misto. Evita soluzioni limitate a un CIG: conserva provenienza, formato, fase e criterio di collegamento, distinguendo un riscontro esatto da una fonte relativa a lotto, accordo quadro, CUP, fase antecedente o contesto.

Le risorse selezionate sono state registrate in un manifesto dati e integrate nella pipeline comune. La verifica non si limita alla raggiungibilità del collegamento: il nesso dichiarato evita di attribuire a una gara un atto che documenta soltanto il suo contesto. Per i procedimenti relativi a minori è stata inoltre privilegiata la minimizzazione, collegando fonti istituzionali senza ripubblicare documenti potenzialmente sensibili.
