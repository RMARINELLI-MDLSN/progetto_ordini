import unittest
from ordini_sql.csv_reader import completa_setup

class SetupTests(unittest.TestCase):
    def test_genovese_arrotondamento(self):
        row = completa_setup({'VALORE01':'12','WSET_WORK':'5','DATA_INIZIO':'2024-01-10 09:03:00.000','TEFF_SETUP_MAC':'0.01389'})
        self.assertEqual(row['TEFF_SETUP_MAN'], '0.01389')
        self.assertEqual(row['CHIUSURA_ATTREZZAGGIO'], '2024-01-10 09:03:50.000')
        self.assertEqual(row['INIZIO_LAVORAZIONE'], '2024-01-10 09:03:55.000')

    def test_vecchi_campi_sostituiti(self):
        row = completa_setup({'VALORE01':'12','WSET_WORK':'5','DATA_INIZIO':'2024-01-10 23:59:50.000','TEFF_SETUP_MAC':'0,00750',
                              'TEFF_SETUP_MAN':'99','CHIUSURA_ATTREZZAGGIO':'obsoleto','INIZIO_LAVORAZIONE':'obsoleto'})
        self.assertEqual(row['TEFF_SETUP_MAN'], '0,00750')
        self.assertEqual(row['CHIUSURA_ATTREZZAGGIO'], '2024-01-11 00:00:17.000')
        self.assertEqual(row['INIZIO_LAVORAZIONE'], '2024-01-11 00:00:22.000')

    def test_negativo_rifiutato(self):
        with self.assertRaises(ValueError):
            completa_setup({'VALORE01':'12','WSET_WORK':'5','DATA_INIZIO':'2024-01-10 09:03:00.000','TEFF_SETUP_MAC':'-1'})

    def test_pausa_negativa(self):
        with self.assertRaises(ValueError):
            completa_setup({'VALORE01':'12','DATA_INIZIO':'2024-01-10 09:03:00.000',
                            'TEFF_SETUP_MAC':'0.00750','WSET_WORK':'-1'})

    def test_pausa_zero(self):
        row = completa_setup({'VALORE01':'12','DATA_INIZIO':'2024-01-10 09:03:00.000',
                              'TEFF_SETUP_MAC':'0.00750','WSET_WORK':'0'})
        self.assertEqual(row['INIZIO_LAVORAZIONE'], row['CHIUSURA_ATTREZZAGGIO'])

    def test_data_fine_derivata(self):
        row = completa_setup({'DATA_INIZIO':'2024-01-10 09:03:00.000',
                              'TEFF_SETUP_MAC':'0.01389','WSET_WORK':'5',
                              'VALORE01':'12','DATA_FINE':'vecchio valore'})
        self.assertEqual(row['DATA_FINE'], '2024-01-10 09:16:45.000')

    def test_fine_cambio_giorno(self):
        row = completa_setup({'DATA_INIZIO':'2024-01-10 23:59:00.000',
                              'TEFF_SETUP_MAC':'0.00750','WSET_WORK':'5','VALORE01':'4'})
        self.assertEqual(row['DATA_FINE'], '2024-01-11 00:03:59.000')

    def test_troncamento_mezzo_secondo(self):
        row = completa_setup({'DATA_INIZIO':'2024-01-10 23:59:59.500',
                              'TEFF_SETUP_MAC':'0','WSET_WORK':'0','VALORE01':'1'})
        self.assertEqual(row['CHIUSURA_ATTREZZAGGIO'], '2024-01-10 23:59:59.000')
        self.assertEqual(row['DATA_FINE'], '2024-01-11 00:00:59.000')

    def test_setup_secondi_per_difetto(self):
        # 0.01416 ore = 50.976 secondi: deve aggiungere 50, mai 51.
        row = completa_setup({'DATA_INIZIO':'2024-01-10 09:03:00.900',
                              'TEFF_SETUP_MAC':'0.01416','WSET_WORK':'5.7','VALORE01':'12'})
        self.assertEqual(row['CHIUSURA_ATTREZZAGGIO'], '2024-01-10 09:03:50.000')
        self.assertEqual(row['DATA_FINE'], '2024-01-10 09:16:45.000')
