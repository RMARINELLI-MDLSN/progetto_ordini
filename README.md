# Generatore SQL ordini

Generatore Python senza dipendenze esterne. L’esecutore SQL richiede pyodbc e un driver ODBC SQL Server. Richiede Python 3.9 o successivo.
Genera un SQL per riga CSV; non si connette al database e non esegue query.

## Avvio

1. Estrai tutto il progetto e apri un terminale nella cartella estratta.
2. Modifica `config.json`: server, istanza, nome database e `file_csv`.
3. Esegui `python leggi_ordini.py`.

Il config.json punta al nuovo CSV Ordini_Alba_Tramezzini_data_fine_calcolata.csv, incluso nel progetto. Il precedente CSV con tre ordini resta come riferimento per i test.
I percorsi relativi nel JSON sono risolti rispetto alla cartella del JSON.
L'istanza predefinita si indica con una stringa vuota.
Server e istanza restano predisposti; il nome database viene usato nel comando USE.

Comandi alternativi:

```bash
python leggi_ordini.py --config /percorso/config.json
python -m ordini_sql
python -m unittest discover -s tests -v
```

## Moduli

| Percorso | Responsabilità |
| --- | --- |
| `leggi_ordini.py` | Punto di avvio |
| `ordini_sql/cli.py` | Argomenti e messaggi |
| `ordini_sql/config.py` | Configurazione JSON |
| `ordini_sql/csv_reader.py` | Lettura CSV, intestazione esclusa |
| `ordini_sql/conversions.py` | Date, numeri, ore e stringhe SQL |
| `ordini_sql/service.py` | Validazione completa e file per riga |
| `ordini_sql/generators/ordini.py` | ORDINI |
| `ordini_sql/generators/tasks.py` | TASKS |
| `ordini_sql/generators/operazioni.py` | OPERAZIONI |
| `ordini_sql/generators/jobset.py` | JOBSET |
| `ordini_sql/generators/eventi.py` | Otto eventi MAC/OPE |
| `ordini_sql/generators/fprocessdata.py` | Campioni al minuto |
| `ordini_sql/generators/situazioni.py` | Quattro situazioni MAC/OPE |
| `tests/` | Verifica equivalenza con la versione precedente |

## Output e regole mantenute

Cartella `<nome_csv>_sql`, accanto al CSV. Nomi: `0001_<ORDINE>.sql`, ecc.
I file omonimi vengono sostituiti; eventuali vecchi file diversi non vengono eliminati.
Tutte le righe vengono validate prima di iniziare a scrivere gli SQL.
L'intestazione CSV è esclusa e la prima riga di dati viene elaborata.

Ordine delle query: ORDINI, TASKS, OPERAZIONI, JOBSET, eventi, FPROCESSDATA, situazioni.
Con il CSV incluso si generano tre file da 28 INSERT ciascuno.

- Tempi di lavoro TASKS/OPERAZIONI/JOBSET: VALORE01 / 60.
- FPROCESSDATA: VALORE01 campioni, da DATA_INIZIO + 1 minuto.
  Gli scostamenti rispetto a VALORE02 sono modificabili in `SCOSTAMENTI_FNVALUE01`
  nel modulo `generators/fprocessdata.py`.
- Situazioni: WSET da DATA_INIZIO a CHIUSURA_ATTREZZAGGIO; WORK da
  INIZIO_LAVORAZIONE a DATA_FINE. SETUP e LAVORO sono calcolati dagli orari effettivi.
- FINSDATE delle situazioni: DATA_INIZIO + 2 giorni mantenendo l'orario.
- Restano i controlli sui duplicati ORDINE/TASK e sui dati non validi.

I test confrontano gli SQL di esempio byte per byte con il riferimento verificato, aggiornato per le correzioni richieste. Non verificano lo schema di un database SQL Server reale.

Regola UTENTE negli eventi: CLS usa UTENTE_EVENTI del CSV; OPNS, CLSS e OPN usano il valore fisso WS, per MAC e OPE.

ORDINI.CLIENTE viene letto da CLIENTE nel CSV; se assente o vuoto viene scritto NULL. ORDINI.FAVOIDRSTPRIO resta NULL.

ORDINI.FALTPNUMBBUF vale 0 (testo); FPSTATUSALERT resta NULL. TASKS.CICLI_CONTATI legge VALORE01 direttamente.

Negli eventi, OGGETTO legge UTENTE_EVENTI per OPE e MACCHINA per MAC. La colonna MACCHINA resta sempre la macchina del CSV.

## Esecuzione sul database

`esegui_sql.py` è allo stesso livello di `leggi_ordini.py`; la logica di esecuzione è in `ordini_sql/executor.py`.

1. Installa Microsoft ODBC Driver 18 for SQL Server sul computer.
2. Esegui `python -m pip install -r requirements.txt`.
3. Compila i valori reali di `database` in `config.json`.
4. Genera gli SQL con `python leggi_ordini.py`.
5. Esegui `python esegui_sql.py`.

Il comando esegue realmente gli INSERT. Il config.json fornito predispone
l’autenticazione SQL; compila username e password. L’autenticazione Windows resta
disponibile impostando autenticazione a windows. Il driver deve essere installato separatamente da pyodbc.
Encrypt è true e trust_server_certificate è false; configura un certificato attendibile.
Su ambienti che richiedono esplicitamente di accettare il certificato del server puoi
impostare trust_server_certificate a true.

Per autenticazione SQL aggiungi/modifica nella sezione database:

```json
"autenticazione": "sql",
"username": "UTENTE_SQL",
"password": "LA_TUA_PASSWORD"
```

Username e password vengono letti direttamente da config.json.
Gli altri parametri (server_name, istanza, db, driver) restano invariati.
La stringa di connessione non viene stampata.

```bash
python esegui_sql.py --verifica
python esegui_sql.py --cartella /percorso/sql
python esegui_sql.py --file /percorso/0002_150124_F1.sql
python esegui_sql.py --config /percorso/config.json
```

Senza opzioni legge tutti i file `.sql` della cartella `<nome_csv>_sql`, in ordine di nome.
Controlla che la cartella non contenga SQL di precedenti generazioni che non vuoi eseguire.
`--verifica` controlla la struttura dei file e il database USE senza aprire connessioni;
non verifica vincoli, tabelle o validità SQL sul server.

Tutti i file selezionati appartengono a un'unica transazione: un solo commit dopo
l'ultimo file. In caso di errore o interruzione durante l'esecuzione, il rollback
annulla anche gli INSERT dei file precedenti di questo caricamento. Durante
l'esecuzione i file sono indicati come in attesa del commit finale.
Se il commit o il rollback non sono confermati viene segnalato l'esito incerto:
verificare sul database prima di riprovare. Il comando non ritenta automaticamente.
I caricamenti confermati in esecuzioni precedenti non vengono annullati.

Il separatore GO viene gestito dal programma e non inviato al server. Sono supportati
i file generati dal progetto (USE iniziale e batch INSERT). Il database USE deve
coincidere con config.json: se cambi database rigenera gli SQL.

Riferimenti: https://github.com/mkleehammer/pyodbc e
https://learn.microsoft.com/en-us/sql/connect/odbc/dsn-connection-string-attribute

## Campi setup derivati dal CSV

TEFF_SETUP_MAC nel CSV è espresso in ore. La durata da aggiungere agli orari è
`setup_secondi = int(TEFF_SETUP_MAC * 3600)`, arrotondata per difetto:
0.01389 ore diventano 50 secondi, 0.00750 ore diventano 27 secondi.

- TEFF_SETUP_MAN = TEFF_SETUP_MAC.
- CHIUSURA_ATTREZZAGGIO = DATA_INIZIO + setup_secondi, troncata al secondo inferiore.
- INIZIO_LAVORAZIONE = CHIUSURA_ATTREZZAGGIO + WSET_WORK secondi.
- DATA_FINE = INIZIO_LAVORAZIONE + VALORE01 minuti + setup_secondi, troncata al secondo inferiore.

CHIUSURA_ATTREZZAGGIO e DATA_FINE hanno sempre millesimi .000.
Esempio: DATA_INIZIO 09:03:00, setup 0.01389, WSET_WORK 5 e VALORE01 12
producono chiusura 09:03:50, inizio lavorazione 09:03:55 e fine 09:16:45.
Le durate devono essere non negative. I quattro campi derivati vengono ricalcolati
anche se presenti nei vecchi CSV; tutti i generatori ricevono la stessa riga completata.
DATA_UPD e le date programmate restano lette dal CSV.

Per situazioni con TIPO_OGGETTO MAC e PROGRESSIVO 2, LAVORO è la differenza
ORA_FINE - ORA_INIZIO in ore decimali. Attualmente WSET ha progressivo 1
(LAVORO zero), mentre WORK ha progressivo 2.

FPROCESSDATA viene generata esclusivamente per COD_CICLO da CYC_FORNO1 a CYC_FORNO7
(confronto senza distinzione di maiuscole, ignorando gli spazi esterni).
Gli altri cicli, incluso CYC_FORNI1, generano tutte le altre query ma nessuna
INSERT FPROCESSDATA; VALORE02 non è richiesto per questi cicli.

## Progressivi SITUAZIONI

Gli INSERT SITUAZIONI cercano in esecuzione il primo PROGRESSIVO positivo libero
(da 1 a 99999) per OGGETTO, TIPO_OGGETTO e DATA. I valori già inseriti nella stessa
transazione sono inclusi nella ricerca. UPDLOCK e HOLDLOCK proteggono la scelta
fino alla fine della transazione. Se i progressivi sono esauriti, il caricamento fallisce.
La fase WSET/WORK resta indipendente dal progressivo assegnato: LAVORO è zero per
WSET e la durata effettiva per WORK. Non viene saltata alcuna riga già esistente.
Rigenerare gli SQL con leggi_ordini.py e usare l'esecutore aggiornato.
È richiesta una transazione attiva; esegui_sql.py mantiene il commit unico finale.

## Quantità da CSV per cicli non forno

QTY_COMPLETATA e QTY_RICHIESTA sono obbligatorie, numeriche e non negative
per tutti i cicli eccetto CYC_FORNO1–CYC_FORNO7 (maiuscole e spazi ignorati).
Popolano rispettivamente QTA_COMPLETATA e QTA_RICHIESTA nei campi SQL esistenti:
ORDINI, OPERAZIONI e JOBSET ricevono entrambe; TASKS riceve QTA_RICHIESTA.
Negli EVENTI la completata viene assegnata solo a CLS; nelle SITUAZIONI solo
a WORK, mentre QTA_RICHIESTA viene assegnata anche a WSET.
I forni ignorano le due colonne e mantengono il comportamento precedente.
QTA_CONTATA è uguale a QTA_COMPLETATA in EVENTI e SITUAZIONI.
In TASKS QTA_CONTATA resta zero; in JOBSET resta NULL.
In ORDINI QTA_VERSATA è uguale a QTA_COMPLETATA.
Per SITUAZIONI WSET resta zero, per WORK usa QTY_COMPLETATA (sia MAC sia OPE).
In TASKS CICLI_CONTATI legge QTY_COMPLETATA dal CSV.
In ORDINI QTA_LANCIATA è uguale a QTA_RICHIESTA.
I tempi mantengono le regole precedenti legate a VALORE01.
MINIPAN: completata 150, richiesta 150. ALMA: completata 30, richiesta 60.
Le colonne nei CSV dei forni riportano zero, come gli SQL modello originali.

## Centro reale e quantità MINIPAN

In OPERAZIONI, CENTRO_REALE copia CENTRO_ASSEGNATO per tutti i cicli.
NUM_SPLIT è zero per CYC_MINIPAN e CYC_CASSETTEPANE, NULL per gli altri cicli.
Solo CYC_MINIPAN richiede QUANTITA1 e QUANTITA2 nel CSV (numeriche non negative).
Sono assegnate ai campi omonimi in ORDINI, OPERAZIONI e JOBSET;
in EVENTI solo a CLS e in SITUAZIONI solo a WORK, sia MAC sia OPE.
WSET mantiene le quantità a zero; gli altri eventi mantengono NULL.
TASKS: FVALUE01 copia QUANTITA01 se presente, altrimenti QUANTITA1; FVALUE02 resta invariato.
Il CSV MINIPAN incluso contiene 10 e 10, come le query di riferimento.

## Regole CASSETTEPANE

Solo per CYC_CASSETTEPANE (ignora maiuscole e spazi esterni):
- QTA_CICLO = 2 in TASKS, OPERAZIONI, EVENTI e SITUAZIONI.
- In TASKS, TOT_LAVORO_MAC e TOT_LAVORO_MAN sono la differenza
  DATA_FINE_PROG - DATA_INIZ_PROG in ore intere, arrotondate per difetto
  e scritte con cinque decimali (840,08333 ore diventa 840,00000).
  Si considera tutto l'intervallo, inclusi i giorni; nessuna esclusione di festivi.
- In TASKS, TOT_SETUP_MAC = TEFF_SETUP_MAC; TOT_SETUP_MAN resta invariato.
Le date programmate devono essere presenti e ordinate cronologicamente.

Solo per CYC_CASSETTEPANE, in OPERAZIONI QTA_SCARTATA e QTA_SOSPESA sono zero.

Per `CYC_CASSETTEPANE`, in EVENTI `QTA_CICLO` vale 2 solo per OPNS e OPN (MAC e OPE); per CLSS e CLS vale NULL. In SITUAZIONI vale 2 su tutte le righe WSET e WORK, sia MAC sia OPE.

Solo MINIPAN: TASKS TOT_SETUP_MAC/MAN = 0.08330 ore esatte. TOT_LAVORO_MAC/MAN = (DATA_FINE_PROG - DATA_INIZ_PROG) in ore meno il rispettivo setup, a cinque decimali. Intervalli inferiori al setup sono rifiutati. OPERAZIONI T_LAVORO_MAC/MAN copia il rispettivo TOT_SETUP di TASKS (0.08330).

Solo MINIPAN: anche OPERAZIONI T_SETUP_MAC e T_SETUP_MAN copiano rispettivamente TASKS TOT_SETUP_MAC e TOT_SETUP_MAN (0.08330 ore).
