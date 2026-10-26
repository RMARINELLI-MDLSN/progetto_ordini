import unittest
from ordini_sql.generators.fprocessdata import costruisci_insert_fprocessdata

class ProcessDataTests(unittest.TestCase):
    def test_cicli_ammessi(self):
        for i in range(1, 8):
            with self.subTest(ciclo=i):
                row = dict(COD_CICLO=f" cyc_forno{i} ", MACCHINA="M1", TASK="T1",
                           VALORE01="2", VALORE02="230", DATA_INIZIO="2024-01-10 09:00:00")
                sql = list(costruisci_insert_fprocessdata(row))
                self.assertEqual(len(sql), 2)
                self.assertIn("2024-01-10T09:01:00.000", sql[0])
                self.assertIn("2024-01-10T09:02:00.000", sql[1])

    def test_cicli_esclusi_senza_dati_processo(self):
        for ciclo in ("CYC_FORNO0", "CYC_FORNO8", "CYC_FORNO10", "CYC_FORNO01",
                      "CYC_FORNI1", "ALTRO", ""):
            with self.subTest(ciclo=ciclo):
                self.assertEqual(list(costruisci_insert_fprocessdata({"COD_CICLO": ciclo})), [])
