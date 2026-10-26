import csv,re,tempfile,unittest
from pathlib import Path
from ordini_sql.quantita import applica_quantita
from ordini_sql.service import genera_script
from ordini_sql.executor import prepara_file
ROOT=Path(__file__).resolve().parent.parent
class QuantitaTests(unittest.TestCase):
    def test_validazione_e_forni(self):
        for err in ('-1','abc','NaN',''):
            with self.subTest(err=err),self.assertRaises(ValueError):
                applica_quantita({},dict(COD_CICLO='CYC_ALMA',QTY_COMPLETATA=err,QTY_RICHIESTA='60'))
        with self.assertRaisesRegex(ValueError,'QTY_COMPLETATA'):
            applica_quantita({},dict(COD_CICLO='CYC_MINIPAN'))
        for i in range(1,8):
            v={'QTA_COMPLETATA':'originale','QTA_RICHIESTA':'originale'}
            applica_quantita(v,{'COD_CICLO':f' cyc_forno{i} ','QTY_COMPLETATA':'errato'})
            self.assertEqual(set(v.values()),{'originale'})
    def test_tutte_le_query(self):
        with (ROOT/'Ordini_Alba_Tramezzini_Gennaio_2024_3_righe.csv').open(encoding='utf-8-sig') as f:
            row=next(csv.DictReader(f,delimiter=';'))
        for ciclo,c,r in [('CYC_MINIPAN','150','150'),('CYC_ALMA','30','60')]:
            row.update(COD_CICLO=ciclo,QTY_COMPLETATA=c,QTY_RICHIESTA=r,QUANTITA1="10",QUANTITA2="7.5",CENTRO_ASSEGNATO="CDL_TEST")
            with tempfile.TemporaryDirectory() as folder:
                p=Path(folder)/'input.csv'
                with p.open('w',encoding='utf-8-sig',newline='') as f:
                    w=csv.DictWriter(f,fieldnames=list(row),delimiter=';');w.writeheader();w.writerow(row)
                result=genera_script({'file_csv':p,'database':{'db':'test'}})
                batches=prepara_file(result[0][0],'test');self.assertEqual(len(batches),16)
                for b in batches:
                    m=re.search(r'INSERT \[dbo\]\.\[(\w+)\] \((.*?)\)\nVALUES \(\n    (.*?)\n\);',b,re.S)
                    self.assertIsNotNone(m)
                    table=m[1].upper();v=dict(zip(re.findall(r'\[(\w+)\]',m[2]),m[3].split(',\n    ')))
                    if 'QTA_CONTATA' in v:
                        expected_contata = ('CAST(0.00000 AS Numeric(15, 5))' if table == 'TASKS'
                                            else 'NULL' if table == 'JOBSET' else v['QTA_COMPLETATA'])
                        self.assertEqual(v['QTA_CONTATA'], expected_contata)
                    if table == 'ORDINI':
                        self.assertEqual(v['QTA_VERSATA'],v['QTA_COMPLETATA'])
                        self.assertEqual(v['QTA_LANCIATA'],v['QTA_RICHIESTA'])
                    if table == 'TASKS':
                        self.assertEqual(v['CICLI_CONTATI'],f'CAST({c}.00000 AS Numeric(15, 5))')
                    if table == 'OPERAZIONI':
                        self.assertEqual(v['CENTRO_REALE'], v['CENTRO_ASSEGNATO'])
                        self.assertEqual(v['NUM_SPLIT'], 'CAST(0 AS Numeric(6, 0))' if ciclo == 'CYC_MINIPAN' else 'NULL')
                    for campo,numero in [('QUANTITA1','10.00000'),('QUANTITA2','7.50000')]:
                        if campo in v:
                            attivo=(table not in ('EVENTI','SITUAZIONI') or
                                    (table=='EVENTI' and v['EVENTO']=="N'CLS'") or
                                    (table=='SITUAZIONI' and v['TIPO']=="N'WORK'"))
                            expected=f'CAST({numero} AS Numeric(15, 5))' if ciclo=='CYC_MINIPAN' and attivo else ('NULL' if table=='EVENTI' else 'CAST(0.00000 AS Numeric(15, 5))')
                            self.assertEqual(v[campo],expected)
                    if 'QTA_RICHIESTA' in v:self.assertEqual(v['QTA_RICHIESTA'],f'CAST({r}.00000 AS Numeric(15, 5))')
                    if 'QTA_COMPLETATA' in v:
                        expected=c
                        if table=='EVENTI' and v['EVENTO']!="N'CLS'":expected='0'
                        if table=='SITUAZIONI' and v['TIPO']=="N'WSET'":expected='0'
                        self.assertEqual(v['QTA_COMPLETATA'],f'CAST({expected}.00000 AS Numeric(15, 5))')

    def test_situazioni_csv_reali(self):
        from ordini_sql.csv_reader import leggi_ordini
        from ordini_sql.generators.situazioni import costruisci_insert_situazioni
        for nome, completata, richiesta in (
            ('Ordini_MINIPAN_160424.csv', '150.00000', '150.00000'),
            ('Ordini_ALMA_19032025.csv', '30.00000', '60.00000'),
        ):
            with self.subTest(csv=nome):
                row=next(leggi_ordini(ROOT/nome))
                sql=costruisci_insert_situazioni(row)
                self.assertEqual(len(sql),4)
                observed=set()
                for batch in sql:
                    m=re.search(r'INSERT \[dbo\]\.\[situazioni\] \((.*?)\)\nVALUES \(\n    (.*?)\n\);',batch,re.S)
                    v=dict(zip(re.findall(r'\[(\w+)\]',m[1]),m[2].split(',\n    ')))
                    observed.add((v['TIPO_OGGETTO'],v['TIPO']))
                    self.assertEqual(v['QTA_RICHIESTA'],f'CAST({richiesta} AS Numeric(15, 5))')
                    value=completata if v['TIPO']=="N'WORK'" else '0.00000'
                    self.assertEqual(v['QTA_COMPLETATA'],f'CAST({value} AS Numeric(15, 5))')
                    self.assertEqual(v['QTA_CONTATA'],v['QTA_COMPLETATA'])
                    self.assertIn('@progressivo_situazione',v['PROGRESSIVO'])
                self.assertEqual(observed,{("N'MAC'","N'WSET'"),("N'MAC'","N'WORK'"),("N'OPE'","N'WSET'"),("N'OPE'","N'WORK'")})
