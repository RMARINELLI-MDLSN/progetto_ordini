"""Esegue i file SQL sul database indicato in config.json.

Uso: python esegui_sql.py
Controllo senza connessione: python esegui_sql.py --verifica
"""
import argparse
from pathlib import Path

from ordini_sql.config import carica_config
from ordini_sql.executor import prepara_file, stringa_connessione, esegui_file


def main():
    parser = argparse.ArgumentParser(description='Esegue gli SQL sul database di config.json.')
    parser.add_argument('--config', type=Path, default=Path(__file__).resolve().with_name('config.json'))
    parser.add_argument('--cartella', type=Path, help='Cartella SQL alternativa; relativa alla cartella corrente.')
    parser.add_argument('--file', type=Path, help='Esegue un solo file SQL, ad esempio per ripartire dopo un errore.')
    parser.add_argument('--verifica', action='store_true', help='Valida i file senza collegarsi al database.')
    args = parser.parse_args()
    if args.file and args.cartella:
        parser.error('Usare --file oppure --cartella, non entrambi.')
    connessione = None
    completati = 0
    totale = 0
    try:
        config = carica_config(args.config)
        db = config['database']
        csv_path = config['file_csv']
        cartella = args.cartella or csv_path.parent / (csv_path.stem + '_sql')
        if args.file:
            files = [args.file.resolve()]
        else:
            if not cartella.is_dir():
                raise ValueError(f'Cartella SQL non trovata: {cartella}. Eseguire prima leggi_ordini.py.')
            files = sorted(cartella.glob('*.sql'), key=lambda p: p.name)
        if not files:
            raise ValueError(f'Nessun file .sql in {cartella}.')
        # Valida tutti i file prima di aprire la connessione e fare modifiche.
        pronti = [(path, prepara_file(path, db['db'])) for path in files]
        print(f"Destinazione: {db['server']} / {db['db']}")
        if args.verifica:
            for path, batches in pronti:
                print(f'VALIDO {path.name}: {len(batches)} INSERT')
            print(f'{len(pronti)} file verificati. Nessuna connessione aperta.')
            return
        connection_string = stringa_connessione(db)
        try:
            import pyodbc
        except ImportError:
            raise ValueError('Manca pyodbc. Eseguire: python -m pip install -r requirements.txt') from None
        driver = db.get('driver', 'ODBC Driver 18 for SQL Server')
        if driver not in pyodbc.drivers():
            raise ValueError(f'Driver ODBC non installato: {driver}. Installarlo o configurare database.driver.')
        connessione = pyodbc.connect(connection_string, autocommit=False, timeout=15)
        for path, batches in pronti:
            print(f'IN ESECUZIONE {path.name}', flush=True)
            conteggio = esegui_file(connessione, batches)
            completati += 1
            totale += conteggio
            print(f'OK {path.name}: {conteggio} INSERT, commit eseguito.', flush=True)
        print(f'Completati {completati} file, {totale} INSERT.')
    except KeyboardInterrupt:
        parser.exit(130, f'Interrotto. File già confermati: {completati}.\n')
    except Exception as errore:
        parser.exit(1, f'ERRORE: {errore}\nFile già confermati: {completati}. Esecuzione fermata.\n')
    finally:
        if connessione is not None:
            connessione.close()


if __name__ == '__main__':
    main()
