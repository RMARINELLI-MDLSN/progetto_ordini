"""Tempi pianificati MINIPAN espressi in ore decimali."""
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

SETUP_ORE = Decimal("0.08330")


def lavoro_pianificato(riga):
    inizio = datetime.fromisoformat(riga["DATA_INIZ_PROG"].strip())
    fine = datetime.fromisoformat(riga["DATA_FINE_PROG"].strip())
    delta = fine - inizio
    microsecondi = (delta.days * 86400 + delta.seconds) * 1000000 + delta.microseconds
    lavoro = Decimal(microsecondi) / Decimal("3600000000") - SETUP_ORE
    if lavoro < 0:
        raise ValueError("MINIPAN: intervallo pianificato inferiore al tempo di setup.")
    return lavoro.quantize(Decimal("0.00001"), rounding=ROUND_HALF_UP)
