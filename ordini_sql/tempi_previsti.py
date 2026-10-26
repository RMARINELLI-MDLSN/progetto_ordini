"""Tempi previsti da intervallo pianificato e quantità, esclusi i forni."""
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP, ROUND_DOWN
from .conversions import durata_non_negativa, sql_data, sql_numero

SETUP_ORE = Decimal("0.08330")
CICLI = {'CYC_MINIPAN', 'CYC_CASSETTEPANE', 'CIC_SCROSTATORE', 'CYC_BSTRAM', 'CYC_ALMA'}


def attivo(riga):
    return riga.get('COD_CICLO', '').strip().upper() in CICLI


def setup_previsto(riga):
    if riga.get('COD_CICLO', '').strip().upper() == 'CIC_SCROSTATORE':
        valore = durata_non_negativa(riga.get('SETUP_PREVISTO', '0.16670'), 'SETUP_PREVISTO')
        sql_numero(str(valore))
        return valore
    return SETUP_ORE


def lavoro_esatto(riga):
    for campo in ('DATA_INIZ_PROG', 'DATA_FINE_PROG'):
        if not riga.get(campo, '').strip():
            raise ValueError(f'{campo} obbligatoria per i tempi pianificati.')
        sql_data(riga[campo])
    inizio = datetime.fromisoformat(riga['DATA_INIZ_PROG'].strip())
    fine = datetime.fromisoformat(riga['DATA_FINE_PROG'].strip())
    delta = fine - inizio
    microsecondi = (delta.days * 86400 + delta.seconds) * 1000000 + delta.microseconds
    lavoro = Decimal(microsecondi) / Decimal('3600000000') - setup_previsto(riga)
    if lavoro < 0:
        raise ValueError(f"{riga.get('COD_CICLO', '').strip().upper()}: intervallo pianificato inferiore al tempo di setup.")
    return lavoro


def lavoro_pianificato(riga):
    return lavoro_esatto(riga).quantize(Decimal('0.00001'), rounding=ROUND_HALF_UP)


def tempo_unitario(riga):
    quantita = durata_non_negativa(riga.get('QTY_RICHIESTA', ''), 'QTY_RICHIESTA')
    if quantita <= 0:
        raise ValueError('QTY_RICHIESTA deve essere maggiore di zero per il tempo unitario.')
    # Dividere la durata esatta evita che un arrotondamento intermedio superi il budget.
    return (lavoro_esatto(riga) / quantita).quantize(Decimal('0.00001'), rounding=ROUND_DOWN)
