import unittest
from decimal import Decimal
from ordini_sql.csv_reader import completa_setup
from ordini_sql.tempi_previsti import tempo_unitario, setup_previsto
from ordini_sql.generators.tasks import costruisci_insert_tasks
from ordini_sql.generators.operazioni import costruisci_insert_operazioni
import test_minipan
from test_cassettepane import values

class TempiPrevistiTests(unittest.TestCase):
    def row(self,ciclo):
        r=test_minipan.MinipanTests().row()
        r.update(COD_CICLO=ciclo,VALORE01='0',DATA_INIZ_PROG='2024-04-16 00:00:00.000',
                 DATA_FINE_PROG='2024-04-17 00:00:00.000',QTY_CONTATA='15',
                 DATA_EVENTO_UPD='',SETUP_PREVISTO='0,16670')
        return r

    def test_quantita_e_fine_per_tutti_i_cicli(self):
        for ciclo in ('CYC_MINIPAN','CYC_CASSETTEPANE','CIC_SCROSTATORE','CYC_BSTram','CYC_ALMA'):
            for richiesta in ('48','150','300'):
                with self.subTest(ciclo=ciclo,richiesta=richiesta):
                    r=self.row(ciclo);r['QTY_RICHIESTA']=richiesta
                    r=completa_setup(r)
                    self.assertEqual(r['DATA_FINE'],'2024-04-16 23:59:59.000')
                    totale=tempo_unitario(r)*Decimal(richiesta)+setup_previsto(r)
                    self.assertLessEqual(totale,Decimal(24))
                    self.assertGreater(totale,Decimal('23.99'))
                    before=values(costruisci_insert_operazioni(r))
                    task=values(costruisci_insert_tasks(r))
                    r['QTY_COMPLETATA']='999'
                    after=values(costruisci_insert_operazioni(r))
                    for risorsa in ('MAC','MAN'):
                        self.assertEqual(before['T_LAVORO_'+risorsa],after['T_LAVORO_'+risorsa])
                        self.assertEqual(before['T_SETUP_'+risorsa],task['TOT_SETUP_'+risorsa])

    def test_intervalli_e_quantita_invalidi(self):
        for ciclo in ('CYC_CASSETTEPANE','CIC_SCROSTATORE','CYC_BSTram','CYC_ALMA'):
            r=self.row(ciclo);r['QTY_RICHIESTA']='0'
            with self.assertRaises(ValueError):tempo_unitario(r)
            r=self.row(ciclo);r['DATA_FINE_PROG']=r['DATA_INIZ_PROG']
            with self.assertRaises(ValueError):tempo_unitario(r)
            r=self.row(ciclo);r['DATA_FINE_PROG']=r['DATA_INIZIO']
            with self.assertRaises(ValueError):completa_setup(r)

    def test_forni_invariati_con_zero(self):
        for i in range(1,8):
            r=self.row(f'CYC_FORNO{i}')
            r=completa_setup(r)
            self.assertNotEqual(r['DATA_FINE'],'2024-04-16 23:59:59.000')
            op=values(costruisci_insert_operazioni(r))
            task=values(costruisci_insert_tasks(r))
            self.assertEqual(op['T_LAVORO_MAC'],'CAST(0.00000 AS Numeric(15, 5))')
            self.assertEqual(task['TOT_LAVORO_MAC'],'CAST(0.00000 AS Numeric(15, 5))')
