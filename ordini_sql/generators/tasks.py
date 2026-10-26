"""Generazione INSERT per tasks; valori e regole del modello originale."""

from .. import tempi_previsti
from .. import scrostatore
from ..quantita import applica_quantita
from ..conversions import sql_testo, sql_data, sql_numero, minuti_in_ore_sql

COLONNE_TASKS = """
TASK CEFF_ESTERNO CEFF_FIX_MAC CEFF_FIX_MAN CEFF_MACCHINA CEFF_MANODOPERA
CICLI_CONTATI CRITICO DATA_FINE DATA_FINE_PROG DATA_INIZ_PROG DATA_INIZIO DATA_INS
DATA_UPD DESCRIZIONE INIZIO_MATRICOLE MACCHINA MACCHINA_ASSEGNATA MODIFICATO
NUM_OPERAI_LAVORO NUM_OPERAI_SETUP POSIZIONE PRIORITA PROGRAMMA QTA_CICLO
QTA_CONTATA QTA_SCARTATA STAMPATO STATO TEFF_GIUST_MAC TEFF_GIUST_MAN
TEFF_LAVORO_MAC TEFF_LAVORO_MAN TEFF_SETUP_MAC TEFF_SETUP_MAN TIPO TOT_LAVORO_MAC
TOT_LAVORO_MAN TOT_SETUP_MAC TOT_SETUP_MAN TOT_SUPPL_MAC TOT_SUPPL_MAN UTENTE_UPD
FFIXSTDATE FFIXDUEDATE FNOTE FCAPSTATE FMATSTATE FLATESTATE FCODE01 FCODE02 FCODE03
FCODE04 FCODE05 FVALUE01 FVALUE02 FVALUE03 FVALUE04 FVALUE05 CEFF_INDIRECT FPRGDATE
FMNGSTATUS FRESNOTAVAILABLE FRESCONFLICT FLOCKPLAN FPRDUESETDATE FGROUPTYPE
FNATTACHMENT QTA_CONTATA_SCARTI FNDESCS FPERCADVANCEMENT FREFTYPE FREFERENCE
CICLI_CONTATI_SCARTI QTA_RICHIESTA FSQPREVDTPRG FSQNEXTDTPRG FSQPREVMAC FSQNEXTMAC
FSQPREVSTS FSQNEXTSTS FSQPREVTSK FSQNEXTTSK FSQPREVHOURS FSQNEXTHOURS FCODE06
FCODE07 FCODE08 FCODE09 FCODE10 FVALUE06 FVALUE07 FVALUE08 FVALUE09 FVALUE10
FTIMECHANGEDBYUSER FFORCEDTOTALMACWORKTIME FPARTPROGRAM FPARTPROGRAMQTY
EFF_PWR_SETUP EFF_PWR_WORK EFF_PWR_IDLE CEFF_PWR_SETUP CEFF_PWR_WORK CEFF_PWR_IDLE
""".split()


DATE_TASKS = "DATA_FINE DATA_FINE_PROG DATA_INIZ_PROG DATA_INIZIO DATA_INS".split()


TESTO_TASKS = {"TASK": "TASK", "MACCHINA": "MACCHINA",
               "MACCHINA_ASSEGNATA": "MACCHINA_ASSEGNATA", "UTENTE_UPD": "UTENTE_TASK"}


TEMPI_TASKS = ("TEFF_LAVORO_MAC", "TEFF_LAVORO_MAN", "TEFF_SETUP_MAC", "TEFF_SETUP_MAN")


def costruisci_insert_tasks(riga):
    """Mantiene tutte le colonne TASKS, sostituendo i soli campi richiesti.

    UTENTE_UPD proviene da UTENTE_TASK (non dall'utente dell'ordine).
    CICLI_CONTATI legge VALORE01 direttamente, senza conversione in ore.
    TEFF_LAVORO_MAC/MAN derivano da VALORE01 (minuti / 60), a 5 decimali.
    Se una colonna è presente ma vuota, scrive NULL.
    """
    richiesti = list(TESTO_TASKS.values()) + DATE_TASKS + list(TEMPI_TASKS[2:]) + ["VALORE01"]
    mancanti = [c for c in richiesti if c not in riga]
    if mancanti:
        raise ValueError("Colonne CSV mancanti per TASKS: " + ", ".join(mancanti))
    if not riga["TASK"].strip():
        raise ValueError("TASK non può essere vuoto.")
    valori = dict.fromkeys(COLONNE_TASKS, "NULL")
    for campo in """CEFF_ESTERNO CEFF_FIX_MAC CEFF_FIX_MAN CEFF_MACCHINA
    CEFF_MANODOPERA QTA_CICLO QTA_CONTATA TEFF_GIUST_MAC TEFF_GIUST_MAN
    TOT_LAVORO_MAC TOT_LAVORO_MAN TOT_SETUP_MAC TOT_SETUP_MAN TOT_SUPPL_MAC
    TOT_SUPPL_MAN CEFF_INDIRECT CICLI_CONTATI_SCARTI QTA_RICHIESTA""".split():
        valori[campo] = "CAST(0.00000 AS Numeric(15, 5))"
    for campo in ("NUM_OPERAI_LAVORO", "NUM_OPERAI_SETUP"):
        valori[campo] = "CAST(0.00 AS Numeric(5, 2))"
    for campo in ("FNATTACHMENT", "FNDESCS"):
        valori[campo] = "CAST(0 AS Numeric(6, 0))"
    for campo, valore in {"CRITICO": "N", "STAMPATO": "N", "STATO": "COM",
                          "TIPO": "WRK", "FLOCKPLAN": "N"}.items():
        valori[campo] = sql_testo(valore)
    for destinazione, sorgente in TESTO_TASKS.items():
        valore = riga[sorgente]
        valori[destinazione] = sql_testo(valore) if valore.strip() else "NULL"
    for campo in DATE_TASKS:
        valore = riga[campo]
        valori[campo] = sql_data(valore) if valore.strip() else "NULL"
    for campo in TEMPI_TASKS[2:]:
        valore = riga[campo]
        valori[campo] = sql_numero(valore) if valore.strip() else "NULL"
    cicli = riga["VALORE01"]
    valori["CICLI_CONTATI"] = sql_numero(cicli) if cicli.strip() else "NULL"
    ore = minuti_in_ore_sql(riga["VALORE01"])
    valori["TEFF_LAVORO_MAC"] = ore
    valori["TEFF_LAVORO_MAN"] = ore
    applica_quantita(valori, riga, aggiorna_contata=False)
    if tempi_previsti.attivo(riga):
        lavoro = sql_numero(str(tempi_previsti.lavoro_pianificato(riga)))
        for risorsa in ('MAC', 'MAN'):
            valori['TOT_SETUP_' + risorsa] = sql_numero(str(tempi_previsti.setup_previsto(riga)))
            valori['TOT_LAVORO_' + risorsa] = lavoro
    if riga['COD_CICLO'].strip().upper() == 'CYC_MINIPAN':
        # QUANTITA1 è il nome storico nel CSV; QUANTITA01 ha precedenza se fornita.
        valori['FVALUE01'] = sql_numero(riga.get('QUANTITA01', riga['QUANTITA1']))
    if scrostatore.attivo(riga):
        scrostatore.applica_totali_task(valori, riga)
    nomi = ", ".join(f"[{c}]" for c in COLONNE_TASKS)
    dati = ",\n    ".join(valori[c] for c in COLONNE_TASKS)
    return f"INSERT [dbo].[TASKS] ({nomi})\nVALUES (\n    {dati}\n);\nGO\n"
