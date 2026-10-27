"""Generazione INSERT per jobset; valori e regole del modello originale."""

from ..quantita import applica_quantita
from ..conversions import sql_testo, sql_data, sql_numero, lavoro_effettivo_sql

COLONNE_JOBSET = """
TASK ORDINE OPERAZIONE CEFF_ESTERNO CEFF_FIX_MAC CEFF_FIX_MAN CEFF_MACCHINA
CEFF_MANODOPERA DIMENSIONE ID_OPER LOTTO QTA_COMPLETATA QTA_CONTATA QTA_RECUPERATA
QTA_RICHIESTA QTA_SCARTATA QTA_SOSPESA QUANTITA1 QUANTITA2 QUANTITA3 QUANTITA4
TEFF_GIUST_MAC TEFF_GIUST_MAN TEFF_LAVORO_MAC TEFF_LAVORO_MAN TEFF_SETUP_MAC
TEFF_SETUP_MAN TOT_SUPPL_MAC TOT_SUPPL_MAN CEFF_INDIRECT QTA_RILAVORATA SEQUENZA
EFF_PWR_SETUP EFF_PWR_WORK EFF_PWR_IDLE CEFF_PWR_SETUP CEFF_PWR_WORK CEFF_PWR_IDLE
""".split()


TESTO_JOBSET = {"TASK": "TASK", "ORDINE": "ORDINE",
                "OPERAZIONE": "OPERAZIONI", "ID_OPER": "TASK"}


def costruisci_insert_jobset(riga):
    """Mantiene tutte le colonne JOBSET e sostituisce gli 8 campi richiesti.

    TASK alimenta anche ID_OPER; OPERAZIONE proviene da OPERAZIONI nel CSV.
    I tempi di lavoro sono l’intervallo DATA_INIZIO/DATA_FINE in ore meno setup.
    Per i forni resta VALORE01 / 60. Risultato a cinque decimali.
    """
    richiesti = (list(dict.fromkeys(TESTO_JOBSET.values()))
                 + ["VALORE01", "TEFF_SETUP_MAC", "TEFF_SETUP_MAN"])
    mancanti = [campo for campo in richiesti if campo not in riga]
    if mancanti:
        raise ValueError("Colonne CSV mancanti per JOBSET: " + ", ".join(mancanti))
    for campo in dict.fromkeys(TESTO_JOBSET.values()):
        if not riga[campo].strip():
            raise ValueError(f"{campo} non può essere vuoto per JOBSET.")
    valori = dict.fromkeys(COLONNE_JOBSET, "NULL")
    for campo in """CEFF_ESTERNO CEFF_FIX_MAC CEFF_FIX_MAN CEFF_MACCHINA
    CEFF_MANODOPERA QTA_COMPLETATA QTA_RICHIESTA QTA_SCARTATA QTA_SOSPESA
    QUANTITA1 QUANTITA2 QUANTITA3 QUANTITA4 TEFF_GIUST_MAC TEFF_GIUST_MAN
    TOT_SUPPL_MAC TOT_SUPPL_MAN CEFF_INDIRECT""".split():
        valori[campo] = "CAST(0.00000 AS Numeric(15, 5))"
    valori["SEQUENZA"] = "CAST(0 AS Numeric(5, 0))"
    for destinazione, sorgente in TESTO_JOBSET.items():
        valori[destinazione] = sql_testo(riga[sorgente])
    for campo in ("TEFF_SETUP_MAC", "TEFF_SETUP_MAN"):
        valore = riga[campo]
        valori[campo] = sql_numero(valore) if valore.strip() else "NULL"
    ore = lavoro_effettivo_sql(riga)
    valori["TEFF_LAVORO_MAC"] = ore
    valori["TEFF_LAVORO_MAN"] = ore
    applica_quantita(valori, riga, aggiorna_contata=False)
    nomi = ", ".join(f"[{c}]" for c in COLONNE_JOBSET)
    dati = ",\n    ".join(valori[c] for c in COLONNE_JOBSET)
    return f"INSERT [dbo].[JOBSET] ({nomi})\nVALUES (\n    {dati}\n);\nGO\n"
