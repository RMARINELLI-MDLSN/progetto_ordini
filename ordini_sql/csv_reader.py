"""Lettura CSV con separatore punto e virgola; intestazione esclusa."""

import csv
from pathlib import Path

def leggi_ordini(percorso):
    """Restituisce una riga alla volta come dizionario di stringhe.

    Usa le intestazioni originali, incluse UTENTE_UPD e UTENTE_TASK.
    Date e numeri restano stringhe, come nel file originale.
    """
    with Path(percorso).open(encoding="utf-8-sig", newline="") as file:
        lettore = csv.DictReader(file, delimiter=";", strict=True)
        if lettore.fieldnames is None:
            return
        if len(set(lettore.fieldnames)) != len(lettore.fieldnames):
            raise ValueError("Il CSV contiene intestazioni duplicate.")

        for riga in lettore:
            if None in riga or None in riga.values():
                raise ValueError(
                    f"Riga {lettore.line_num}: numero di colonne diverso "
                    "da quello delle intestazioni."
                )
            yield riga
