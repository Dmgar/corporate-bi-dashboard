import pandas as pd
import sqlite3
import duckdb
import os

class DBClient:
    def __init__(self, db_path="data/sales_database.db"):
        self.db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', db_path))

    def _read_sql_file(self, filename):
        filepath = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'sql', filename))
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()

    def get_default_data(self):
        """Loads data from the default SQLite db into a flattened Pandas DataFrame."""
        conn = sqlite3.connect(self.db_path)
        query = """
        SELECT 
            s.transaction_id,
            s.date,
            p.category,
            p.product_name,
            st.region,
            st.channel,
            c.segment,
            s.quantity,
            s.discount,
            s.revenue,
            s.cost,
            s.profit
        FROM sales s
        JOIN products p ON s.product_id = p.product_id
        JOIN stores st ON s.store_id = st.store_id
        JOIN customers c ON s.customer_id = c.customer_id
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        df['date'] = pd.to_datetime(df['date'])
        return df

    def execute_advanced_query(self, sql_filename, df):
        """Executes a DuckDB query over the given dataframe 'df'."""
        query = self._read_sql_file(sql_filename)
        con = duckdb.connect()
        con.register('data_table', df)
        try:
            result_df = con.execute(query).df()
        finally:
            con.close()
        return result_df
