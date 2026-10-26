import csv,re,unittest
from pathlib import Path
from ordini_sql.csv_reader import completa_setup
from ordini_sql.generators.tasks import costruisci_insert_tasks
from ordini_sql.generators.operazioni import costruisci_insert_operazioni
from ordini_sql.generators.eventi import costruisci_insert_eventi
from ordini_sql.generators.situazioni import costruisci_insert_situazioni
ROOT=Path(__file__).resolve().parent.parent

def values(sql):
    m=re.search(r'INSERT \[dbo\]\.\[\w+\] \((.*?)\)\nVALUES \(\n    (.*?)\n\);',sql,re.S)
    return dict(zip(re.findall(r'\[(\w+)\]',m[1]),m[2].split(',\n    ')))

class CassettePaneTests(unittest.TestCase):
    def row(self):
        with (ROOT/'Ordini_Alba_Tramezzini_Gennaio_2024_3_righe.csv').open(encoding='utf-8-sig') as f:
            row=next(csv.DictReader(f,delimiter=';'))
        row.update(COD_CICLO=' cyc_cassettepane ',QTY_COMPLETATA='48',QTY_RICHIESTA='48',
                   DATA_INIZ_PROG='2024-01-29 23:54:59.000',DATA_FINE_PROG='2024-03-04 23:59:59.000',TEFF_SETUP_MAC='0,02250')
        return completa_setup(row)
    def test_totali_e_quantita(self):
        row=self.row();task=values(costruisci_insert_tasks(row))
        self.assertEqual(values(costruisci_insert_operazioni(row))['NUM_SPLIT'],'CAST(0 AS Numeric(6, 0))')
        operazione=values(costruisci_insert_operazioni(row))
        for campo in ('QTA_SCARTATA','QTA_SOSPESA'):
            self.assertEqual(operazione[campo],'CAST(0.00000 AS Numeric(15, 5))')
        self.assertEqual(task['TOT_LAVORO_MAC'],'CAST(840.00003 AS Numeric(15, 5))')
        self.assertEqual(task['TOT_LAVORO_MAN'],task['TOT_LAVORO_MAC'])
        self.assertEqual(task['TOT_SETUP_MAC'],'CAST(0.08330 AS Numeric(15, 5))')
        self.assertEqual(task['TOT_SETUP_MAN'],task['TOT_SETUP_MAC'])
        for risorsa in ('MAC', 'MAN'):
            self.assertEqual(operazione['T_LAVORO_'+risorsa],'CAST(17.50000 AS Numeric(15, 5))')
            self.assertEqual(operazione['T_SETUP_'+risorsa],task['TOT_SETUP_'+risorsa])
        sql=[costruisci_insert_tasks(row),costruisci_insert_operazioni(row)]+costruisci_insert_situazioni(row)
        for statement in sql:self.assertEqual(values(statement)['QTA_CICLO'],'CAST(2.00000 AS Numeric(15, 5))')
    def test_quantita_ciclo_eventi(self):
        for ciclo in (' cyc_cassettepane ', 'CYC_ALMA', 'CYC_FORNO1'):
            row=self.row();row['COD_CICLO']=ciclo
            eventi=[values(sql) for sql in costruisci_insert_eventi(row)]
            self.assertEqual(len(eventi),8)
            for evento in eventi:
                apertura=evento['EVENTO'] in ("N'OPNS'", "N'OPN'")
                numero='2' if ciclo.strip().upper()=='CYC_CASSETTEPANE' else '0'
                atteso=f'CAST({numero}.00000 AS Numeric(15, 5))' if apertura else 'NULL'
                self.assertEqual(evento['QTA_CICLO'],atteso)

    def test_date_errate(self):
        for data in ('','2024-01-28 00:00:00'):
            row=self.row();row['DATA_FINE_PROG']=data
            with self.assertRaises(ValueError):costruisci_insert_tasks(row)
    def test_altri_cicli_invariati(self):
        row=self.row();row['COD_CICLO']='CYC_ALTRO';v=values(costruisci_insert_tasks(row))
        operazione=values(costruisci_insert_operazioni(row))
        self.assertEqual(operazione['QTA_SCARTATA'],'NULL')
        self.assertEqual(operazione['QTA_SOSPESA'],'NULL')
        for k in ('QTA_CICLO','TOT_LAVORO_MAC','TOT_LAVORO_MAN','TOT_SETUP_MAC'):
            self.assertEqual(v[k],'CAST(0.00000 AS Numeric(15, 5))')

    def test_intervallo_meno_setup(self):
        for fine, atteso in [('2024-01-29 00:05:00.000','0.00003'),
                             ('2024-01-29 01:00:00.000','0.91670'),
                             ('2024-01-30 00:00:00.000','23.91670')]:
            row=self.row()
            row.update(DATA_INIZ_PROG='2024-01-29 00:00:00.000',DATA_FINE_PROG=fine)
            v=values(costruisci_insert_tasks(row))
            self.assertEqual(v['TOT_LAVORO_MAC'],f'CAST({atteso} AS Numeric(15, 5))')
            self.assertEqual(v['TOT_LAVORO_MAN'],v['TOT_LAVORO_MAC'])
        row=self.row();row['DATA_FINE_PROG']=row['DATA_INIZ_PROG']
        with self.assertRaisesRegex(ValueError,'CASSETTEPANE'):
            costruisci_insert_tasks(row)
