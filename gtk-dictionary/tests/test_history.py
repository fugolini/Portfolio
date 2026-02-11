import unittest
import sys
from pathlib import Path

src_path = str(Path(__file__).parent.parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from history_manager import HistoryManager


class TestHistory(unittest.TestCase):
    def setUp(self):
        self.hm = HistoryManager()

    def test_navigation(self):
        """Verifica il flusso Avanti/Indietro"""
        self.hm.add("apple.html")
        self.hm.add("pear.html")
        self.hm.add("banana.html")

        # From banana, go back
        self.assertEqual(self.hm.back(), "pear.html")
        self.assertEqual(self.hm.back(), "apple.html")

        # End of history
        self.assertIsNone(self.hm.back())

        # Move forward
        self.assertEqual(self.hm.forward(), "pear.html")

        # Insert a new word in the middle 
        # (forward branch of history must disapppear)
        self.hm.add("oranges.html")
        self.assertIsNone(self.hm.forward())


if __name__ == "__main__":
    unittest.main()
