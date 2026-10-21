"""Generazione INSERT per situazioni; valori e regole del modello originale."""

from ..quantita import applica_quantita
from ..conversions import sql_testo, sql_data, sql_numero, minuti_in_ore_sql
from datetime import datetime, timedelta
from ..conversions import durata_non_negativa, ore_da_intervallo

COLONNE_SITUAZIONI = """
OGGETTO TIPO_OGGETTO DATA PROGRESSIVO CAUSALE CAUSALE_MAT CDCMACCHINA CENTRO_COSTO
CHIUSURA DOCUMENTO EXPORTDATE FINSDATE ID_OPER INFO01 INFO02 INFO03 INFO04 INFO05
INFO06 INFO07 INFO08 INFO09 INFO10 INFORMAZIONI LAVORO LAVORO_GIUST LOTTO MACCHINA
OPERATORE ORA_FINE ORA_INIZIO PART_NUMBER QTA_CICLO QTA_COMPLETATA QTA_CONTATA
QTA_RICHIESTA QTA_SCARTATA QTA_SOSPESA QUADRATURA QUANTITA1 QUANTITA2 QUANTITA3
QUANTITA4 SETUP SETUP_GIUST SQUADRA TASK TIPO TURNO FALTPNUMB FSKILL FENDCAUSE
""".split()


def costruisci_insert_situazioni(riga):
    """Genera WSET e WORK per MAC e OPE, conservando tutte le 52 colonne.

    WSET: DATA_INIZIO -> CHIUSURA_ATTREZZAGGIO.
    WORK: INIZIO_LAVORAZIONE -> DATA_FINE.
    DATA è DATA_INIZIO a mezzanotte; FINSDATE è DATA_INIZIO + 2 giorni.
    LAVORO e SETUP derivano dagli intervalli effettivi.
    Per i cicli non forno QTY_RICHIESTA alimenta QTA_RICHIESTA su tutte
    le righe MAC/OPE. QTY_COMPLETATA alimenta QTA_COMPLETATA solo su WORK.
    La fase (WSET/WORK), non il progressivo libero assegnato dal database,
    determina dove registrare la quantità completata.
    """
    richiesti = {"TASK", "MACCHINA", "UTENTE_EVENTI", "DATA_INIZIO", "DATA_FINE",
                 "CDCMACCHINA", "CENTRO_COSTO", "PART_NUMBER", "VALORE01",
                 "CHIUSURA_ATTREZZAGGIO", "INIZIO_LAVORAZIONE"}
    mancanti = sorted(richiesti - riga.keys())
    if mancanti:
        raise ValueError("Colonne CSV mancanti per situazioni: " + ", ".join(mancanti))
    for campo in ("TASK", "MACCHINA", "UTENTE_EVENTI", "DATA_INIZIO", "DATA_FINE",
                  "CHIUSURA_ATTREZZAGGIO", "INIZIO_LAVORAZIONE"):
        if not riga[campo].strip():
            raise ValueError(f"{campo} non può essere vuoto per situazioni.")
    sql_data(riga["DATA_INIZIO"])
    sql_data(riga["DATA_FINE"])
    inizio = datetime.fromisoformat(riga["DATA_INIZIO"].strip())
    fine = datetime.fromisoformat(riga["DATA_FINE"].strip())
    sql_data(riga["CHIUSURA_ATTREZZAGGIO"])
    sql_data(riga["INIZIO_LAVORAZIONE"])
    fine_setup = datetime.fromisoformat(riga["CHIUSURA_ATTREZZAGGIO"].strip())
    inizio_lavoro = datetime.fromisoformat(riga["INIZIO_LAVORAZIONE"].strip())
    if not inizio <= fine_setup <= inizio_lavoro <= fine:
        raise ValueError("Date situazioni non ordinate: DATA_INIZIO <= CHIUSURA_ATTREZZAGGIO "
                         "<= INIZIO_LAVORAZIONE <= DATA_FINE.")
    quantita = durata_non_negativa(riga["VALORE01"], "VALORE01")
    try:
        finsdate = inizio + timedelta(days=2)
    except OverflowError as errore:
        raise ValueError("FINSDATE fuori intervallo per situazioni.") from errore
    istruzioni = []
    for tipo_oggetto in ("MAC", "OPE"):
        oggetto = riga["MACCHINA"] if tipo_oggetto == "MAC" else riga["UTENTE_EVENTI"]
        for fase, tipo, ora_inizio, ora_fine in (
            (1, "WSET", inizio, fine_setup), (2, "WORK", inizio_lavoro, fine)
        ):
            valori = dict.fromkeys(COLONNE_SITUAZIONI, "NULL")
            for campo in """LAVORO LAVORO_GIUST QTA_CICLO QTA_COMPLETATA QTA_CONTATA
            QTA_RICHIESTA QTA_SCARTATA QTA_SOSPESA QUANTITA1 QUANTITA2 QUANTITA3
            QUANTITA4 SETUP SETUP_GIUST""".split():
                valori[campo] = "CAST(0.00000 AS Numeric(15, 5))"
            for destinazione, sorgente in {
                "CDCMACCHINA": "CDCMACCHINA", "CENTRO_COSTO": "CENTRO_COSTO",
                "MACCHINA": "MACCHINA", "OPERATORE": "UTENTE_EVENTI",
                "PART_NUMBER": "PART_NUMBER", "TASK": "TASK", "ID_OPER": "TASK",
            }.items():
                valore = riga[sorgente]
                valori[destinazione] = sql_testo(valore) if valore.strip() else "NULL"
            valori["OGGETTO"] = sql_testo(oggetto)
            valori["TIPO_OGGETTO"] = sql_testo(tipo_oggetto)
            valori["TIPO"] = sql_testo(tipo)
            valori["PROGRESSIVO"] = "CAST(@progressivo_situazione AS Numeric(5, 0))"
            valori["FALTPNUMB"] = "N'0'"
            valori["DATA"] = sql_data(inizio.replace(hour=0, minute=0, second=0, microsecond=0).isoformat())
            valori["FINSDATE"] = sql_data(finsdate.isoformat())
            valori["ORA_INIZIO"] = sql_data(ora_inizio.isoformat())
            valori["ORA_FINE"] = sql_data(ora_fine.isoformat())
            if tipo == "WSET":
                valori["SETUP"] = ore_da_intervallo(ora_inizio, ora_fine)
            else:
                valori["LAVORO"] = ore_da_intervallo(ora_inizio, ora_fine)
                valori["QTA_CONTATA"] = sql_numero(str(quantita))
                if tipo_oggetto == "MAC":
                    valori["CHIUSURA"] = "N'O'"
            if tipo_oggetto == "MAC" and fase == 2:
                valori["LAVORO"] = ore_da_intervallo(ora_inizio, ora_fine)
            applica_quantita(valori, riga, completata=tipo == "WORK")
            nomi = ", ".join(f"[{c}]" for c in COLONNE_SITUAZIONI)
            dati = ",\n    ".join(valori[c] for c in COLONNE_SITUAZIONI)
            ricerca = (
                "DECLARE @progressivo_situazione int = 1;\n"
                "IF @@TRANCOUNT = 0 THROW 50001, N'SITUAZIONI richiede una transazione attiva', 1;\n"
                "WHILE EXISTS (\n"
                "    SELECT 1 FROM [dbo].[situazioni] WITH (UPDLOCK, HOLDLOCK)\n"
                f"    WHERE [OGGETTO] = {valori['OGGETTO']}\n"
                f"      AND [TIPO_OGGETTO] = {valori['TIPO_OGGETTO']}\n"
                f"      AND [DATA] = {valori['DATA']}\n"
                "      AND [PROGRESSIVO] = @progressivo_situazione\n"
                ")\nBEGIN\n"
                "    SET @progressivo_situazione = @progressivo_situazione + 1;\n"
                "    IF @progressivo_situazione > 99999\n"
                "        THROW 50002, N'Nessun PROGRESSIVO disponibile per SITUAZIONI', 1;\n"
                "END;\n"
            )
            istruzioni.append(ricerca + f"INSERT [dbo].[situazioni] ({nomi})\nVALUES (\n    {dati}\n);\nGO\n")
    return istruzioni
