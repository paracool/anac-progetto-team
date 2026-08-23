# Archivio XML dei CIG ANAC

Progetto universitario di elaborazione documentale che trasforma fonti CSV, JSON, HTML e PDF in documenti XML, integra un catalogo qualificato di fonti web istituzionali, valida il corpus mediante DTD, estrae un modello intermedio normalizzato e genera analisi territoriali, cronologiche ed economiche. La build produce un sito statico autonomo in `dist/`, pubblicato su GitHub Pages senza backend o database.

Sito: [https://paracool.github.io/anac-progetto-team/](https://paracool.github.io/anac-progetto-team/)

## Requisiti

- Python 3.11 o successivo;
- `pip`;
- LaTeX facoltativo, necessario soltanto per ricompilare il report PDF;
- nessuna variabile segreta o API esterna.

## Struttura

```text
documenti_xml/       XML del dataset
fonti_originali/     CSV, JSON, HTML e PDF locali; catalogo web JSON
schema/              DTD
src/support/         configurazione, I/O, parsing, formattazione e controlli
src/processing/      preparazione, estrazione, analisi, sito e report
scripts/             entry point
site/templates/      template Jinja2
site/assets/         CSS e JavaScript
output_data/         risultati intermedi, incluso analysis.json
report/              report LaTeX, PDF e frammenti generati
tests/               test pytest
dist/                sito statico generato, escluso dal versionamento
```

## Installazione

### Linux e macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
```

### Windows PowerShell

```powershell
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
```

## Preparazione del dataset

```bash
python scripts/prepare.py
```

La preparazione individua dinamicamente i CIG presenti nelle fonti JSON e integra le righe corrispondenti del CSV. Le altre fonti locali vengono associate cercando il CIG prima nel nome del file e, per i nomi descrittivi, nel contenuto testuale estraibile. Il criterio vale per l’intero dataset e non contiene eccezioni dedicate a singoli CIG.

Le risorse reperite sul web sono descritte in `fonti_originali/web/fonti_web.json`. Il caricatore pretende la corrispondenza esatta con l’insieme dei CIG, almeno una fonte per record, URL HTTP(S) validi e metadati completi. Ogni voce distingue il nesso probatorio (`cig-esatto`, lotto o accordo quadro, CUP e oggetto, procedura, fase antecedente, contesto o repertorio) affinché una fonte indiretta non venga presentata come atto della gara.

## Build del sito

Per validare gli XML esistenti, calcolare le analisi e generare `dist/`:

```bash
python scripts/build.py
```

Per rigenerare prima gli XML e, quando `pdflatex` è disponibile, compilare anche il report:

```bash
python scripts/build_all.py
```

Il controllo dei collegamenti viene eseguito automaticamente sulla sola directory `dist/`. La build fallisce se un riferimento locale non esiste o punta fuori dalla directory pubblicata.

## Report LaTeX

Dopo una build, i frammenti dinamici sono disponibili in `report/generated/`:

```bash
python scripts/build_report.py
```

La build GitHub Pages non richiede LaTeX. Se `report/report_progetto.pdf` è già presente, viene copiato in `dist/downloads/report/`.

## Test

```bash
pytest
```

I test coprono parsing di importi e date, normalizzazione, estrazione XML, validazione dei due content model misti, copertura integrale del catalogo web, anomalie cronologiche, statistiche, pagine principali, collegamenti e file indispensabili al deploy.

## Contenuto di `dist/`

```text
dist/
├── index.html
├── archivio.html
├── report.html
├── progetto.html
├── qualita-dati.html
├── cig/
├── assets/
├── data/
├── downloads/
└── .nojekyll
```

Tutti i CSS, JavaScript, SVG, dati e download necessari sono locali. `assets/css/stile.css` è il foglio comune applicato a tutte le pagine e importa i moduli di base e delle fonti. Nessun collegamento relativo deve uscire da `dist/`.

## Pubblicazione su GitHub Pages

Il workflow `.github/workflows/pages.yml` viene eseguito a ogni push su `main` e può essere avviato anche manualmente. La procedura:

1. installa Python e le dipendenze;
2. rigenera gli XML con `python scripts/prepare.py`, includendo gli eventuali nuovi documenti collegati;
3. genera il sito con `python scripts/build.py`;
4. esegue l'intera suite `pytest`;
5. carica esclusivamente `dist/` come artefatto GitHub Pages;
6. pubblica il sito nell'ambiente `github-pages`.

Nel repository, la sorgente di pubblicazione deve essere impostata una sola volta su **Settings → Pages → Source: GitHub Actions**. Il sito viene quindi aggiornato automaticamente all'indirizzo:

<https://paracool.github.io/anac-progetto-team/>

I riferimenti interni sono relativi e restano validi sotto il percorso di progetto `/anac-progetto-team/`. La directory `dist/` non viene versionata: è ricostruita in modo riproducibile dal workflow, evitando la duplicazione delle fonti e degli artefatti.

## Anteprima locale

Dopo la build, avviare un server HTTP dalla radice del progetto:

```bash
python -m http.server 8000 --directory dist
```

Il sito è disponibile su <http://localhost:8000/>.

## Risoluzione dei problemi

- **XML non valido:** consultare `output_data/validation.xml`; la build si interrompe prima della pubblicazione.
- **Link interrotto:** il messaggio indica pagina e percorso inesistente dentro `dist/`.
- **Report PDF assente:** installare una distribuzione LaTeX ed eseguire `python scripts/build_report.py`; il sito funziona comunque.
- **Fonte non trovata:** verificare che il CIG compaia nel nome oppure nel testo estraibile del documento. Per i PDF acquisiti come sole immagini è necessaria una versione con testo OCR.
- **Ambiente Windows non attivato:** usare `.venv\Scripts\Activate.ps1` in PowerShell oppure `.venv\Scripts\activate.bat` nel Prompt dei comandi.

## Provenienza e limiti dei dati

Il campione coincide con i documenti conservati nel progetto e non rappresenta necessariamente l'intero sistema degli appalti pubblici. Le incongruenze cronologiche vengono segnalate senza correggere i dati e senza attribuirle automaticamente a errori della fonte. Le differenze tra importo di gara e aggiudicazione sono descrittive e non vengono denominate automaticamente ribassi. Le fonti web sono state verificate nella data dichiarata dal manifesto; disponibilità e contenuto delle pagine esterne possono mutare. Il tipo di nesso resta quindi sempre visibile nel sito e negli XML.

## Modifiche principali

La versione corrente introduce 26 fonti web qualificate per tutti i 15 CIG, un secondo content model misto dedicato agli approfondimenti, associazione generalizzata delle fonti locali, navigazione orientata alla discussione d’esame, pagina unificata “Progetto e metodo”, relazione sintetica conforme al limite di tre pagine, modello `ContractRecord`, analisi territoriali/temporali/economiche, microdata, pubblicazione automatica su GitHub Pages e test automatici. Il dettaglio è riportato in `CHANGELOG.md`.
