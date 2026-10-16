"""Coordina i generatori e scrive un file SQL per riga CSV."""

import re
from .csv_reader import leggi_ordini
from .generators.ordini import costruisci_insert
from .generators.tasks import costruisci_insert_tasks
from .generators.operazioni import costruisci_insert_operazioni
from .generators.jobset import costruisci_insert_jobset
from .generators.eventi import costruisci_insert_eventi
from .generators.fprocessdata import costruisci_insert_fprocessdata
from .generators.situazioni import costruisci_insert_situazioni


def genera_script(config):
    percorso_csv = config["file_csv"]
    cartella = percorso_csv.parent / (percorso_csv.stem + "_sql")
    file_preparati = []
    ordini = set()
    tasks = set()
    for numero, riga in enumerate(leggi_ordini(percorso_csv), start=1):
        istruzioni = []
        try:
            istruzione = costruisci_insert(riga)
            istruzione_task = costruisci_insert_tasks(riga)
            istruzione_operazione = costruisci_insert_operazioni(riga)
            istruzione_jobset = costruisci_insert_jobset(riga)
            istruzioni_eventi = costruisci_insert_eventi(riga)
            if riga["TASK"] in tasks:
                raise ValueError(f"TASK duplicato nel CSV: {riga['TASK']}")
            tasks.add(riga["TASK"])
            if riga["ORDINE"] in ordini:
                raise ValueError(f"ORDINE duplicato nel CSV: {riga['ORDINE']}")
            ordini.add(riga["ORDINE"])
            istruzioni.extend((istruzione, istruzione_task, istruzione_operazione, istruzione_jobset))
            istruzioni.extend(istruzioni_eventi)
            istruzioni.extend(costruisci_insert_fprocessdata(riga))
            istruzioni.extend(costruisci_insert_situazioni(riga))
            # Prefisso numerico univoco e nome compatibile anche con Windows.
            codice = re.sub(r"[^A-Za-z0-9_-]+", "_", riga["ORDINE"]).strip("_")[:100] or "ordine"
            destinazione = cartella / f"{numero:04d}_{codice}.sql"
            file_preparati.append((destinazione, "\n".join(istruzioni), len(istruzioni)))
        except ValueError as errore:
            raise ValueError(f"Record CSV {numero}: {errore}") from errore
    if not file_preparati:
        raise ValueError("Il CSV non contiene righe di dati.")
    database = config["database"]["db"].replace("]", "]]")
    intestazione = (
        "-- Script generato dal CSV; nessuna query eseguita dal programma.\n"
        "-- INSERT semplici: una nuova esecuzione può produrre duplicati o errori di chiave.\n"
        f"USE [{database}];\nGO\n\n"
    )
    # Scrive i file separati solo dopo aver validato tutte le righe.
    cartella.mkdir(parents=True, exist_ok=True)
    risultati = []
    for destinazione, contenuto, conteggio in file_preparati:
        destinazione.write_text(intestazione + contenuto, encoding="utf-8-sig")
        risultati.append((destinazione, conteggio))
    return risultati
