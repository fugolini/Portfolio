import unittest
import sqlite3
import sys
import json
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

# Add folder 'src' to the Python path
src_path = str(Path(__file__).parent.parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

mock_config = MagicMock()
# Simulates config file
sys.modules["config"] = mock_config
# Create mock paths 
mock_config.DICTIONARIES_CATALOG = "dummy.json"
mock_config.DICTIONARIES_FOLDER = Path(".")

from database import DictionaryDAO

class TestDatabaseLogic(unittest.TestCase):
    def setUp(self):

        self.fake_catalog = [{
            "name": "TestDB",
            "database_path": ":memory:", # In RAM (:memory:)
            "css_path": "style.css",
            "js_path": "script.js",
            "entries_path": "entries"
        }]

        # Intercept open() calls
        with patch("builtins.open", mock_open(read_data=json.dumps(self.fake_catalog))), \
             patch("pathlib.Path.read_text", return_value="body {color: red;}"):
            
            self.dao = DictionaryDAO()

        self.connection = sqlite3.connect(":memory:")
        self.cursor = self.connection.cursor()

        # Set up minimalistic SQL table
        self.cursor.execute("CREATE TABLE entries (headword TEXT, filename TEXT)")
        self.cursor.executemany(
            "INSERT INTO entries VALUES (?, ?)",
            [("apple", "a.html"), ("application", "b.html"), ("pineapple", "c.html")],
        )

        # Commit the new table to the mock database
        self.connection.commit()
        self.dao.con = self.connection

    def tearDown(self):
        self.connection.close()

    def test_search_priority(self):
        """Verify order of results"""
        word = "app"

        # Original query from DAO
        self.cursor.execute(
            """
            SELECT headword FROM entries WHERE headword LIKE ?
            ORDER BY 
            CASE 
                WHEN headword = ? THEN 0
                WHEN headword LIKE ? THEN 1
                ELSE 2
            END,
            LENGTH(headword)
        """,
            ("%" + word + "%", word, word + "%"),
        )

        results = [r[0] for r in self.cursor.fetchall()]

        # Verify order: apple (5 letters) must come before application (11 letters)
        # pineapple must come last ('app' is just a subset)
        self.assertEqual(results, ["apple", "application", "pineapple"])

    def test_html_not_found(self):
        """Test what happens when the HTML file of a word is missing"""
        with patch("pathlib.Path.exists", return_value=False):
            result = self.dao.fetch_word_html("missing.html")
            self.assertIsNone(result)

if __name__ == "__main__":
    unittest.main()
