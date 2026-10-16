"""Lettura e validazione della configurazione JSON."""

import json
from pathlib import Path

def carica_config(percorso):
    """Legge SQL Server e CSV; i percorsi relativi partono dalla configurazione.

    Per l'istanza predefinita usare una stringa vuota in database.istanza.
    Questa funzione prepara i parametri ma non apre una connessione SQL.
    """
    percorso = Path(percorso).resolve()
    with percorso.open(encoding="utf-8-sig") as file:
        config = json.load(file)
    if not isinstance(config, dict):
        raise ValueError("La configurazione deve essere un oggetto JSON.")
    database = config.get("database")
    if not isinstance(database, dict):
        raise ValueError("Manca la sezione database nella configurazione.")
    for campo in ("server_name", "db"):
        if not isinstance(database.get(campo), str) or not database[campo].strip():
            raise ValueError(f"database.{campo} deve essere una stringa non vuota.")
    if not isinstance(database.get("istanza"), str):
        raise ValueError("database.istanza deve essere una stringa (anche vuota).")
    if not isinstance(config.get("file_csv"), str) or not config["file_csv"].strip():
        raise ValueError("file_csv deve contenere il nome o percorso del CSV.")

    server = database["server_name"].strip()
    istanza = database["istanza"].strip()
    database["server"] = f"{server}\\{istanza}" if istanza else server
    csv_path = Path(config["file_csv"])
    if not csv_path.is_absolute():
        csv_path = percorso.parent / csv_path
    config["file_csv"] = csv_path
    return config
