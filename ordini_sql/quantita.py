"""Quantità di produzione dei cicli diversi da CYC_FORNO1–7."""
from .conversions import durata_non_negativa, sql_numero


def applica_quantita(valori, riga, completata=True, aggiorna_contata=True):
    ciclo = riga.get('COD_CICLO', '').strip().upper()
    if not ciclo:
        raise ValueError('COD_CICLO è obbligatorio per gestire le quantità.')
    if ciclo in {f'CYC_FORNO{i}' for i in range(1, 8)}:
        return
    for sorgente, destinazione in (('QTY_COMPLETATA', 'QTA_COMPLETATA'),
                                   ('QTY_RICHIESTA', 'QTA_RICHIESTA')):
        valore = riga.get(sorgente, '').strip()
        if not valore:
            raise ValueError(f'{sorgente} è obbligatoria per il ciclo {ciclo}.')
        numero = durata_non_negativa(valore, sorgente)
        sql = sql_numero(str(numero))
        if destinazione in valori and (destinazione != 'QTA_COMPLETATA' or completata):
            valori[destinazione] = sql
    if 'QTA_VERSATA' in valori and 'QTA_COMPLETATA' in valori:
        valori['QTA_VERSATA'] = valori['QTA_COMPLETATA']
    if aggiorna_contata and 'QTA_CONTATA' in valori and 'QTA_COMPLETATA' in valori:
        valori['QTA_CONTATA'] = valori['QTA_COMPLETATA']
    if 'QTA_LANCIATA' in valori and 'QTA_RICHIESTA' in valori:
        valori['QTA_LANCIATA'] = valori['QTA_RICHIESTA']
    if 'CICLI_CONTATI' in valori:
        valori['CICLI_CONTATI'] = sql_numero(riga['QTY_COMPLETATA'])
    if ciclo == 'CYC_MINIPAN':
        for campo in ('QUANTITA1', 'QUANTITA2'):
            valore = riga.get(campo, '').strip()
            if not valore:
                raise ValueError(f'{campo} è obbligatoria per CYC_MINIPAN.')
            numero = durata_non_negativa(valore, campo)
            sql = sql_numero(str(numero))
            # Come la completata, registrare le quantità solo nella fase produttiva.
            if campo in valori and completata:
                valori[campo] = sql
    if ciclo == 'CYC_CASSETTEPANE' and 'QTA_CICLO' in valori:
        valori['QTA_CICLO'] = sql_numero('2')
