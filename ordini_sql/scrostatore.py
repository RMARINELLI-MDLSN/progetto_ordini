"""Regole del ciclo CIC_SCROSTATORE, dal modello GASPERINI."""
from datetime import datetime
from decimal import Decimal
from .conversions import durata_non_negativa, sql_numero, sql_data


def attivo(riga):
    return riga.get('COD_CICLO', '').strip().upper() == 'CIC_SCROSTATORE'


def numero(riga, campo, default=None):
    testo = riga.get(campo, str(default) if default is not None else '').strip()
    if not testo:
        raise ValueError(f'{campo} obbligatorio per CIC_SCROSTATORE.')
    valore = durata_non_negativa(testo, campo)
    sql_numero(str(valore))
    return valore


def valida(riga):
    contata = numero(riga, 'QTY_CONTATA')
    completata = numero(riga, 'QTY_COMPLETATA')
    numero(riga, 'SETUP_PREVISTO', '0.16670')
    if riga.get('DATA_EVENTO_UPD', '').strip():
        sql_data(riga['DATA_EVENTO_UPD'])
        if not (datetime.fromisoformat(riga['INIZIO_LAVORAZIONE']) < datetime.fromisoformat(riga['DATA_EVENTO_UPD']) < datetime.fromisoformat(riga['DATA_FINE'])):
            raise ValueError('DATA_EVENTO_UPD deve essere tra INIZIO_LAVORAZIONE e DATA_FINE.')
        if numero(riga, 'QTY_CONTATA_UPD') > contata:
            raise ValueError('QTY_CONTATA_UPD supera QTY_CONTATA.')
        if numero(riga, 'QTY_COMPLETATA_UPD') > completata:
            raise ValueError('QTY_COMPLETATA_UPD supera QTY_COMPLETATA.')
    for campo in ('FINSDATE_MAC', 'FINSDATE_OPE'):
        if riga.get(campo, '').strip():
            sql_data(riga[campo])


def quantita_fase(riga, fase):
    """Quantità incrementali per UPD e chiusura, senza duplicare i totali."""
    if fase == 'WSET':
        return Decimal(0), Decimal(0)
    c = numero(riga, 'QTY_COMPLETATA')
    q = numero(riga, 'QTY_CONTATA')
    if riga.get('DATA_EVENTO_UPD', '').strip():
        cu = numero(riga, 'QTY_COMPLETATA_UPD')
        qu = numero(riga, 'QTY_CONTATA_UPD')
        return (cu, qu) if fase == 'UPD' else (c-cu, q-qu)
    return c, q


def applica_totali_task(valori, riga):
    valori['CICLI_CONTATI'] = sql_numero(str(numero(riga, 'QTY_CONTATA')))
