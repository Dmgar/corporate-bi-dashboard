import io
from pathlib import Path
from unittest.mock import patch
import pandas as pd
import pytest

from app import process_file
from src.components.custom_builder import sanitize_csv_dataframe
from src.data_generator import generate_data
from src.db_client import DBClient


class _MockUploadedFile(io.BytesIO):
    def __init__(self, content: bytes, name: str) -> None:
        super().__init__(content)
        self.name = name


def test_sanitize_csv_dataframe_neutralizes_formulas() -> None:
    df = pd.DataFrame({
        "producto": ["=CMD|' /C calc'!A0", "+1+1", "-2+3", "@SUM(A1:A2)", "Normal"],
        "revenue": [100.0, 200.0, -50.0, 300.0, 400.0],
    })
    sanitized = sanitize_csv_dataframe(df)

    assert sanitized["producto"].tolist() == [
        "'=CMD|' /C calc'!A0",
        "'+1+1",
        "'-2+3",
        "'@SUM(A1:A2)",
        "Normal",
    ]
    # Numeric values must remain untouched
    assert sanitized["revenue"].tolist() == [100.0, 200.0, -50.0, 300.0, 400.0]


def test_process_file_csv_normalizes_spanish_columns() -> None:
    csv_bytes = b"Fecha,Ventas,Costos,Categoria\n2026-01-10,500,300,Software\n2026-01-15,1000,600,Hardware\n"
    uploaded = _MockUploadedFile(csv_bytes, "reporte.csv")

    df = process_file(uploaded)

    assert df is not None
    assert "date" in df.columns
    assert pd.api.types.is_datetime64_any_dtype(df["date"])
    assert df["revenue"].tolist() == [500, 1000]
    assert df["cost"].tolist() == [300, 600]
    assert df["profit"].tolist() == [200, 400]
    assert df["category"].tolist() == ["Software", "Hardware"]


def test_process_file_rejects_xls_and_invalid_extensions() -> None:
    for filename in ("legacy.xls", "notes.txt"):
        uploaded = _MockUploadedFile(b"dummy", filename)
        with patch("app.st.error") as mock_error:
            result = process_file(uploaded)
        assert result is None
        mock_error.assert_called_once()


def test_generate_data_reproducible_and_readable(tmp_path: Path) -> None:
    db_file = tmp_path / "test_sales.db"
    out_path = generate_data(num_sales=25, seed=123, db_path=str(db_file))

    assert out_path == db_file
    assert db_file.exists()

    client = DBClient(db_path=str(db_file))
    df = client.get_default_data()
    assert len(df) == 25
    assert {"revenue", "cost", "profit", "country", "country_code"}.issubset(df.columns)
