"""Confronta gli SQL con il riferimento verificato e le correzioni autorizzate."""
import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from ordini_sql.config import carica_config
from ordini_sql.service import genera_script
from ordini_sql.conversions import minuti_in_ore_sql

ROOT = Path(__file__).resolve().parent.parent

class RegressionTests(unittest.TestCase):
    def test_output_identico(self):
        config = carica_config(ROOT / "config.json")
        expected = json.loads((ROOT / "tests/expected_hashes.json").read_text())
        with tempfile.TemporaryDirectory() as folder:
            csv_path = Path(folder) / "ordini.csv"
            shutil.copyfile(ROOT / "Ordini_Alba_Tramezzini_Gennaio_2024_3_righe.csv", csv_path)
            config["file_csv"] = csv_path
            results = genera_script(config)
            self.assertEqual(len(results), 3)
            self.assertEqual(sum(count for _, count in results), 84)
            actual = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path, _ in results}
            self.assertEqual(actual, expected)

    def test_minuti_in_ore(self):
        self.assertEqual(minuti_in_ore_sql("12"), "CAST(0.20000 AS Numeric(15, 5))")
        self.assertEqual(minuti_in_ore_sql("1"), "CAST(0.01667 AS Numeric(15, 5))")

if __name__ == "__main__":
    unittest.main()
