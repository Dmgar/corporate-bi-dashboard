import sqlite3
import pandas as pd
from faker import Faker
import random
from datetime import datetime, timedelta

fake = Faker('es_MX')

def generate_data(num_sales=50000):
    print("Iniciando generación de datos...")
    
    # 1. Categories and Products
    categories = {
        'Electrónica': ['Smartphone', 'Laptop', 'Tablet', 'Smartwatch', 'Auriculares', 'Monitor', 'Teclado Mecánico', 'Mouse Gamer'],
        'Electrodomésticos': ['Refrigerador', 'Lavadora', 'Microondas', 'Cafetera', 'Licuadora', 'Aspiradora'],
        'Muebles': ['Silla Ergonómica', 'Escritorio', 'Sofá', 'Mesa de Comedor', 'Estante'],
        'Ropa': ['Camiseta', 'Pantalón', 'Chaqueta', 'Zapatos', 'Gorra', 'Vestido']
    }
    
    products = []
    product_id_counter = 1
    for cat, items in categories.items():
        for item in items:
            # Ropa has high margin, electronics lower margin
            if cat == 'Electrónica':
                cost = round(random.uniform(50, 800), 2)
                margin = random.uniform(1.1, 1.3)
            elif cat == 'Ropa':
                cost = round(random.uniform(5, 40), 2)
                margin = random.uniform(1.5, 3.0)
            else:
                cost = round(random.uniform(20, 300), 2)
                margin = random.uniform(1.3, 1.8)
                
            price = round(cost * margin, 2)
            
            products.append({
                'product_id': product_id_counter,
                'category': cat,
                'product_name': item,
                'unit_cost': cost,
                'unit_price': price
            })
            product_id_counter += 1
            
    df_products = pd.DataFrame(products)
    print(f"Generados {len(df_products)} productos.")
    
    # 2. Stores / Channels
    stores = []
    regions = ['Norte', 'Sur', 'Centro', 'Occidente', 'Oriente']
    for i in range(1, 11):
        is_online = random.random() > 0.7 # 30% online
        stores.append({
            'store_id': i,
            'channel': 'Online' if is_online else 'Offline',
            'region': random.choice(regions),
            'city': fake.city() if not is_online else 'Digital'
        })
    df_stores = pd.DataFrame(stores)
    print(f"Generadas {len(df_stores)} tiendas.")
    
    # 3. Customers
    customers = []
    for i in range(1, 2001):
        customers.append({
            'customer_id': i,
            'name': fake.name(),
            'segment': random.choices(['Retail', 'Corporativo', 'VIP'], weights=[0.7, 0.2, 0.1])[0]
        })
    df_customers = pd.DataFrame(customers)
    print(f"Generados {len(df_customers)} clientes.")
    
    # 4. Sales
    print(f"Generando {num_sales} transacciones de ventas. Esto puede tardar un momento...")
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2025, 12, 31)
    
    sales = []
    for i in range(1, num_sales + 1):
        # random date
        days_between = (end_date - start_date).days
        random_number_of_days = random.randrange(days_between)
        sale_date = start_date + timedelta(days=random_number_of_days)
        
        product = random.choice(products)
        store = random.choice(stores)
        customer = random.choice(customers)
        
        qty = random.choices([1, 2, 3, 4, 5, 10], weights=[0.6, 0.2, 0.1, 0.05, 0.03, 0.02])[0]
        discount = round(random.choices([0, 0.05, 0.1, 0.15, 0.2], weights=[0.7, 0.1, 0.1, 0.05, 0.05])[0], 2)
        
        unit_price = product['unit_price']
        unit_cost = product['unit_cost']
        
        total_revenue = round((unit_price * qty) * (1 - discount), 2)
        total_cost = round(unit_cost * qty, 2)
        profit = round(total_revenue - total_cost, 2)
        
        sales.append({
            'transaction_id': i,
            'date': sale_date.strftime('%Y-%m-%d'),
            'product_id': product['product_id'],
            'store_id': store['store_id'],
            'customer_id': customer['customer_id'],
            'quantity': qty,
            'discount': discount,
            'revenue': total_revenue,
            'cost': total_cost,
            'profit': profit
        })
        
    df_sales = pd.DataFrame(sales)
    
    # Export to SQLite
    print("Guardando datos en data/sales_database.db...")
    conn = sqlite3.connect('data/sales_database.db')
    df_products.to_sql('products', conn, if_exists='replace', index=False)
    df_stores.to_sql('stores', conn, if_exists='replace', index=False)
    df_customers.to_sql('customers', conn, if_exists='replace', index=False)
    df_sales.to_sql('sales', conn, if_exists='replace', index=False)
    conn.close()
    
    print("Base de datos generada exitosamente en 'data/sales_database.db'")

if __name__ == "__main__":
    generate_data(100000)
