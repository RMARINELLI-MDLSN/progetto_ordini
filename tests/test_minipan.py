import csv
import unittest
from pathlib import Path
from ordini_sql.csv_reader import completa_setup
from ordini_sql.generators.tasks import costruisci_insert_tasks
from ordini_sql.generators.operazioni import costruisci_insert_operazioni
from test_cassettepane import values

class MinipanTests(unittest.TestCase):
    def row(self):
        with (Path(__file__).resolve().parent.parent/'Ordini_MINIPAN_160424.csv').open(encoding='utf-8-sig') as f:
            row=next(csv.DictReader(f,delimiter=';'))
        row.update(COD_CICLO=' cyc_minipan ',DATA_INIZ_PROG='2024-04-16 23:30:00',DATA_FINE_PROG='2024-04-17 01:00:00')
        return completa_setup(row)

    def test_tempi_e_quantita(self):
        row=self.row()
        task=values(costruisci_insert_tasks(row))
        op=values(costruisci_insert_operazioni(row))
        for risorsa in ('MAC','MAN'):
            self.assertEqual(task['TOT_SETUP_'+risorsa],'CAST(0.08330 AS Numeric(15, 5))')
            self.assertEqual(task['TOT_LAVORO_'+risorsa],'CAST(1.41670 AS Numeric(15, 5))')
            self.assertEqual(op['T_LAVORO_'+risorsa],'CAST(0.00944 AS Numeric(15, 5))')
            self.assertEqual(op['T_SETUP_'+risorsa],task['TOT_SETUP_'+risorsa])
        self.assertEqual(task['FVALUE01'],'CAST(10.00000 AS Numeric(15, 5))')
        row['QUANTITA01']='7,5'
        self.assertEqual(values(costruisci_insert_tasks(row))['FVALUE01'],'CAST(7.50000 AS Numeric(15, 5))')

    def test_intervallo_insufficiente(self):
        row=self.row();row['DATA_FINE_PROG']=row['DATA_INIZ_PROG']
        with self.assertRaisesRegex(ValueError,'MINIPAN'):
            costruisci_insert_tasks(row)

    def test_ciclo_non_gestito_invariato(self):
        row=self.row();row['COD_CICLO']='CYC_ALTRO'
        task=values(costruisci_insert_tasks(row));op=values(costruisci_insert_operazioni(row))
        for risorsa in ('MAC','MAN'):
            self.assertEqual(task['TOT_SETUP_'+risorsa],'CAST(0.00000 AS Numeric(15, 5))')
            self.assertEqual(task['TOT_LAVORO_'+risorsa],'CAST(0.00000 AS Numeric(15, 5))')
            self.assertEqual(op['T_LAVORO_'+risorsa],'CAST(0.00000 AS Numeric(15, 5))')
            self.assertEqual(op['T_SETUP_'+risorsa],'CAST(0.00000 AS Numeric(15, 5))')
        self.assertEqual(task['FVALUE01'],'NULL')

    def test_zero_e_quantita_variabile(self):
        from decimal import Decimal
        from ordini_sql.tempi_previsti import tempo_unitario
        row=self.row()
        row.update(VALORE01='0', DATA_INIZ_PROG='2024-04-16 00:00:00', DATA_FINE_PROG='2024-04-17 00:00:00')
        row=completa_setup(row)
        self.assertEqual(row['DATA_FINE'],'2024-04-16 23:59:59.000')
        for q in ('150', '300'):
            row['QTY_RICHIESTA']=q
            totale=tempo_unitario(row)*Decimal(q)+Decimal('0.08330')
            self.assertLessEqual(totale,Decimal(24))
            self.assertGreater(totale,Decimal('23.99'))
        row['QTY_RICHIESTA']='0'
        with self.assertRaises(ValueError):costruisci_insert_operazioni(row)
        row['DATA_FINE_PROG']=row['INIZIO_LAVORAZIONE']
        with self.assertRaises(ValueError):completa_setup(row)
