import sqlite3
import pandas as pd
import os

class DBClient:
    def __init__(self, db_path="data/sales_database.db"):
        # Resolve path relative to project root
        self.db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', db_path))

    def _read_sql_file(self, filename):
        filepath = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'sql', filename))
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()

    def execute_query(self, sql_filename):
        query = self._read_sql_file(sql_filename)
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
