"""Esegue gli SQL del generatore, un’unica transazione per tutti i file selezionati."""
import re
from pathlib import Path


def separa_batch(testo):
    """Separa GO fuori da stringhe, identificatori e commenti multilinea."""
    batches, lines = [], []
    state, depth = None, 0
    for line in testo.splitlines(keepends=True):
        if state is None and depth == 0 and re.fullmatch(r'\s*GO\s*(?:--[^\r\n]*)?[\r\n]*', line, re.I):
            if ''.join(lines).strip():
                batches.append(''.join(lines).strip())
            lines = []
            continue
        if state is None and depth == 0 and re.match(r'^\s*GO\s+\d', line, re.I):
            raise ValueError('GO con ripetizioni non supportato: usare i file del generatore.')
        lines.append(line)
        i = 0
        while i < len(line):
            pair = line[i:i+2]
            ch = line[i]
            if depth:
                if pair == '/*': depth += 1; i += 2; continue
                if pair == '*/': depth -= 1; i += 2; continue
            elif state:
                end = ']' if state == '[' else state
                if ch == end:
                    if i+1 < len(line) and line[i+1] == end:
                        i += 2; continue
                    state = None
            else:
                if pair == '--': break
                if pair == '/*': depth = 1; i += 2; continue
                if ch in ("'", '"', '['): state = ch
            i += 1
    if state or depth:
        raise ValueError('Stringa, identificatore o commento SQL non terminato.')
    if ''.join(lines).strip(): batches.append(''.join(lines).strip())
    return batches


def prepara_file(percorso, database):
    """Controlla il database USE e restituisce gli INSERT generati.

    Il database effettivo è scelto dalla connessione; USE viene verificato e
    rimosso, evitando che uno script vecchio cambi il database di destinazione.
    """
    batches = separa_batch(Path(percorso).read_text(encoding='utf-8-sig'))
    if not batches:
        raise ValueError(f'{percorso}: file vuoto.')
    first = re.sub(r'^\s*--[^\n]*(?:\n|$)', '', batches[0], flags=re.M).strip()
    match = re.fullmatch(r'USE\s+\[((?:[^\]]|\]\])+)\]\s*;?', first, re.I)
    if not match:
        raise ValueError(f'{percorso}: manca USE [database] iniziale del generatore.')
    if match.group(1).replace(']]', ']') != database:
        raise ValueError(f'{percorso}: database nello script diverso da config.json; rigenerare gli SQL.')
    inserts = batches[1:]
    if not inserts or any(not (re.match(r'^INSERT\s+\[dbo\]\.\[', b, re.I) or
                                   (b.startswith('DECLARE @progressivo_situazione int = 1;\n')
                                    and '\nINSERT [dbo].[situazioni] (' in b)) for b in inserts):
        raise ValueError(f'{percorso}: sono supportati gli INSERT prodotti dal generatore.')
    return inserts


def parametro_odbc(valore):
    return '{' + str(valore).replace('}', '}}') + '}'


def stringa_connessione(database):
    driver = database.get('driver', 'ODBC Driver 18 for SQL Server')
    auth = database.get('autenticazione', 'windows').lower()
    encrypt = database.get('encrypt', True)
    trust = database.get('trust_server_certificate', False)
    if not isinstance(encrypt, bool) or not isinstance(trust, bool):
        raise ValueError('encrypt e trust_server_certificate devono essere booleani JSON.')
    parts = [f'DRIVER={parametro_odbc(driver)}',
             f'SERVER={parametro_odbc(database["server"])}',
             f'DATABASE={parametro_odbc(database["db"])}',
             f'Encrypt={"yes" if encrypt else "no"}',
             f'TrustServerCertificate={"yes" if trust else "no"}']
    if auth == 'windows':
        parts.append('Trusted_Connection=yes')
    elif auth == 'sql':
        username = database.get('username', '')
        password = database.get('password', '')
        if not isinstance(username, str) or not username.strip():
            raise ValueError('Autenticazione SQL: compilare database.username in config.json.')
        if not isinstance(password, str) or not password:
            raise ValueError('Autenticazione SQL: compilare database.password in config.json.')
        parts.extend((f'UID={parametro_odbc(username)}', f'PWD={parametro_odbc(password)}'))
    else:
        raise ValueError('autenticazione deve essere windows oppure sql.')
    return ';'.join(parts) + ';'


def esegui_tutti(connessione, files, notifica=None):
    """Esegue (percorso, batches) con un solo commit finale e rollback globale.

    Richiede una connessione dedicata con autocommit=False.
    I file devono essere già validati da prepara_file.
    """
    if connessione.autocommit is not False:
        raise ValueError('La transazione globale richiede autocommit=False.')
    cursor = connessione.cursor()
    fase = 'impostazioni'
    totale = 0
    completati = 0
    try:
        cursor.execute('SET XACT_ABORT ON; SET NOCOUNT ON;')
        for path, batches in files:
            fase = f'file {path}'
            if notifica:
                notifica(f'IN ESECUZIONE {Path(path).name}')
            for numero, batch in enumerate(batches, 1):
                fase = f'{Path(path).name}, INSERT {numero}/{len(batches)}'
                cursor.execute(batch)
                while cursor.nextset():
                    pass
            totale += len(batches)
            completati += 1
            if notifica:
                notifica(f'ESEGUITO {Path(path).name}: {len(batches)} INSERT, in attesa del commit finale.')
        fase = 'commit'
        connessione.commit()
    except BaseException as errore:
        try:
            connessione.rollback()
        except Exception:
            raise RuntimeError(f'Errore durante {fase}; rollback globale non confermato. '
                               'Verificare il database prima di riprovare.') from errore
        if fase == 'commit':
            raise RuntimeError('Esito del commit incerto; verificare il database prima di riprovare.') from errore
        if isinstance(errore, KeyboardInterrupt):
            raise KeyboardInterrupt('Interrotto: rollback globale eseguito, nessun file confermato.') from errore
        if isinstance(errore, SystemExit):
            raise
        raise RuntimeError(f'{fase} fallito; rollback eseguito su tutti i file del caricamento. {errore}') from errore
    finally:
        # Un errore di chiusura non deve nascondere l'esito della transazione.
        try:
            cursor.close()
        except Exception:
            pass
    return completati, totale


def esegui_file(connessione, batches):
    """Compatibilità per chiamanti che eseguono un singolo file isolato."""
    _, totale = esegui_tutti(connessione, [(Path('script.sql'), batches)])
    return totale
