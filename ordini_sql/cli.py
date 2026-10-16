"""Interfaccia da riga di comando."""

import argparse
import csv
from pathlib import Path
from .config import carica_config
from .service import genera_script

def main():
    parser = argparse.ArgumentParser(description="Genera gli INSERT ORDINI, TASKS, OPERAZIONI, JOBSET, eventi, FPROCESSDATA e situazioni dal CSV.")
    parser.add_argument("--config", type=Path,
                        default=Path(__file__).resolve().parent.parent / "config.json",
                        help="Percorso del file di configurazione JSON")
    argomenti = parser.parse_args()
    try:
        risultati = genera_script(carica_config(argomenti.config))
    except (OSError, UnicodeError, csv.Error, ValueError) as errore:
        parser.exit(1, f"Errore: {errore}\n")
    for destinazione, conteggio in risultati:
        print(f"Creato: {destinazione} ({conteggio} INSERT).")
    totale = sum(conteggio for _, conteggio in risultati)
    print(f"Creati {len(risultati)} file SQL, {totale} INSERT totali. Nessuna query eseguita.")
