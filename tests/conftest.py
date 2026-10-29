import pytest
import pandas as pd
from datetime import datetime, timedelta

@pytest.fixture
def sample_sales_df() -> pd.DataFrame:
    """Provides a controlled synthetic DataFrame for unit tests."""
    base_date = datetime(2025, 1, 1)
    data = []
    products = [
        ("Electrónica", "Laptop", 1000.0, 700.0),
        ("Electrónica", "Mouse", 50.0, 20.0),
        ("Ropa", "Camiseta", 30.0, 10.0),
        ("Muebles", "Escritorio", 250.0, 150.0),
    ]
    regions = [("México", "MEX", "Norte"), ("Colombia", "COL", "Centro")]

    for i in range(20):
        cat, prod, price, cost = products[i % len(products)]
        country, code, reg = regions[i % len(regions)]
        qty = (i % 3) + 1
        disc = 0.1 if i % 2 == 0 else 0.0
        rev = round((price * qty) * (1 - disc), 2)
        tot_cost = round(cost * qty, 2)
        profit = round(rev - tot_cost, 2)

        data.append({
            "transaction_id": i + 1,
            "date": (base_date + timedelta(days=i * 5)).strftime("%Y-%m-%d"),
            "category": cat,
            "product_name": prod,
            "region": reg,
            "channel": "Online" if i % 2 == 0 else "Offline",
            "segment": "Retail",
            "quantity": qty,
            "discount": disc,
            "revenue": rev,
            "cost": tot_cost,
            "profit": profit,
            "country": country,
            "country_code": code,
        })

    df = pd.DataFrame(data)
    df["date"] = pd.to_datetime(df["date"])
    return df
