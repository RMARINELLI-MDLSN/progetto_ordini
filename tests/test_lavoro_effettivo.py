import unittest
from ordini_sql.conversions import lavoro_effettivo_sql
from ordini_sql.generators.tasks import costruisci_insert_tasks
from ordini_sql.generators.operazioni import costruisci_insert_operazioni
from ordini_sql.generators.jobset import costruisci_insert_jobset
import test_minipan
from test_cassettepane import values

class LavoroEffettivoTests(unittest.TestCase):
    def test_formula_tutti_non_forni(self):
        for ciclo in ('CYC_MINIPAN','CYC_CASSETTEPANE','CIC_SCROSTATORE','CYC_BSTram','CYC_ALMA','CYC_ALTRO'):
            row=test_minipan.MinipanTests().row()
            row.update(COD_CICLO=ciclo,VALORE01='0',QTY_CONTATA='10',DATA_INIZIO='2024-04-16 10:00:00',DATA_FINE='2024-04-17 12:30:00',TEFF_SETUP_MAC='0,5')
            for fn in (costruisci_insert_tasks,costruisci_insert_operazioni,costruisci_insert_jobset):
                with self.subTest(ciclo=ciclo,tabella=fn.__name__):
                    v=values(fn(row))
                    self.assertEqual(v['TEFF_LAVORO_MAC'],'CAST(26.00000 AS Numeric(15, 5))')
                    self.assertEqual(v['TEFF_LAVORO_MAN'],v['TEFF_LAVORO_MAC'])

    def test_forni_usano_ancora_valore01(self):
        for i in range(1,8):
            self.assertEqual(lavoro_effettivo_sql({'COD_CICLO':f' cyc_forno{i} ','VALORE01':'12'}),'CAST(0.20000 AS Numeric(15, 5))')

    def test_date_e_setup_invalidi(self):
        base=dict(COD_CICLO='CYC_ALMA',DATA_INIZIO='2024-01-01 00:00:00',DATA_FINE='2024-01-01 01:00:00',TEFF_SETUP_MAC='1')
        self.assertEqual(lavoro_effettivo_sql(base),'CAST(0.00000 AS Numeric(15, 5))')
        for campo,valore in [('DATA_FINE',''),('DATA_FINE','2023-12-31 23:59:59'),('TEFF_SETUP_MAC','2')]:
            row=dict(base);row[campo]=valore
            with self.assertRaises(ValueError):lavoro_effettivo_sql(row)
