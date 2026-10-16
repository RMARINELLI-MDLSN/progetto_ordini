# Generatore SQL ordini

Generatore Python senza dipendenze esterne. L’esecutore SQL richiede pyodbc e un driver ODBC SQL Server. Richiede Python 3.9 o successivo.
Genera un SQL per riga CSV; non si connette al database e non esegue query.

## Avvio

1. Estrai tutto il progetto e apri un terminale nella cartella estratta.
2. Modifica `config.json`: server, istanza, nome database e `file_csv`.
3. Esegui `python leggi_ordini.py`.

Il config.json punta al nuovo CSV Ordini_Alba_Tramezzini_CLIENTE.csv, incluso nel progetto. Il precedente CSV con tre ordini resta come riferimento per i test.
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

Un file corrisponde a una transazione. Tutti i suoi INSERT vengono confermati insieme;
in caso di errore viene eseguito il rollback e l'esecuzione si ferma. I file precedenti
rimangono confermati. Se il commit o il rollback non sono confermati viene segnalato
l'esito incerto: verificare sul database prima di riprovare. Il comando non ritenta
automaticamente e non evita duplicati: non rilanciare i file già importati.

Il separatore GO viene gestito dal programma e non inviato al server. Sono supportati
i file generati dal progetto (USE iniziale e batch INSERT). Il database USE deve
coincidere con config.json: se cambi database rigenera gli SQL.

Riferimenti: https://github.com/mkleehammer/pyodbc e
https://learn.microsoft.com/en-us/sql/connect/odbc/dsn-connection-string-attribute
