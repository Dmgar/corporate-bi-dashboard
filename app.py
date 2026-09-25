import streamlit as st
import plotly.express as px
from src.db_client import DBClient

st.set_page_config(page_title="Analytics Ventas", layout="wide")

# Theme / CSS adjustments
st.markdown("""
<style>
    /* Estilos globales y ocultar branding de streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Mejoras para las tarjetas de métricas */
    div[data-testid="metric-container"] {
        background-color: rgba(28, 28, 30, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 5% 5% 5% 10%;
        border-radius: 10px;
        color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    client = DBClient()
    kpi_df = client.execute_query('kpi_summary.sql')
    trends_df = client.execute_query('sales_trends.sql')
    products_df = client.execute_query('product_performance.sql')
    return kpi_df, trends_df, products_df

def main():
    st.title("Dashboard Fénix: Análisis de Ventas")
    st.markdown("Bienvenido al panel interactivo de ventas. Aquí podrás monitorear el desempeño de la compañía de manera dinámica.")
    
    # Load Data
    with st.spinner("Ejecutando consultas SQL locales..."):
        kpi_df, trends_df, products_df = load_data()
        
    # KPIs
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
    
    # Gráficos
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.subheader("Tendencia Mensual")
        fig_trend = px.area(
            trends_df, 
            x='month', 
            y='total_revenue', 
            markers=True,
            title='Ingresos Históricos',
            labels={'month': 'Mes', 'total_revenue': 'Ingresos ($)'},
            template='plotly_dark',
            color_discrete_sequence=['#00D2FF']
        )
        fig_trend.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_trend, use_container_width=True)
        
    with col_chart2:
        st.subheader("Top Rentabilidad")
        top_products = products_df.head(10).sort_values('total_profit', ascending=True)
        fig_prod = px.bar(
            top_products, 
            y='product_name', 
            x='total_profit', 
            orientation='h',
            color='category',
            title='Top 10 Productos Más Rentables',
            labels={'product_name': 'Producto', 'total_profit': 'Utilidad ($)', 'category': 'Categoría'},
            template='plotly_dark'
        )
        fig_prod.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_prod, use_container_width=True)

    # Tabla Detallada
    st.subheader("Rendimiento Detallado por Producto")
    st.dataframe(products_df.style.format({
        'total_revenue': '${:,.2f}',
        'total_profit': '${:,.2f}',
        'margin_percentage': '{:.2f}%'
    }), use_container_width=True, height=400)

if __name__ == "__main__":
    main()
