"""Conversioni, durate e formattazione sicura dei valori SQL."""

from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

def sql_testo(valore):
    """Protegge gli apostrofi nei valori Unicode SQL Server."""
    return "N'" + valore.replace("'", "''") + "'"


def sql_data(valore):
    try:
        data = datetime.fromisoformat(valore.strip())
    except ValueError as errore:
        raise ValueError(f"Data non valida: {valore!r}") from errore
    if data.tzinfo is not None or data.year < 1753:
        raise ValueError(f"Data incompatibile con SQL DateTime: {valore!r}")
    return "CAST(" + sql_testo(data.isoformat(timespec="milliseconds")) + " AS DateTime)"


def sql_numero(valore):
    """Converte un numero CSV in Numeric(15, 5), senza arrotondamenti impliciti."""
    try:
        numero = Decimal(valore.strip().replace(",", "."))
        if not numero.is_finite() or abs(numero) >= Decimal("10000000000"):
            raise ValueError(f"Numero fuori intervallo: {valore!r}")
        if numero != numero.quantize(Decimal("0.00001")):
            raise ValueError(f"Numero con oltre 5 decimali: {valore!r}")
    except InvalidOperation as errore:
        raise ValueError(f"Numero non valido: {valore!r}") from errore
    return f"CAST({numero:.5f} AS Numeric(15, 5))"


def minuti_in_ore_sql(valore):
    """Converte minuti in ore decimali, arrotondando a 5 cifre (half up).

    Come per gli altri campi CSV, un valore vuoto produce NULL.
    """
    if not valore.strip():
        return "NULL"
    try:
        minuti = Decimal(valore.strip().replace(",", "."))
        if not minuti.is_finite() or minuti < 0 or minuti >= Decimal("600000000000"):
            raise ValueError(f"VALORE01 non valido come durata in minuti: {valore!r}")
        ore = (minuti / Decimal("60")).quantize(Decimal("0.00001"), rounding=ROUND_HALF_UP)
    except InvalidOperation as errore:
        raise ValueError(f"VALORE01 non valido come durata in minuti: {valore!r}") from errore
    return sql_numero(str(ore))


def durata_non_negativa(valore, campo):
    try:
        numero = Decimal(valore.strip().replace(",", "."))
    except InvalidOperation as errore:
        raise ValueError(f"{campo} non numerico: {valore!r}") from errore
    if not numero.is_finite() or numero < 0:
        raise ValueError(f"{campo} deve essere un numero non negativo.")
    return numero


def ore_da_intervallo(inizio, fine):
    """Ore decimali effettive fra due date, arrotondate a cinque decimali."""
    intervallo = fine - inizio
    if intervallo < timedelta(0):
        raise ValueError("ORA_FINE precede ORA_INIZIO nella situazione.")
    microsecondi = ((intervallo.days * 86400 + intervallo.seconds) * 1000000
                    + intervallo.microseconds)
    ore = (Decimal(microsecondi) / Decimal("3600000000")).quantize(
        Decimal("0.00001"), rounding=ROUND_HALF_UP)
    return sql_numero(str(ore))
