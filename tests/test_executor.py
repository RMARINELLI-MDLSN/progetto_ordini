"""Verifica l'esecutore senza collegarsi a SQL Server."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock
from ordini_sql.executor import separa_batch, prepara_file, stringa_connessione, esegui_file

class ExecutorTests(unittest.TestCase):
    def test_go_fuori_dalle_stringhe(self):
        sql = "SELECT N'prima\nGO\nultima';\nGO\n/* commento\nGO\n*/\nSELECT 2;\nGO -- fine\n"
        batches = separa_batch(sql)
        self.assertEqual(len(batches), 2)
        self.assertIn("prima\nGO\nultima", batches[0])

    def test_database(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'x.sql'
            path.write_text("-- origine\nUSE [test];\nGO\nINSERT [dbo].[ORDINI] ([ORDINE]) VALUES (N'x');\nGO\n")
            self.assertEqual(len(prepara_file(path, 'test')), 1)
            with self.assertRaisesRegex(ValueError, 'diverso'):
                prepara_file(path, 'altro')

    def test_windows(self):
        text = stringa_connessione({'server': 'HOST\\ISTANZA', 'db': 'test'})
        self.assertIn('Trusted_Connection=yes', text)
        self.assertIn('SERVER={HOST\\ISTANZA}', text)

    def test_sql_password_da_config(self):
        text = stringa_connessione({'server':'host', 'db':'test', 'autenticazione':'sql',
                                   'username':'user', 'password':'a};b'})
        self.assertIn('PWD={a}};b}', text)
        self.assertNotIn('Trusted_Connection', text)

    def test_password_mancante(self):
        with self.assertRaisesRegex(ValueError, 'database.password'):
            stringa_connessione({'server':'host', 'db':'test', 'autenticazione':'sql',
                                 'username':'user'})

    def connection(self):
        connection = Mock()
        connection.cursor.return_value.nextset.return_value = False
        return connection

    def test_commit_solo_alla_fine(self):
        connection = self.connection()
        self.assertEqual(esegui_file(connection, ['INSERT uno', 'INSERT due']), 2)
        connection.commit.assert_called_once()
        connection.rollback.assert_not_called()
        self.assertEqual(connection.cursor.return_value.execute.call_count, 3)

    def test_rollback_su_errore(self):
        connection = self.connection()
        connection.cursor.return_value.execute.side_effect = [None, None, RuntimeError('vincolo')]
        with self.assertRaisesRegex(RuntimeError, 'rollback eseguito'):
            esegui_file(connection, ['INSERT uno', 'INSERT due'])
        connection.rollback.assert_called_once()
        connection.commit.assert_not_called()

    def test_commit_incerto(self):
        connection = self.connection()
        connection.commit.side_effect = RuntimeError('connessione persa')
        with self.assertRaisesRegex(RuntimeError, 'incerto'):
            esegui_file(connection, ['INSERT uno'])

    def test_rollback_non_confermato(self):
        connection = self.connection()
        connection.cursor.return_value.execute.side_effect = RuntimeError('errore')
        connection.rollback.side_effect = RuntimeError('connessione persa')
        with self.assertRaisesRegex(RuntimeError, 'rollback non confermato'):
            esegui_file(connection, ['INSERT uno'])
