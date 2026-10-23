"""Generazione INSERT per ordini; valori e regole del modello originale."""

from .. import scrostatore
from ..quantita import applica_quantita
from ..conversions import sql_testo, sql_data, sql_numero, minuti_in_ore_sql

COLONNE = """
ORDINE ALT_CICLO AZIENDA C_ESTERNO C_FIX_MAC C_FIX_MAN C_MACCHINA C_MANODOPERA
C_MATERIALE C_RECUPERO CARATTERISTICA1 CARATTERISTICA2 CARATTERISTICA3
CARATTERISTICA4 CARATTERISTICA5 CAUSALE CEFF_ESTERNO CEFF_FIX_MAC CEFF_FIX_MAN
CEFF_MACCHINA CEFF_MANODOPERA CEFF_MATERIALE CLASSE CLAV_CRITICO CLIENTE
CMAT_CRITICO COD_CICLO CODICE01 CODICE02 CODICE03 CODICE04 CODICE05 COMMESSA
DATA_EMISSIONE DATA_FINE DATA_FINE_PROG DATA_INIZ_PROG DATA_INIZIO DATA_INS DATA_UPD
DESCRIZIONE DESCRIZIONE01 DESCRIZIONE02 DESCRIZIONE03 DESCRIZIONE04 DESCRIZIONE05
FALTPNUMB FEXTORDER FPLDUEDATE FPLSTDATE FRQDUEDATE FRQSTDATE GG_RITARDO LOCK_PLAN
LOTTO MAGAZZINO MODIFICATO PART_NUMBER PRIORITA QTA_COMPLETATA QTA_LANCIATA
QTA_RICHIESTA QTA_VERSATA QUANTITA1 QUANTITA2 QUANTITA3 QUANTITA4 REPARTO
RIFERIMENTO STAMPATO STATO STATO_CAPACITA STATO_MATERIALI STATO_RITARDI TIPO
UTENTE_UPD VALORE01 VALORE02 VALORE03 VALORE04 VALORE05 FPLANNED FLASTPLANDATE
FLASTPLANUSER ATTIVO FFCNTPART FPROGRAM DATA_DOC FRFSTDATE FRFDUEDATE CEFF_INDIRECT
C_INDIRECT ECCNETTYPE ECCNETQTY ECCNETDT FEXPORTDATE FQUALITY FWBS FMNGSTATUS
FGENCOMM CARATTERISTICA6 CARATTERISTICA7 CARATTERISTICA8 CARATTERISTICA9
CARATTERISTICA10 CODICE06 CODICE07 CODICE08 CODICE09 CODICE10 VALORE06 VALORE07
VALORE08 VALORE09 VALORE10 FRELDATE FPLSTMINDATE FPLLEADTIME FNATTACHMENT FNDESCS
DATA01 DATA02 DATA03 DATA04 DATA05 DATA06 DATA07 DATA08 DATA09 DATA10 FBEPRODQTY
FNOTE FHASALT FPERCSALEABILITY FSALEABILITYDATE FPNUMBPHASE FSOURCEORDER
FSOURCEOPERATN FPNUMBBUF FALTPNUMBBUF FPSTATUSALERT FCLOSINGEXPDATE PWR_SETUP
PWR_WORK EFF_PWR_SETUP EFF_PWR_WORK EFF_PWR_IDLE FAVOIDRSTPRIO
""".split()


CAMPI_TESTO = "ORDINE COD_CICLO DESCRIZIONE PART_NUMBER UTENTE_UPD CLIENTE".split()


CAMPI_DATA = """DATA_EMISSIONE DATA_FINE DATA_FINE_PROG DATA_INIZ_PROG
DATA_INIZIO DATA_INS DATA_UPD FPLDUEDATE FPLSTDATE FRQDUEDATE FRQSTDATE""".split()


def costruisci_insert(riga):
    """Mantiene le 148 colonne e legge dal CSV i campi richiesti, incluso CLIENTE.

    VALORE01 e VALORE02 restano zero, come nella query modello.
    I campi CSV vuoti diventano NULL; ORDINE è obbligatorio.
    FAVOIDRSTPRIO resta NULL (non popolato).
    """
    # Nel CSV originale FPLDUEDATE si chiama FPLDUEDATA.
    riga = dict(riga)
    # Compatibilità con i CSV precedenti: CLIENTE assente o vuoto -> NULL.
    riga.setdefault("CLIENTE", "")
    if "FPLDUEDATE" not in riga and "FPLDUEDATA" in riga:
        riga["FPLDUEDATE"] = riga["FPLDUEDATA"]
    richiesti = CAMPI_TESTO + CAMPI_DATA
    mancanti = [c for c in richiesti if c not in riga]
    if mancanti:
        raise ValueError("Colonne CSV mancanti: " + ", ".join(mancanti))
    if not riga["ORDINE"].strip():
        raise ValueError("ORDINE non può essere vuoto.")

    valori = dict.fromkeys(COLONNE, "NULL")
    # Valori fissi del modello: gli altri campi restano NULL.
    for campo, valore in {
        "FALTPNUMB": "0", "MODIFICATO": "S", "REPARTO": "REP01",
        "STAMPATO": "N", "STATO": "COM", "TIPO": "MAKE",
        "FPLANNED": "N", "ATTIVO": "Y", "FALTPNUMBBUF": "0",
    }.items():
        valori[campo] = sql_testo(valore)
    for campo, precisione in {
        "ALT_CICLO": 10, "PRIORITA": 6, "FPLLEADTIME": 5,
        "FNATTACHMENT": 6, "FNDESCS": 6, "FHASALT": 2,
    }.items():
        valori[campo] = f"CAST(0 AS Numeric({precisione}, 0))"
    for campo in """QTA_COMPLETATA QTA_LANCIATA QTA_RICHIESTA QTA_VERSATA
    QUANTITA1 QUANTITA2 QUANTITA3 QUANTITA4 VALORE01 VALORE02 VALORE03 VALORE04 VALORE05""".split():
        valori[campo] = "CAST(0.00000 AS Numeric(15, 5))"

    for campi, converti in ((CAMPI_TESTO, sql_testo), (CAMPI_DATA, sql_data)):
        for campo in campi:
            valore = riga[campo]
            valori[campo] = converti(valore) if valore.strip() else "NULL"
    # TASK, UTENTE_TASK e gli altri campi non presenti in ORDINI non vengono inseriti.
    applica_quantita(valori, riga)
    if scrostatore.attivo(riga):
        valori['FAVOIDRSTPRIO'] = sql_testo('N')
    nomi = ", ".join(f"[{c}]" for c in COLONNE)
    dati = ",\n    ".join(valori[c] for c in COLONNE)
    return f"INSERT [dbo].[ORDINI] ({nomi})\nVALUES (\n    {dati}\n);\nGO\n"
