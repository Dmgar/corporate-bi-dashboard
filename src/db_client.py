import pandas as pd
import sqlite3
import duckdb
import os

class DBClient:
    def __init__(self, db_path: str = "data/sales_database.db") -> None:
        self.db_path: str = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', db_path))

    def _read_sql_file(self, filename: str) -> str:
        filepath = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'sql', filename))
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()

    def get_default_data(self) -> pd.DataFrame:
        """Loads data from the default SQLite db into a flattened Pandas DataFrame."""
        conn = sqlite3.connect(self.db_path)
        
        # Check available columns in stores table
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(stores)")
        store_columns = [col[1] for col in cursor.fetchall()]
        
        geo_fields = []
        if 'country' in store_columns:
            geo_fields.append("st.country")
        if 'country_code' in store_columns:
            geo_fields.append("st.country_code")
        if 'city' in store_columns:
            geo_fields.append("st.city")
        if 'lat' in store_columns and 'lon' in store_columns:
            geo_fields.extend(["st.lat", "st.lon"])
            
        geo_clause = (", " + ", ".join(geo_fields)) if geo_fields else ""

        query = f"""
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
            s.profit{geo_clause}
        FROM sales s
        JOIN products p ON s.product_id = p.product_id
        JOIN stores st ON s.store_id = st.store_id
        JOIN customers c ON s.customer_id = c.customer_id
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        df['date'] = pd.to_datetime(df['date'])

        # Fallback if country is missing
        if 'country' not in df.columns:
            region_to_country = {
                'Norte': ('México', 'MEX'),
                'Centro': ('Colombia', 'COL'),
                'Oriente': ('España', 'ESP'),
                'Sur': ('Argentina', 'ARG'),
                'Occidente': ('Perú', 'PER')
            }
            if 'region' in df.columns:
                df['country'] = df['region'].map(lambda r: region_to_country.get(r, ('México', 'MEX'))[0])
                df['country_code'] = df['region'].map(lambda r: region_to_country.get(r, ('México', 'MEX'))[1])

        return df

    def execute_advanced_query(self, sql_filename: str, df: pd.DataFrame) -> pd.DataFrame:
        """Executes a DuckDB query over the given dataframe 'df' with defensive schema normalization."""
        if df is None or df.empty:
            return pd.DataFrame()

        clean_df = df.copy()

        # 1. Normalización segura de la columna de fecha
        if 'date' in clean_df.columns:
            if not pd.api.types.is_datetime64_any_dtype(clean_df['date']):
                clean_df['date'] = pd.to_datetime(clean_df['date'], errors='coerce')
        else:
            date_candidates = [c for c in clean_df.columns if any(k in str(c).lower() for k in ['date', 'fecha', 'timestamp', 'periodo'])]
            if date_candidates:
                clean_df['date'] = pd.to_datetime(clean_df[date_candidates[0]], errors='coerce')
            else:
                clean_df['date'] = pd.Timestamp.now().normalize()

        # 2. Normalización de métricas financieras clave
        if 'revenue' not in clean_df.columns:
            rev_cand = [c for c in clean_df.columns if any(k in str(c).lower() for k in ['ingreso', 'ventas', 'total_sales', 'facturacion', 'monto'])]
            clean_df['revenue'] = pd.to_numeric(clean_df[rev_cand[0]], errors='coerce').fillna(0) if rev_cand else 0.0
        else:
            clean_df['revenue'] = pd.to_numeric(clean_df['revenue'], errors='coerce').fillna(0)

        if 'cost' not in clean_df.columns:
            cost_cand = [c for c in clean_df.columns if any(k in str(c).lower() for k in ['cost', 'costo'])]
            if cost_cand:
                clean_df['cost'] = pd.to_numeric(clean_df[cost_cand[0]], errors='coerce').fillna(0)
            elif 'profit' in clean_df.columns:
                clean_df['cost'] = clean_df['revenue'] - pd.to_numeric(clean_df['profit'], errors='coerce').fillna(0)
            else:
                clean_df['cost'] = 0.0
        else:
            clean_df['cost'] = pd.to_numeric(clean_df['cost'], errors='coerce').fillna(0)

        if 'profit' not in clean_df.columns:
            prof_cand = [c for c in clean_df.columns if any(k in str(c).lower() for k in ['profit', 'utilidad', 'ganancia', 'beneficio'])]
            if prof_cand:
                clean_df['profit'] = pd.to_numeric(clean_df[prof_cand[0]], errors='coerce').fillna(0)
            else:
                clean_df['profit'] = clean_df['revenue'] - clean_df['cost']
        else:
            clean_df['profit'] = pd.to_numeric(clean_df['profit'], errors='coerce').fillna(0)

        if 'quantity' not in clean_df.columns:
            qty_cand = [c for c in clean_df.columns if any(k in str(c).lower() for k in ['quantity', 'cantidad', 'unidades', 'items', 'volumen', 'qty'])]
            clean_df['quantity'] = pd.to_numeric(clean_df[qty_cand[0]], errors='coerce').fillna(1) if qty_cand else 1
        else:
            clean_df['quantity'] = pd.to_numeric(clean_df['quantity'], errors='coerce').fillna(1)

        # 3. Normalización de dimensiones categóricas
        if 'category' not in clean_df.columns:
            cat_cand = [c for c in clean_df.columns if any(k in str(c).lower() for k in ['categoria', 'categoría', 'category', 'familia', 'linea', 'línea'])]
            clean_df['category'] = clean_df[cat_cand[0]] if cat_cand else 'General'

        if 'product_name' not in clean_df.columns:
            prod_cand = [c for c in clean_df.columns if any(k in str(c).lower() for k in ['producto', 'product', 'articulo', 'artículo', 'item'])]
            clean_df['product_name'] = clean_df[prod_cand[0]] if prod_cand else clean_df['category']

        if 'region' not in clean_df.columns:
            reg_cand = [c for c in clean_df.columns if any(k in str(c).lower() for k in ['region', 'región', 'zona', 'territorio', 'pais', 'país', 'country'])]
            clean_df['region'] = clean_df[reg_cand[0]] if reg_cand else 'General'

        if 'channel' not in clean_df.columns:
            chan_cand = [c for c in clean_df.columns if any(k in str(c).lower() for k in ['channel', 'canal', 'medio'])]
            clean_df['channel'] = clean_df[chan_cand[0]] if chan_cand else 'Directo'

        query = self._read_sql_file(sql_filename)
        query = query.replace("strftime(date,", "strftime(CAST(date AS DATE),")
        query = query.replace("strftime(date ,", "strftime(CAST(date AS DATE),")

        con = duckdb.connect()
        con.register('data_table', clean_df)
        try:
            result_df = con.execute(query).df()
        finally:
            con.close()
        return result_df
