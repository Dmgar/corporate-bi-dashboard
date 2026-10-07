import streamlit as st
import pandas as pd
import plotly.express as px
from src.db_client import DBClient

st.set_page_config(page_title="Analytics Ventas Avanzado", layout="wide")

# Theme / CSS adjustments
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    div[data-testid="metric-container"] {
        background-color: #FFFFFF;
        border: 1px solid #E1DFDD;
        padding: 15px;
        border-radius: 4px;
        box-shadow: 0 1.6px 3.6px 0 rgba(0,0,0,0.132), 0 0.3px 0.9px 0 rgba(0,0,0,0.108);
    }
    div[data-testid="metric-container"] > div {
        color: #323130;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_default_data():
    client = DBClient()
    return client.get_default_data()

def process_file(uploaded_file):
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    elif uploaded_file.name.endswith(('.xls', '.xlsx')):
        df = pd.read_excel(uploaded_file)
    else:
        st.error("Formato no soportado.")
        return None
    
    # Intento de normalización de nombres de columnas y parseo de fechas
    df.columns = df.columns.str.lower().str.replace(' ', '_')
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
    elif 'fecha' in df.columns:
        df['date'] = pd.to_datetime(df['fecha'], errors='coerce')
        
    return df
    
def render_insights(trends_df, products_df, kpi_df):
    st.subheader(":material/lightbulb: Inteligencia de Negocio & Oportunidades")
    
    col1, col2 = st.columns(2)
    
    # Insight 1: Crecimiento General (Tendencias)
    if trends_df is not None and len(trends_df) >= 2:
        last_month = trends_df.iloc[-1]
        growth = last_month['growth_pct']
        if pd.notna(growth):
            if growth > 0:
                col1.success(f"**Crecimiento Positivo:** Las ventas del último mes ({last_month['month']}) crecieron un **{growth:.1f}%**. ¡Buen momento para escalar campañas!", icon=":material/trending_up:")
            elif growth < 0:
                col1.error(f"**Alerta de Ventas:** Las ventas cayeron un **{abs(growth):.1f}%** en {last_month['month']}. Revisa tu abastecimiento y promociones.", icon=":material/trending_down:")
            else:
                col1.info(f"**Ventas Estables:** Sin crecimiento respecto al mes anterior.", icon=":material/trending_flat:")
                
    # Insight 2: Producto Estrella
    if products_df is not None and not products_df.empty:
        top_product = products_df.loc[products_df['total_profit'].idxmax()]
        col2.info(f"**Producto Estrella:** **{top_product['product_name']}** lidera las utilidades globales con **${top_product['total_profit']:,.2f}**. ¡Asegura su inventario!", icon=":material/star:")
        
        # Insight 3: Oportunidad de Costos (Alto ingreso, bajo margen)
        avg_margin = kpi_df['overall_margin'][0] if 'overall_margin' in kpi_df.columns else products_df['margin_percentage'].mean()
        revenue_threshold = products_df['total_revenue'].quantile(0.8)
        low_margin_products = products_df[(products_df['total_revenue'] >= revenue_threshold) & (products_df['margin_percentage'] < avg_margin)]
        
        if not low_margin_products.empty:
            opp_product = low_margin_products.sort_values('total_revenue', ascending=False).iloc[0]
            st.warning(f"**Oportunidad de Optimización:** El producto **{opp_product['product_name']}** tiene un altísimo volumen de ingresos (${opp_product['total_revenue']:,.2f}), pero su margen de rentabilidad ({opp_product['margin_percentage']:.1f}%) está por debajo del promedio del negocio ({avg_margin:.1f}%). Evalúa renegociar con proveedores o realizar un ajuste ligero de precio para disparar tus ganancias.", icon=":material/tips_and_updates:")

def main():
    st.title(":material/insights: Inteligencia Comercial Corporativa")
    st.markdown("Carga tus propios datos o usa la base de datos simulada local. Explora el rendimiento de forma sencilla.")
    
    # Sidebar
    st.sidebar.header(":material/database: Origen de Datos")
    uploaded_file = st.sidebar.file_uploader("Sube tu archivo (CSV o Excel)", type=['csv', 'xlsx', 'xls'])
    
    if uploaded_file:
        raw_df = process_file(uploaded_file)
        if raw_df is None: return
        st.sidebar.success("Datos cargados correctamente.")
    else:
        raw_df = load_default_data()
        st.sidebar.info("Usando datos locales por defecto (SQLite).")
        
    # Validation
    required_cols = {'revenue', 'cost', 'profit', 'date', 'category'}
    if not required_cols.issubset(set(raw_df.columns)):
        st.warning(f":material/warning: Faltan algunas de estas columnas: {', '.join(required_cols)}.\\nAlgunos gráficos podrían fallar.")

    # Filters
    st.sidebar.header(":material/filter_alt: Filtros Generales")
    
    # Date filter
    min_date = raw_df['date'].min() if 'date' in raw_df.columns else None
    max_date = raw_df['date'].max() if 'date' in raw_df.columns else None
    
    if min_date and max_date:
        start_date, end_date = st.sidebar.date_input("Rango de Fechas", [min_date, max_date], min_value=min_date, max_value=max_date)
    else:
        start_date, end_date = None, None
        
    # Category filter
    if 'category' in raw_df.columns:
        categories = sorted(raw_df['category'].dropna().unique().tolist())
        selected_cats = st.sidebar.multiselect("Categorías", categories, default=categories)
    else:
        selected_cats = None
        
    # Apply filters
    filtered_df = raw_df.copy()
    if start_date and end_date and 'date' in filtered_df.columns:
        filtered_df = filtered_df[(filtered_df['date'] >= pd.to_datetime(start_date)) & (filtered_df['date'] <= pd.to_datetime(end_date))]
    if selected_cats and 'category' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['category'].isin(selected_cats)]
        
    client = DBClient()
    
    # Execution using DuckDB
    try:
        kpi_df = client.execute_advanced_query('kpi_summary.sql', filtered_df)
        trends_df = client.execute_advanced_query('sales_trends.sql', filtered_df) if 'date' in filtered_df.columns else None
        products_df = client.execute_advanced_query('product_performance.sql', filtered_df) if 'category' in filtered_df.columns and 'product_name' in filtered_df.columns else None
    except Exception as e:
        st.error(f"Error al ejecutar las consultas SQL: {e}")
        return

    # Selección de Enfoque (Global o Producto)
    selected_product = "(Vista Global)"
    if products_df is not None and not products_df.empty:
        st.sidebar.divider()
        st.sidebar.subheader(":material/center_focus_strong: Enfoque Específico")
        product_list = ["(Vista Global)"] + sorted(products_df['product_name'].unique().tolist())
        selected_product = st.sidebar.selectbox(":material/search: Buscar o seleccionar producto", product_list)

    if selected_product == "(Vista Global)":
        # KPIs GLOBALES
        st.subheader("Resumen General")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Ingresos", f"${kpi_df['total_revenue'][0]:,.2f}")
        with col2:
            st.metric("Costo Total", f"${kpi_df['total_cost'][0]:,.2f}")
        with col3:
            st.metric("Utilidad Bruta", f"${kpi_df['total_profit'][0]:,.2f}")
        with col4:
            st.metric("Total Transacciones", f"{kpi_df['total_transactions'][0]:,}")
            
        st.divider()
        
        # Inteligencia de Negocio
        render_insights(trends_df, products_df, kpi_df)
        
        st.divider()
        
        # Gráficos de Tendencias y Top Productos
        col_chart1, col_chart2 = st.columns(2)
        with col_chart1:
            if trends_df is not None:
                st.subheader("Tendencia de Ingresos Mensuales")
                fig_trend = px.line(
                    trends_df, x='month', y='total_revenue', markers=True,
                    labels={'month': 'Mes', 'total_revenue': 'Ingresos ($)'},
                    template='plotly_white', color_discrete_sequence=['#118DFF']
                )
                fig_trend.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_trend, use_container_width=True)
                
        with col_chart2:
            if products_df is not None:
                st.subheader("Top 10 Productos Más Rentables")
                top_products = products_df.head(10).sort_values('total_profit', ascending=True)
                fig_prod = px.bar(
                    top_products, y='product_name', x='total_profit', orientation='h',
                    color='category',
                    labels={'product_name': 'Producto', 'total_profit': 'Utilidad ($)', 'category': 'Categoría'},
                    template='plotly_white', color_discrete_sequence=['#118DFF', '#12239E', '#E66C37', '#00B7C3']
                )
                fig_prod.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_prod, use_container_width=True)
                
    else:
        # VISTA ESPECÍFICA POR PRODUCTO
        st.subheader(f":material/inventory: Análisis del Producto: {selected_product}")
        
        prod_data = products_df[products_df['product_name'] == selected_product].iloc[0]
        
        # Product KPIs
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Ingresos Generados", f"${prod_data['total_revenue']:,.2f}")
        with col2:
            st.metric("Utilidad Bruta", f"${prod_data['total_profit']:,.2f}")
        with col3:
            st.metric("Margen de Ganancia", f"{prod_data['margin_percentage']:.1f}%")
        with col4:
            st.metric("Unidades Vendidas", f"{prod_data['items_sold']:,.0f}")
            
        st.divider()
        
        # Product Insights
        st.subheader(":material/lightbulb: Insights del Producto")
        avg_margin = kpi_df['overall_margin'][0] if 'overall_margin' in kpi_df.columns else 25.0
        
        if prod_data['margin_percentage'] > avg_margin:
            st.success(f"**Alta Rentabilidad:** Este producto supera el margen promedio del negocio ({avg_margin:.1f}%). Su venta es estratégica y muy favorable para las ganancias.", icon=":material/thumb_up:")
        else:
            st.warning(f"**Margen Bajo:** La rentabilidad de este producto ({prod_data['margin_percentage']:.1f}%) está por debajo del promedio del negocio ({avg_margin:.1f}%). Se recomienda revisar costos logísticos, de abastecimiento o reevaluar el precio de venta.", icon=":material/warning:")
            
        st.divider()
        
        # Product specific trends
        if 'date' in filtered_df.columns and 'product_name' in filtered_df.columns:
            prod_transactions = filtered_df[filtered_df['product_name'] == selected_product].copy()
            if not prod_transactions.empty:
                prod_transactions['month'] = prod_transactions['date'].dt.strftime('%Y-%m')
                prod_trends = prod_transactions.groupby('month')[['revenue', 'profit']].sum().reset_index()
                
                st.subheader(f"Tendencia Mensual: {selected_product}")
                fig_trend = px.area(
                    prod_trends, x='month', y='revenue', markers=True,
                    labels={'month': 'Mes', 'revenue': 'Ingresos ($)'},
                    template='plotly_white', color_discrete_sequence=['#118DFF']
                )
                fig_trend.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_trend, use_container_width=True)


if __name__ == "__main__":
    main()
