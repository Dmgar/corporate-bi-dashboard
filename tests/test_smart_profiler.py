import pytest
import pandas as pd
from src.components.smart_profiler import SmartProfiler

def test_profile_empty_dataframe() -> None:
    profile = SmartProfiler.profile_dataframe(pd.DataFrame())
    assert profile["row_count"] == 0
    assert profile["numeric_cols"] == []
    assert profile["recommendations"] == []

def test_profile_sample_dataframe(sample_sales_df: pd.DataFrame) -> None:
    profile = SmartProfiler.profile_dataframe(sample_sales_df)
    assert profile["row_count"] == len(sample_sales_df)
    assert "revenue" in profile["metrics"].values()
    assert "profit" in profile["metrics"].values()
    assert len(profile["date_cols"]) >= 1
    assert profile["geo_cols"]["country"] == "country"
    assert len(profile["recommendations"]) > 0

def test_profile_heuristics_spanish_columns() -> None:
    df = pd.DataFrame({
        "fecha_pedido": ["2025-01-01", "2025-01-02"],
        "facturacion": [1200.0, 3400.0],
        "utilidad": [400.0, 1100.0],
        "unidades": [3, 5],
        "pais": ["México", "Colombia"]
    })
    df["fecha_pedido"] = pd.to_datetime(df["fecha_pedido"])
    profile = SmartProfiler.profile_dataframe(df)

    assert "fecha_pedido" in profile["date_cols"]
    assert profile["metrics"]["revenue"] == "facturacion"
    assert profile["metrics"]["profit"] == "utilidad"
    assert profile["metrics"]["quantity"] == "unidades"
    assert profile["geo_cols"]["country"] == "pais"
