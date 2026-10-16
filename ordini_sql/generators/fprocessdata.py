"""Generazione INSERT per fprocessdata; valori e regole del modello originale."""

from ..conversions import sql_testo, sql_data, sql_numero, minuti_in_ore_sql
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

COLONNE_FPROCESSDATA = ['FOBJECT', 'FOBJTYPE', 'FCHANNEL', 'FTIMESTAMP', 'FROW', 'FBATCH', 'FSTATUS', 'FVALUE01', 'FVALUE02', 'FVALUE03', 'FVALUE04', 'FVALUE05', 'FVALUE06', 'FVALUE07', 'FVALUE08', 'FVALUE09', 'FVALUE10', 'FVALUE11', 'FVALUE12', 'FVALUE13', 'FVALUE14', 'FVALUE15', 'FVALUE16', 'FVALUE17', 'FVALUE18', 'FVALUE19', 'FVALUE20', 'FVALUE21', 'FVALUE22', 'FVALUE23', 'FVALUE24', 'FVALUE25', 'FVALUE26', 'FVALUE27', 'FVALUE28', 'FVALUE29', 'FVALUE30', 'FVALUE31', 'FVALUE32', 'FVALUE33', 'FVALUE34', 'FVALUE35', 'FVALUE36', 'FVALUE37', 'FVALUE38', 'FVALUE39', 'FVALUE40', 'FVALUE41', 'FVALUE42', 'FVALUE43', 'FVALUE44', 'FVALUE45', 'FVALUE46', 'FVALUE47', 'FVALUE48', 'FVALUE49', 'FVALUE50', 'FVALUE51', 'FVALUE52', 'FVALUE53', 'FVALUE54', 'FVALUE55', 'FVALUE56', 'FVALUE57', 'FVALUE58', 'FVALUE59', 'FVALUE60', 'FVALUE61', 'FVALUE62', 'FVALUE63', 'FVALUE64', 'FVALUE65', 'FVALUE66', 'FVALUE67', 'FVALUE68', 'FVALUE69', 'FVALUE70', 'FVALUE71', 'FVALUE72', 'FVALUE73', 'FVALUE74', 'FVALUE75', 'FVALUE76', 'FVALUE77', 'FVALUE78', 'FVALUE79', 'FVALUE80', 'FVALUE81', 'FVALUE82', 'FVALUE83', 'FVALUE84', 'FVALUE85', 'FVALUE86', 'FVALUE87', 'FVALUE88', 'FVALUE89', 'FVALUE90', 'FOPERATOR', 'FMACHINE', 'FVALUE91', 'FVALUE92', 'FVALUE93', 'FVALUE94', 'FVALUE95', 'FVALUE96', 'FVALUE97', 'FVALUE98', 'FVALUE99', 'FVALUE100', 'FTASK', 'FNVALUE01', 'FNVALUE02', 'FNVALUE03', 'FNVALUE04', 'FNVALUE05', 'FNVALUE06', 'FNVALUE07', 'FNVALUE08', 'FNVALUE09', 'FNVALUE10', 'FNVALUE11', 'FNVALUE12', 'FNVALUE13', 'FNVALUE14', 'FNVALUE15', 'FNVALUE16', 'FNVALUE17', 'FNVALUE18', 'FNVALUE19', 'FNVALUE20', 'FCALCTIME', 'FNVALUE21', 'FNVALUE22', 'FNVALUE23', 'FNVALUE24', 'FNVALUE25', 'FNVALUE26', 'FNVALUE27', 'FNVALUE28', 'FNVALUE29', 'FNVALUE30', 'FNVALUE31', 'FNVALUE32', 'FNVALUE33', 'FNVALUE34', 'FNVALUE35', 'FNVALUE36', 'FNVALUE37', 'FNVALUE38', 'FNVALUE39', 'FNVALUE40', 'FNVALUE41', 'FNVALUE42', 'FNVALUE43', 'FNVALUE44', 'FNVALUE45', 'FNVALUE46', 'FNVALUE47', 'FNVALUE48', 'FNVALUE49', 'FNVALUE50', 'FNVALUE51', 'FNVALUE52', 'FNVALUE53', 'FNVALUE54', 'FNVALUE55', 'FNVALUE56', 'FNVALUE57', 'FNVALUE58', 'FNVALUE59', 'FNVALUE60', 'FNVALUE61', 'FNVALUE62', 'FNVALUE63', 'FNVALUE64', 'FNVALUE65', 'FNVALUE66', 'FNVALUE67', 'FNVALUE68', 'FNVALUE69', 'FNVALUE70', 'FNVALUE71', 'FNVALUE72', 'FNVALUE73', 'FNVALUE74', 'FNVALUE75', 'FNVALUE76', 'FNVALUE77', 'FNVALUE78', 'FNVALUE79', 'FNVALUE80', 'FNVALUE81', 'FNVALUE82', 'FNVALUE83', 'FNVALUE84', 'FNVALUE85', 'FNVALUE86', 'FNVALUE87', 'FNVALUE88', 'FNVALUE89', 'FNVALUE90', 'FNVALUE91', 'FNVALUE92', 'FNVALUE93', 'FNVALUE94', 'FNVALUE95', 'FNVALUE96', 'FNVALUE97', 'FNVALUE98', 'FNVALUE99', 'FNVALUE100', 'FCHARTSTATUS']


DEFAULT_FPROCESSDATA = {'FOBJTYPE': "N'MAC'", 'FCHANNEL': "N'HIST'", 'FROW': 'CAST(0 AS Numeric(6, 0))', 'FSTATUS': "N'REL'"}


SCOSTAMENTI_FNVALUE01 = (3, 2, -1, -2, 6, 7, 5, 3, 0, -2, 6, 6)


def costruisci_insert_fprocessdata(riga):
    """Genera VALORE01 campioni, uno al minuto, da DATA_INIZIO + 1 minuto.

    VALORE01 deve essere un intero non negativo (zero genera zero campioni).
    FNVALUE02 va da 0 a VALORE01-1. FNVALUE01 oscilla attorno a VALORE02
    usando gli scostamenti ciclici sopra. Mantiene tutte le 212 colonne.
    """
    richiesti = {"MACCHINA", "TASK", "VALORE01", "VALORE02", "DATA_INIZIO"}
    mancanti = sorted(richiesti - riga.keys())
    if mancanti:
        raise ValueError("Colonne CSV mancanti per FPROCESSDATA: " + ", ".join(mancanti))
    for campo in richiesti:
        if not riga[campo].strip():
            raise ValueError(f"{campo} non può essere vuoto per FPROCESSDATA.")
    try:
        numero = Decimal(riga["VALORE01"].strip().replace(",", "."))
        if not numero.is_finite() or numero < 0 or numero != numero.to_integral_value():
            raise ValueError("VALORE01 deve essere un intero non negativo per FPROCESSDATA.")
        # Valida anche il tipo Numeric(15, 5) dei valori generati.
        sql_numero(riga["VALORE02"])
        base = Decimal(riga["VALORE02"].strip().replace(",", "."))
    except InvalidOperation as errore:
        raise ValueError("VALORE01 o VALORE02 non numerico per FPROCESSDATA.") from errore
    sql_data(riga["DATA_INIZIO"])
    inizio = datetime.fromisoformat(riga["DATA_INIZIO"].strip())
    numero = int(numero)
    try:
        sql_data((inizio + timedelta(minutes=numero)).isoformat())
    except (OverflowError, ValueError) as errore:
        raise ValueError("Intervallo temporale FPROCESSDATA fuori dai limiti DateTime.") from errore
    if not SCOSTAMENTI_FNVALUE01:
        raise ValueError("La sequenza SCOSTAMENTI_FNVALUE01 non può essere vuota.")
    nomi = ", ".join(f"[{c}]" for c in COLONNE_FPROCESSDATA)
    for indice in range(numero):
        valori = dict.fromkeys(COLONNE_FPROCESSDATA, "NULL")
        valori.update(DEFAULT_FPROCESSDATA)
        valori["FOBJECT"] = sql_testo(riga["MACCHINA"])
        valori["FMACHINE"] = sql_testo(riga["MACCHINA"])
        valori["FBATCH"] = sql_testo(riga["TASK"])
        timestamp = inizio + timedelta(minutes=indice + 1)
        valori["FTIMESTAMP"] = sql_data(timestamp.isoformat(timespec="milliseconds"))
        scostamento = Decimal(str(SCOSTAMENTI_FNVALUE01[indice % len(SCOSTAMENTI_FNVALUE01)]))
        valori["FNVALUE01"] = sql_numero(str(base + scostamento))
        valori["FNVALUE02"] = sql_numero(str(indice))
        dati = ",\n    ".join(valori[c] for c in COLONNE_FPROCESSDATA)
        yield f"INSERT [dbo].[FPROCESSDATA] ({nomi})\nVALUES (\n    {dati}\n);\nGO\n"
