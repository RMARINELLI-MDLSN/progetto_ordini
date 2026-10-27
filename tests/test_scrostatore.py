import json
import re
import unittest
from pathlib import Path
from ordini_sql.csv_reader import leggi_ordini, completa_setup
from ordini_sql.generators.ordini import costruisci_insert
from ordini_sql.generators.tasks import costruisci_insert_tasks
from ordini_sql.generators.operazioni import costruisci_insert_operazioni
from ordini_sql.generators.jobset import costruisci_insert_jobset
from ordini_sql.generators.eventi import costruisci_insert_eventi
from ordini_sql.generators.situazioni import costruisci_insert_situazioni
from ordini_sql.generators.fprocessdata import costruisci_insert_fprocessdata
from test_cassettepane import values
ROOT=Path(__file__).resolve().parent.parent

def raw(sql):
    if sql=='NULL':return ''
    m=re.fullmatch(r'CAST\((.*?)\s+AS\s+.*\)',sql,re.I|re.S)
    if m:sql=m[1]
    if sql.startswith("N'"):sql=sql[1:]
    if sql.startswith("'"):
        sql=sql[1:-1].replace("''", "'")
        if re.match(r'\d{4}-\d{2}-\d{2}T',sql):sql=sql.replace('T',' ')
    return sql

class ScrostatoreTests(unittest.TestCase):
    def row(self):return next(leggi_ordini(ROOT/'Ordini_GASPERINI_20062024.csv'))

    def test_modello_con_nuovi_tempi_previsti(self):
        originali=json.loads((ROOT/'tests/fixtures/gasperini.json').read_text())
        for tabella,fn in [('ORDINI',costruisci_insert),('TASKS',costruisci_insert_tasks),('OPERAZIONI',costruisci_insert_operazioni),('JOBSET',costruisci_insert_jobset)]:
            with self.subTest(tabella=tabella):
                attesi = originali[tabella][0].copy()
                if tabella in ('TASKS', 'OPERAZIONI', 'JOBSET'):
                    attesi.update(TEFF_LAVORO_MAC='0.07250', TEFF_LAVORO_MAN='0.07250')
                if tabella == 'TASKS':
                    attesi.update(TOT_LAVORO_MAC='2.00052', TOT_LAVORO_MAN='2.00052')
                if tabella == 'OPERAZIONI':
                    attesi.update(T_LAVORO_MAC='0.16671', T_LAVORO_MAN='0.16671')
                self.assertEqual({k:raw(v) for k,v in values(fn(self.row())).items()},attesi)

    def test_eventi_e_situazioni(self):
        row=self.row()
        self.assertEqual(row['DATA_FINE'],'2024-06-20 16:42:47.000')
        eventi=[{k:raw(v) for k,v in values(s).items()} for s in costruisci_insert_eventi(row)]
        self.assertEqual(len(eventi),8)
        for tipo in ('MAC','OPE'):
            subset=[r for r in eventi if r['TIPO_OGGETTO']==tipo]
            self.assertEqual([r['EVENTO'] for r in subset],['OPNS','CLSS','OPN','CLS'])
            self.assertEqual([r['ORA_EVENTO'][-12:] for r in subset],['16:37:45.000','16:38:26.000','16:38:42.000','16:42:47.000'])
            self.assertEqual([r['QTA_CONTATA'] for r in subset],['','','','15.00000'])
            self.assertEqual([r['QTA_COMPLETATA'] for r in subset],['0.00000']*3+['8.00000'])
            self.assertEqual({r['UTENTE'] for r in subset},{'ADMIN'})
            self.assertEqual({r['OGGETTO'] for r in subset},{'SCROSTATORE' if tipo=='MAC' else 'OPE_SCROST'})
        situazioni=[{k:raw(v) for k,v in values(s).items()} for s in costruisci_insert_situazioni(row)]
        self.assertEqual(len(situazioni),6)
        for tipo in ('MAC','OPE'):
            subset=[r for r in situazioni if r['TIPO_OGGETTO']==tipo]
            self.assertEqual([r['TIPO'] for r in subset],['WSET','WORK','WORK'])
            self.assertEqual([r['LAVORO'] for r in subset],['0.00000','0.06667','0.00139'])
            self.assertEqual([r['SETUP'] for r in subset],['0.01139','0.00000','0.00000'])
            self.assertEqual([r['QTA_CONTATA'] for r in subset],['0.00000','14.00000','1.00000'])
            self.assertEqual([r['QTA_COMPLETATA'] for r in subset],['0.00000','8.00000','0.00000'])
            self.assertEqual({r['FINSDATE'] for r in subset},{row['FINSDATE_'+tipo]})
            self.assertEqual([r['CHIUSURA'] for r in subset],['','','O' if tipo=='MAC' else ''])
        self.assertEqual(list(costruisci_insert_fprocessdata(row)),[])

    def test_senza_upd_e_validazione(self):
        row=self.row();row['DATA_EVENTO_UPD']=''
        self.assertEqual(len(costruisci_insert_eventi(completa_setup(row))),8)
        self.assertEqual(len(costruisci_insert_situazioni(completa_setup(row))),4)
        for campo,valore in [('QTY_CONTATA',''),('QTY_CONTATA_UPD','16'),('QTY_COMPLETATA_UPD','9'),('DATA_EVENTO_UPD','2024-06-20 16:42:48')]:
            row=self.row();row[campo]=valore
            with self.subTest(campo=campo),self.assertRaises(ValueError):completa_setup(row)

    def test_csv_standard_scr(self):
        row=next(leggi_ordini(ROOT/'Ordini_SCR.csv'))
        self.assertEqual(row['QTY_CONTATA'],'140')
        self.assertEqual(row['CHIUSURA_ATTREZZAGGIO'],'2024-06-20 16:38:26.000')
        self.assertEqual(row['INIZIO_LAVORAZIONE'],'2024-06-20 16:38:31.000')
        self.assertEqual(row['DATA_FINE'],'2024-06-20 23:59:58.000')
        task={k:raw(v) for k,v in values(costruisci_insert_tasks(row)).items()}
        self.assertEqual(task['CICLI_CONTATI'],'140.00000')
        self.assertEqual(task['TOT_LAVORO_MAC'],'2.00052')
        op={k:raw(v) for k,v in values(costruisci_insert_operazioni(row)).items()}
        self.assertEqual(op['T_LAVORO_MAC'],'0.00666')
        eventi=[{k:raw(v) for k,v in values(s).items()} for s in costruisci_insert_eventi(row)]
        self.assertEqual(len(eventi),8)
        for e in eventi:
            self.assertNotEqual(e['EVENTO'],'UPD')
            if e['EVENTO']=='CLS':
                self.assertEqual(e['QTA_CONTATA'],'140.00000')
                self.assertEqual(e['QTA_COMPLETATA'],'140.00000')
        situazioni=costruisci_insert_situazioni(row)
        self.assertEqual(len(situazioni),4)
