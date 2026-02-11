import sqlite3
import json
import logging
from pathlib import Path
from typing import Optional

from config import (
    DICTIONARIES_CATALOG,
    DICTIONARIES_FOLDER,
)

logger = logging.getLogger(__name__)


class DictionaryDAO:
    """The dictionary Data Access Object"""

    def __init__(self) -> None:
        self.dictionaries = self._load_dictionaries_db()
        self.current_dictionary = self.dictionaries[0]

        self._cache_styles_and_js()
        self.open_dictionary()

    def open_dictionary(self) -> None:
        """Open the dictionary folder with the entries"""
        database_path = DICTIONARIES_FOLDER / self.current_dictionary["database_path"]
        try:
            self.con = sqlite3.connect(database_path)
        except sqlite3.OperationalError:
            logger.error(f"File not found or permission denied: {database_path}")
            raise
        except sqlite3.DatabaseError:
            logger.exception(f"{database_path} is not a valid SQLite database")
            raise
        except Exception as e:
            logger.exception(f"Unforeseen error: {e}")
            raise

    def _load_dictionaries_db(self) -> list[dict]:
        """Load all the dictionaries and relative data"""
        try:
            with open(DICTIONARIES_CATALOG, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error("Dictionary database not found")
            raise
        except Exception as e:
            logger.exception(f"Unforeseen error: {e}")
            raise

    def _cache_styles_and_js(self) -> None:
        """Loads dictionary-specific CSS and JS"""
        self.styles_cache = {}  

        for d in self.dictionaries:
            name = d["name"]
            css_path = DICTIONARIES_FOLDER / d["css_path"]
            js_path = DICTIONARIES_FOLDER / d["js_path"]

            # Cache in memory
            try:
                css_content = css_path.read_text(encoding="utf-8")
                js_content = js_path.read_text(encoding="utf-8")
                self.styles_cache[name] = {"css": css_content, "js": js_content}
            except FileNotFoundError:
                logger.error("Dictionary database not found")
                raise
            except Exception as e:
                logger.error(f"Error loading styles for {name}: {e}")
                self.styles_cache[name] = {"css": "", "js": ""}
                raise

    def get_current_styles(self) -> dict:
        """Fetch the cached style"""
        name = self.current_dictionary["name"]
        return self.styles_cache.get(name, {"css": "", "js": ""})

    def fetch_word_html(self, filename: str) -> Optional[tuple[str, str]]:
        """Fetch the HTML file"""
        # The absolute path of the entry
        filepath = (
            DICTIONARIES_FOLDER / self.current_dictionary["entries_path"] / filename
        )

        if not filepath.exists():
            logger.error(f"Missing entry: {filename}")
            return

        raw_html = filepath.read_text(encoding="utf-8")
        name = self.current_dictionary["name"]
        style = self.styles_cache[name]["css"]

        styled_html = f"<style>{style}</style>\n{raw_html}"
        return styled_html, filepath.as_uri()

    def search(self, word: str) -> list[tuple[str, str]] | bool:
        """Search for the 50 most similar words."""
        cur = self.con.cursor()

        # Search for prefix first, then substring.
        # Prioritize headwords starting with the query
        cur.execute(
            """
                SELECT headword, filename
                FROM entries
                WHERE headword LIKE ?
                ORDER BY 
                CASE 
                WHEN headword = ? THEN 0
                WHEN headword LIKE ? THEN 1
                ELSE 2
                END,
                LENGTH(headword),
                headword
                LIMIT 50
                """,
            ("%" + word + "%", word, word + "%"),
        )
        results = cur.fetchall()

        if not results:
            return False

        return results
