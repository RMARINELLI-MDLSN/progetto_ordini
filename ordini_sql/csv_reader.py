"""Lettura CSV con separatore punto e virgola; intestazione esclusa."""

from .scrostatore import attivo, valida
from . import tempi_previsti
import csv
from pathlib import Path
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from .conversions import sql_data, sql_numero, durata_non_negativa

def leggi_ordini(percorso):
    """Restituisce una riga alla volta come dizionario di stringhe.

    Usa le intestazioni originali, incluse UTENTE_UPD e UTENTE_TASK.
    Date e numeri restano stringhe. TEFF_SETUP_MAN, CHIUSURA_ATTREZZAGGIO
    INIZIO_LAVORAZIONE e DATA_FINE vengono sempre calcolati da TEFF_SETUP_MAC,
    DATA_INIZIO, WSET_WORK e VALORE01, anche se presenti nei vecchi CSV.
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
            try:
                yield completa_setup(riga)
            except (ValueError, InvalidOperation, OverflowError) as errore:
                raise ValueError(f"Riga CSV {lettore.line_num}: {errore}") from errore


def completa_setup(riga):
    """Deriva i campi rimossi dal CSV; TEFF_SETUP_MAC è espresso in ore.

    CHIUSURA_ATTREZZAGGIO è arrotondata al secondo inferiore.
    INIZIO_LAVORAZIONE = CHIUSURA_ATTREZZAGGIO + WSET_WORK secondi.
    setup_secondi = int(TEFF_SETUP_MAC * 3600), arrotondato per difetto.
    DATA_FINE = INIZIO_LAVORAZIONE + VALORE01 minuti + setup_secondi.
    Solo CIC_SCROSTATORE omette setup_secondi dal calcolo della fine.
    CHIUSURA_ATTREZZAGGIO e DATA_FINE hanno sempre millesimi .000.
    Le colonne derivate eventualmente presenti nei vecchi CSV sono ignorate.
    """
    risultato = dict(riga)
    for campo in ("TEFF_SETUP_MAC", "DATA_INIZIO", "WSET_WORK", "VALORE01"):
        if campo not in risultato or not risultato[campo].strip():
            raise ValueError(f"{campo} è obbligatorio per calcolare il setup.")
    ore = durata_non_negativa(risultato["TEFF_SETUP_MAC"], "TEFF_SETUP_MAC")
    sql_numero(str(ore))
    sql_data(risultato["DATA_INIZIO"])
    inizio = datetime.fromisoformat(risultato["DATA_INIZIO"].strip())
    setup_secondi = int(ore * Decimal("3600"))
    chiusura = inizio + timedelta(seconds=setup_secondi)
    chiusura = chiusura.replace(microsecond=0)
    risultato["TEFF_SETUP_MAN"] = risultato["TEFF_SETUP_MAC"]
    risultato["CHIUSURA_ATTREZZAGGIO"] = chiusura.isoformat(sep=" ", timespec="milliseconds")
    pausa = durata_non_negativa(risultato["WSET_WORK"], "WSET_WORK")
    pausa_ms = int((pausa * Decimal("1000")).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    inizio_lavorazione = chiusura + timedelta(milliseconds=pausa_ms)
    risultato["INIZIO_LAVORAZIONE"] = inizio_lavorazione.isoformat(sep=" ", timespec="milliseconds")
    minuti = durata_non_negativa(risultato["VALORE01"], "VALORE01")
    durata_ms = int((minuti * Decimal("60000")).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    fine = inizio_lavorazione + timedelta(milliseconds=durata_ms, seconds=0 if attivo(risultato) else setup_secondi)
    fine = fine.replace(microsecond=0)
    if tempi_previsti.attivo(risultato) and minuti == 0:
        if not risultato.get('DATA_FINE_PROG', '').strip():
            raise ValueError('DATA_FINE_PROG obbligatoria quando VALORE01 = 0.')
        sql_data(risultato['DATA_FINE_PROG'])
        fine = (datetime.fromisoformat(risultato['DATA_FINE_PROG'].strip()) - timedelta(seconds=1)).replace(microsecond=0)
        if fine <= inizio_lavorazione:
            raise ValueError('DATA_FINE_PROG non lascia spazio per una fine successiva a INIZIO_LAVORAZIONE.')
    risultato["DATA_FINE"] = fine.isoformat(sep=" ", timespec="milliseconds")
    if attivo(risultato):
        # Il CSV standard non distingue la quantità contata dalla completata.
        risultato.setdefault('QTY_CONTATA', risultato.get('QTY_COMPLETATA', ''))
        valida(risultato)
    return risultato
