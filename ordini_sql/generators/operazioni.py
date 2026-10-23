"""Generazione INSERT per operazioni; valori e regole del modello originale."""

from ..tempi_previsti import SETUP_ORE
from .. import scrostatore
from ..quantita import applica_quantita
from ..conversions import sql_testo, sql_data, sql_numero, minuti_in_ore_sql

COLONNE_OPERAZIONI = """
ORDINE OPERAZIONE C_ESTERNO C_FIX_MAC C_FIX_MAN C_MACCHINA C_MANODOPERA CAUSALE
CEFF_ESTERNO CEFF_FIX_MAC CEFF_FIX_MAN CEFF_MACCHINA CEFF_MANODOPERA
CENTRO_ASSEGNATO CENTRO_REALE CODICE01 CODICE02 CODICE03 CODICE04 CODICE05 CRITICA
DATA_DOC DATA_EMISSIONE DATA_FINE DATA_FINE_PROG DATA_INIZ_PROG DATA_INIZIO
DATA_INS DATA_UPD DESCRIZIONE DESCRIZIONE01 DESCRIZIONE02 DESCRIZIONE03
DESCRIZIONE04 DESCRIZIONE05 FASE FPLDUEDATE FPLSTDATE ID_OPER LOCALE LOCK_PLAN
LOTTO MACCHINA_ASSEGNATA MODIFICATA NUM_OPERAI_LAVORO NUM_OPERAI_SETUP NUM_SPLIT
PRIORITA QTA_BASE QTA_CICLO QTA_CODA QTA_COMPLETATA QTA_IMPIEGO QTA_PRELEVATA
QTA_RECUPERATA QTA_RICHIESTA QTA_SCARTATA QTA_SOSPESA QUANTITA1 QUANTITA2
QUANTITA3 QUANTITA4 RESPONSABILE RIFERIMENTO SEQUENZA SPECIFICA STAMPATA STATO
STATO_CAPACITA T_LAVORO_MAC T_LAVORO_MAN T_PREVENTIVO T_SETUP_MAC T_SETUP_MAN
TEFF_GIUST_MAC TEFF_GIUST_MAN TEFF_LAVORO_MAC TEFF_LAVORO_MAN TEFF_SETUP_MAC
TEFF_SETUP_MAN TIPO TIPO_RIFERIMENTO TIPO_TEMPO TOT_SUPPL_MAC TOT_SUPPL_MAN
UTENTE_UPD VALORE01 VALORE02 VALORE03 VALORE04 VALORE05 MAGAZZINO STATO_MATERIALI
STATO_RITARDI FPROCEDURE FEVENT FTIMING FRATE FFREQUENCY T_FIX_MAC T_FIX_MAN
FPLSETDATE FPLWRKDATE SETUP1 SETUP2 SETUP3 SETUP4 FRFSTDATE FRFSETDATE FRFWRKDATE
FRFDUEDATE C_INDIRECT CEFF_INDIRECT FOPEALT TYPE_OVER QTA_OVERLAP FPERCPROG
FQUEUETIME FWAITTIME FMNGSTATUS FWRKCNTREF FWFL QTA_RILAVORATA FACTIVE FMINQTYSPL
FEXPORTDATE CENTRO_SUCCESSIVO VALORE06 VALORE07 VALORE08 VALORE09 VALORE10
SETUP5 SETUP6 SETUP7 FNATTACHMENT FNDESCS FALTFORCED FDAYCROSS FTMACSETBATCH
FTMACWRKBATCH FCNTPART FORIGMACWRKTIME FORIGMACSETTIME PWR_SETUP PWR_WORK
EFF_PWR_SETUP EFF_PWR_WORK EFF_PWR_IDLE CEFF_PWR_SETUP CEFF_PWR_WORK CEFF_PWR_IDLE
FCLOSINGEXPDATE FSEGMENT CODICE06 CODICE07 CODICE08 CODICE09 CODICE10
""".split()


TESTO_OPERAZIONI = {
    "ORDINE": "ORDINE", "OPERAZIONE": "OPERAZIONI",
    "CENTRO_ASSEGNATO": "CENTRO_ASSEGNATO", "ID_OPER": "TASK",
    "MACCHINA_ASSEGNATA": "MACCHINA",
}


DATE_OPERAZIONI = {
    "DATA_FINE": "DATA_FINE", "DATA_FINE_PROG": "DATA_FINE_PROG",
    "DATA_INIZ_PROG": "DATA_INIZ_PROG", "DATA_INIZIO": "DATA_INIZIO",
    "DATA_INS": "DATA_INS", "DATA_UPD": "DATA_UPD",
    "FPLDUEDATE": "FPLDUEDATA", "FPLSTDATE": "FPLSTDATE",
}


def costruisci_insert_operazioni(riga):
    """Mantiene il modello OPERAZIONI e sostituisce i soli campi richiesti.

    ID_OPER deriva da TASK; OPERAZIONE da OPERAZIONI; MACCHINA_ASSEGNATA
    da MACCHINA. CENTRO_REALE copia CENTRO_ASSEGNATO e UTENTE_UPD resta WS come nel modello.
    I tempi di lavoro derivano da VALORE01 / 60, come per TASKS.
    """
    richiesti = (list(TESTO_OPERAZIONI.values()) + list(DATE_OPERAZIONI.values())
                 + ["VALORE01", "TEFF_SETUP_MAC", "TEFF_SETUP_MAN"])
    mancanti = [c for c in richiesti if c not in riga]
    if mancanti:
        raise ValueError("Colonne CSV mancanti per OPERAZIONI: " + ", ".join(mancanti))
    for campo in ("ORDINE", "OPERAZIONI", "TASK"):
        if not riga[campo].strip():
            raise ValueError(f"{campo} non può essere vuoto per OPERAZIONI.")
    valori = dict.fromkeys(COLONNE_OPERAZIONI, "NULL")
    for campo in """C_ESTERNO CEFF_ESTERNO CEFF_FIX_MAC CEFF_FIX_MAN CEFF_MACCHINA
    CEFF_MANODOPERA QTA_CICLO QTA_COMPLETATA QTA_RICHIESTA QUANTITA1 QUANTITA2
    QUANTITA3 QUANTITA4 T_LAVORO_MAC T_LAVORO_MAN T_PREVENTIVO T_SETUP_MAC T_SETUP_MAN
    TEFF_GIUST_MAC TEFF_GIUST_MAN TOT_SUPPL_MAC TOT_SUPPL_MAN VALORE01 VALORE02
    VALORE03 VALORE04 VALORE05 T_FIX_MAC T_FIX_MAN CEFF_INDIRECT QTA_OVERLAP
    FQUEUETIME FWAITTIME""".split():
        valori[campo] = "CAST(0.00000 AS Numeric(15, 5))"
    valori["QTA_BASE"] = "CAST(1.00000 AS Numeric(15, 5))"
    valori["SEQUENZA"] = "CAST(10 AS Numeric(6, 0))"
    valori["FOPEALT"] = "CAST(0 AS Numeric(3, 0))"
    for campo in ("FNATTACHMENT", "FNDESCS", "FDAYCROSS"):
        valori[campo] = "CAST(0 AS Numeric(6, 0))"
    for campo in ("NUM_OPERAI_LAVORO", "NUM_OPERAI_SETUP"):
        valori[campo] = "CAST(0.00 AS Numeric(5, 2))"
    for campo, valore in {"LOCALE": "LOC", "STATO": "COM",
                          "TIPO": "WRK", "UTENTE_UPD": "WS", "TYPE_OVER": "P",
                          "FACTIVE": "Y", "FALTFORCED": "N"}.items():
        valori[campo] = sql_testo(valore)
    for mappa, converti in ((TESTO_OPERAZIONI, sql_testo), (DATE_OPERAZIONI, sql_data)):
        for destinazione, sorgente in mappa.items():
            valore = riga[sorgente]
            valori[destinazione] = converti(valore) if valore.strip() else "NULL"
    for campo in ("TEFF_SETUP_MAC", "TEFF_SETUP_MAN"):
        valore = riga[campo]
        valori[campo] = sql_numero(valore) if valore.strip() else "NULL"
    ore = minuti_in_ore_sql(riga["VALORE01"])
    valori["TEFF_LAVORO_MAC"] = ore
    valori["TEFF_LAVORO_MAN"] = ore
    valori["CENTRO_REALE"] = valori["CENTRO_ASSEGNATO"]
    valori["NUM_SPLIT"] = "CAST(0 AS Numeric(6, 0))" if riga["COD_CICLO"].strip().upper() in {"CYC_MINIPAN", "CYC_CASSETTEPANE"} else "NULL"
    if riga["COD_CICLO"].strip().upper() == "CYC_CASSETTEPANE":
        valori["QTA_SCARTATA"] = sql_numero("0")
        valori["QTA_SOSPESA"] = sql_numero("0")
    if riga["COD_CICLO"].strip().upper() in {"CYC_MINIPAN", "CYC_CASSETTEPANE"}:
        valori["T_LAVORO_MAC"] = sql_numero(str(SETUP_ORE))
        valori["T_LAVORO_MAN"] = sql_numero(str(SETUP_ORE))
        valori["T_SETUP_MAC"] = sql_numero(str(SETUP_ORE))
        valori["T_SETUP_MAN"] = sql_numero(str(SETUP_ORE))
    if riga["COD_CICLO"].strip().upper() == "CYC_CASSETTEPANE":
        valori["T_LAVORO_MAC"] = sql_numero("0.5")
        valori["T_LAVORO_MAN"] = sql_numero("0.5")
    applica_quantita(valori, riga)
    if scrostatore.attivo(riga):
        valori['NUM_SPLIT'] = 'CAST(0 AS Numeric(6, 0))'
        valori['DATA_UPD'] = sql_data(riga['DATA_FINE'])
        for risorsa in ('MAC', 'MAN'):
            valori['T_LAVORO_'+risorsa] = sql_numero(str(scrostatore.numero(riga, 'TEMPO_UNITARIO_PREVISTO', '0.16670')))
            valori['T_SETUP_'+risorsa] = sql_numero(str(scrostatore.numero(riga, 'SETUP_PREVISTO', '0.16670')))
    nomi = ", ".join(f"[{c}]" for c in COLONNE_OPERAZIONI)
    dati = ",\n    ".join(valori[c] for c in COLONNE_OPERAZIONI)
    return f"INSERT [dbo].[OPERAZIONI] ({nomi})\nVALUES (\n    {dati}\n);\nGO\n"
