import pytest
import pandas as pd
from src.db_client import DBClient

def test_db_client_instantiation() -> None:
    client = DBClient()
    assert client.db_path.endswith("sales_database.db")

def test_db_client_read_sql_file() -> None:
    client = DBClient()
    sql_content = client._read_sql_file("kpi_summary.sql")
    assert "SUM(revenue)" in sql_content
    assert "FROM data_table" in sql_content

def test_execute_advanced_query_kpi_summary(sample_sales_df: pd.DataFrame) -> None:
    client = DBClient()
    res = client.execute_advanced_query("kpi_summary.sql", sample_sales_df)

    assert not res.empty
    assert "total_revenue" in res.columns
    assert "total_profit" in res.columns
    assert "overall_margin" in res.columns
    assert res["total_revenue"].iloc[0] > 0
    assert res["total_transactions"].iloc[0] == len(sample_sales_df)

def test_execute_advanced_query_sales_trends(sample_sales_df: pd.DataFrame) -> None:
    client = DBClient()
    res = client.execute_advanced_query("sales_trends.sql", sample_sales_df)

    assert not res.empty
    assert "month" in res.columns
    assert "total_revenue" in res.columns
    assert "cumulative_revenue" in res.columns

def test_execute_advanced_query_empty_df() -> None:
    client = DBClient()
    res = client.execute_advanced_query("kpi_summary.sql", pd.DataFrame())
    assert res.empty

def test_defensive_schema_normalization() -> None:
    """Verifies that DBClient auto-normalizes Spanish columns to English standards."""
    client = DBClient()
    spanish_df = pd.DataFrame([
        {"ventas": 500.0, "costos": 300.0, "fecha": "2025-01-10", "categoria": "Tecnologia"},
        {"ventas": 1000.0, "costos": 600.0, "fecha": "2025-01-15", "categoria": "Tecnologia"},
    ])
    res = client.execute_advanced_query("kpi_summary.sql", spanish_df)
    assert not res.empty
    assert res["total_revenue"].iloc[0] == 1500.0
    assert res["total_cost"].iloc[0] == 900.0
    assert res["total_profit"].iloc[0] == 600.0
