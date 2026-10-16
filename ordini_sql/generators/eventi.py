"""Generazione INSERT per eventi; valori e regole del modello originale."""

from ..conversions import sql_testo, sql_data, sql_numero, minuti_in_ore_sql

COLONNE_EVENTI = ['TASK', 'TIPO_OGGETTO', 'OGGETTO', 'EVENTO', 'ORA_EVENTO', 'CAUSALE', 'EXPORTDATE', 'FOBJECT', 'ID_OPER', 'INFO1', 'INFO10', 'INFO11', 'INFO12', 'INFO13', 'INFO14', 'INFO15', 'INFO16', 'INFO17', 'INFO18', 'INFO19', 'INFO2', 'INFO20', 'INFO3', 'INFO4', 'INFO5', 'INFO6', 'INFO7', 'INFO8', 'INFO9', 'INFORMAZIONE', 'LOTTO', 'MACCHINA', 'PART_NUMBER', 'QTA_CICLO', 'QTA_COMPLETATA', 'QTA_CONTATA', 'QTA_SCARTATA', 'QTA_SOSPESA', 'QUANTITA1', 'QUANTITA2', 'QUANTITA3', 'QUANTITA4', 'SOURCE', 'TEMPO', 'TEMPO_SETUP', 'UTENTE', 'OPERATORE', 'FSERIAL', 'PROGRESSIVO', 'FALTPNUMB', 'QTA_RILAVORATA', 'FSKILL', 'QTA_CONTATA_SCARTI', 'PWR_WORK', 'PWR_SETUP']


DEFAULT_EVENTI = {'OPNS': {'CAUSALE': 'NULL',
          'EXPORTDATE': 'NULL',
          'FOBJECT': 'NULL',
          'ID_OPER': 'NULL',
          'INFO1': 'NULL',
          'INFO10': 'NULL',
          'INFO11': 'NULL',
          'INFO12': 'NULL',
          'INFO13': 'NULL',
          'INFO14': 'NULL',
          'INFO15': 'NULL',
          'INFO16': 'NULL',
          'INFO17': 'NULL',
          'INFO18': 'NULL',
          'INFO19': 'NULL',
          'INFO2': 'NULL',
          'INFO20': 'NULL',
          'INFO3': 'NULL',
          'INFO4': 'NULL',
          'INFO5': 'NULL',
          'INFO6': 'NULL',
          'INFO7': 'NULL',
          'INFO8': 'NULL',
          'INFO9': 'NULL',
          'INFORMAZIONE': 'NULL',
          'LOTTO': 'NULL',
          'QTA_CICLO': 'CAST(0.00000 AS Numeric(15, 5))',
          'QTA_COMPLETATA': 'CAST(0.00000 AS Numeric(15, 5))',
          'QTA_SCARTATA': 'CAST(0.00000 AS Numeric(15, 5))',
          'QTA_SOSPESA': 'NULL',
          'QUANTITA1': 'NULL',
          'QUANTITA2': 'NULL',
          'QUANTITA3': 'NULL',
          'QUANTITA4': 'NULL',
          'SOURCE': "N'WS'",
          'TEMPO': 'NULL',
          'TEMPO_SETUP': 'NULL',
          'FSERIAL': 'NULL',
          'PROGRESSIVO': 'CAST(0 AS Numeric(6, 0))',
          'FALTPNUMB': 'NULL',
          'QTA_RILAVORATA': 'NULL',
          'FSKILL': 'NULL',
          'QTA_CONTATA_SCARTI': 'NULL',
          'PWR_WORK': 'NULL',
          'PWR_SETUP': 'NULL'},
 'CLSS': {'CAUSALE': 'NULL',
          'EXPORTDATE': 'NULL',
          'FOBJECT': 'NULL',
          'ID_OPER': 'NULL',
          'INFO1': 'NULL',
          'INFO10': 'NULL',
          'INFO11': 'NULL',
          'INFO12': 'NULL',
          'INFO13': 'NULL',
          'INFO14': 'NULL',
          'INFO15': 'NULL',
          'INFO16': 'NULL',
          'INFO17': 'NULL',
          'INFO18': 'NULL',
          'INFO19': 'NULL',
          'INFO2': 'NULL',
          'INFO20': 'NULL',
          'INFO3': 'NULL',
          'INFO4': 'NULL',
          'INFO5': 'NULL',
          'INFO6': 'NULL',
          'INFO7': 'NULL',
          'INFO8': 'NULL',
          'INFO9': 'NULL',
          'INFORMAZIONE': 'NULL',
          'LOTTO': 'NULL',
          'QTA_CICLO': 'NULL',
          'QTA_COMPLETATA': 'CAST(0.00000 AS Numeric(15, 5))',
          'QTA_SCARTATA': 'CAST(0.00000 AS Numeric(15, 5))',
          'QTA_SOSPESA': 'NULL',
          'QUANTITA1': 'NULL',
          'QUANTITA2': 'NULL',
          'QUANTITA3': 'NULL',
          'QUANTITA4': 'NULL',
          'SOURCE': "N'WS'",
          'TEMPO': 'NULL',
          'TEMPO_SETUP': 'NULL',
          'FSERIAL': 'NULL',
          'PROGRESSIVO': 'CAST(0 AS Numeric(6, 0))',
          'FALTPNUMB': 'NULL',
          'QTA_RILAVORATA': 'NULL',
          'FSKILL': 'NULL',
          'QTA_CONTATA_SCARTI': 'NULL',
          'PWR_WORK': 'NULL',
          'PWR_SETUP': 'NULL'},
 'OPN': {'CAUSALE': 'NULL',
         'EXPORTDATE': 'NULL',
         'FOBJECT': 'NULL',
         'ID_OPER': 'NULL',
         'INFO1': 'NULL',
         'INFO10': 'NULL',
         'INFO11': 'NULL',
         'INFO12': 'NULL',
         'INFO13': 'NULL',
         'INFO14': 'NULL',
         'INFO15': 'NULL',
         'INFO16': 'NULL',
         'INFO17': 'NULL',
         'INFO18': 'NULL',
         'INFO19': 'NULL',
         'INFO2': 'NULL',
         'INFO20': 'NULL',
         'INFO3': 'NULL',
         'INFO4': 'NULL',
         'INFO5': 'NULL',
         'INFO6': 'NULL',
         'INFO7': 'NULL',
         'INFO8': 'NULL',
         'INFO9': 'NULL',
         'INFORMAZIONE': 'NULL',
         'LOTTO': 'NULL',
         'QTA_CICLO': 'CAST(0.00000 AS Numeric(15, 5))',
         'QTA_COMPLETATA': 'CAST(0.00000 AS Numeric(15, 5))',
         'QTA_SCARTATA': 'CAST(0.00000 AS Numeric(15, 5))',
         'QTA_SOSPESA': 'NULL',
         'QUANTITA1': 'NULL',
         'QUANTITA2': 'NULL',
         'QUANTITA3': 'NULL',
         'QUANTITA4': 'NULL',
         'SOURCE': "N'WS'",
         'TEMPO': 'NULL',
         'TEMPO_SETUP': 'NULL',
         'FSERIAL': 'NULL',
         'PROGRESSIVO': 'CAST(0 AS Numeric(6, 0))',
         'FALTPNUMB': 'NULL',
         'QTA_RILAVORATA': 'NULL',
         'FSKILL': 'NULL',
         'QTA_CONTATA_SCARTI': 'NULL',
         'PWR_WORK': 'NULL',
         'PWR_SETUP': 'NULL'},
 'CLS': {'CAUSALE': 'NULL',
         'EXPORTDATE': 'NULL',
         'FOBJECT': 'NULL',
         'ID_OPER': 'NULL',
         'INFO1': 'NULL',
         'INFO10': 'NULL',
         'INFO11': 'NULL',
         'INFO12': 'NULL',
         'INFO13': 'NULL',
         'INFO14': 'NULL',
         'INFO15': 'NULL',
         'INFO16': 'NULL',
         'INFO17': 'NULL',
         'INFO18': 'NULL',
         'INFO19': 'NULL',
         'INFO2': 'NULL',
         'INFO20': 'NULL',
         'INFO3': 'NULL',
         'INFO4': 'NULL',
         'INFO5': 'NULL',
         'INFO6': 'NULL',
         'INFO7': 'NULL',
         'INFO8': 'NULL',
         'INFO9': 'NULL',
         'INFORMAZIONE': 'NULL',
         'LOTTO': 'NULL',
         'QTA_CICLO': 'NULL',
         'QTA_COMPLETATA': 'CAST(0.00000 AS Numeric(15, 5))',
         'QTA_SCARTATA': 'CAST(0.00000 AS Numeric(15, 5))',
         'QTA_SOSPESA': 'NULL',
         'QUANTITA1': 'NULL',
         'QUANTITA2': 'NULL',
         'QUANTITA3': 'NULL',
         'QUANTITA4': 'NULL',
         'SOURCE': "N'FDI_002240'",
         'TEMPO': 'NULL',
         'TEMPO_SETUP': 'NULL',
         'FSERIAL': 'NULL',
         'PROGRESSIVO': 'CAST(0 AS Numeric(6, 0))',
         'FALTPNUMB': 'CAST(0 AS Numeric(6, 0))',
         'QTA_RILAVORATA': 'NULL',
         'FSKILL': 'NULL',
         'QTA_CONTATA_SCARTI': 'CAST(0.00000 AS Numeric(15, 5))',
         'PWR_WORK': 'NULL',
         'PWR_SETUP': 'NULL'}}


MAPPATURA_EVENTI = {
    "OPNS": "DATA_INIZIO",
    "CLSS": "CHIUSURA_ATTREZZAGGIO",
    "OPN": "INIZIO_LAVORAZIONE",
    "CLS": "DATA_FINE",
}


def costruisci_insert_eventi(riga):
    """Genera quattro eventi MAC e quattro OPE, mantenendo tutte le 55 colonne.

    UTENTE proviene da UTENTE_EVENTI per CLS; per gli altri eventi vale WS.
    Per CLS, QTA_CONTATA usa VALORE01 direttamente, senza conversione in ore.
    OGGETTO legge UTENTE_EVENTI per OPE e MACCHINA per MAC.
    La colonna MACCHINA legge sempre MACCHINA del CSV.
    """
    richiesti = {"TASK", "MACCHINA", "UTENTE_EVENTI", "PART_NUMBER", "VALORE01"}
    richiesti.update(MAPPATURA_EVENTI.values())
    mancanti = sorted(richiesti - riga.keys())
    if mancanti:
        raise ValueError("Colonne CSV mancanti per eventi: " + ", ".join(mancanti))
    for campo in ("TASK", "MACCHINA"):
        if not riga[campo].strip():
            raise ValueError(f"{campo} non può essere vuoto per eventi.")
    istruzioni = []
    for tipo in ("MAC", "OPE"):
        for evento, campo_data in MAPPATURA_EVENTI.items():
            if not riga[campo_data].strip():
                raise ValueError(f"{campo_data} non può essere vuoto per l'evento {evento}.")
            valori = dict.fromkeys(COLONNE_EVENTI, "NULL")
            valori.update(DEFAULT_EVENTI[evento])
            for destinazione, sorgente in {
                "TASK": "TASK", "MACCHINA": "MACCHINA",
                "OGGETTO": "UTENTE_EVENTI" if tipo == "OPE" else "MACCHINA",
                "OPERATORE": "UTENTE_EVENTI",
            }.items():
                valore = riga[sorgente]
                valori[destinazione] = sql_testo(valore) if valore.strip() else "NULL"
            utente = riga["UTENTE_EVENTI"] if evento == "CLS" else "WS"
            valori["UTENTE"] = sql_testo(utente) if utente.strip() else "NULL"
            valori["TIPO_OGGETTO"] = sql_testo(tipo)
            valori["EVENTO"] = sql_testo(evento)
            valori["ORA_EVENTO"] = sql_data(riga[campo_data])
            if evento == "CLS":
                part_number = riga["PART_NUMBER"]
                quantita = riga["VALORE01"]
                valori["PART_NUMBER"] = sql_testo(part_number) if part_number.strip() else "NULL"
                valori["QTA_CONTATA"] = sql_numero(quantita) if quantita.strip() else "NULL"
            nomi = ", ".join(f"[{c}]" for c in COLONNE_EVENTI)
            dati = ",\n    ".join(valori[c] for c in COLONNE_EVENTI)
            istruzioni.append(f"INSERT [dbo].[eventi] ({nomi})\nVALUES (\n    {dati}\n);\nGO\n")
    return istruzioni
