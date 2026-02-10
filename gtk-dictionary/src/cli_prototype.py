import sqlite3
from pathlib import Path

TEST_DB = Path('/home/fc/Progetti/Dizionario/db/devoto_oli.sqlite')

def main():
    """Accept a word input and returns the HTML file"""
    
    con = sqlite3.connect(TEST_DB)
    cur = con.cursor()

    print("Welcome to the CLI prototype. Search for a word or input 'q' to exit.")

    while True:
          word_to_search = input('Word: ').strip()
          if word_to_search != 'q':
              cur.execute(
                      "SELECT headword, filename FROM entries WHERE headword = ?",
                      (word_to_search,)
                      )
              results = cur.fetchall()

              if not results:
                  print("No results found.")
              else:
                  for headword, filename in results:    
                      print(f"{headword} -> {filename}") 
          else:
              break
    con.close()

if __name__ == "__main__":
    main()

    



