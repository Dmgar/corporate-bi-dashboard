import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from typing import Optional, Any
from src.db_client import DBClient

# Importación de Componentes Modulares Avanzados
from src.components.smart_profiler import SmartProfiler
from src.components.geo_map import render_geo_analytics
from src.components.scatter_matrix import render_scatter_analytics
from src.components.comparator import render_comparator_analytics
from src.components.floating_filters import render_floating_filters
from src.components.smart_recommender_ui import render_smart_recommender
from src.components.custom_builder import render_custom_builder

st.set_page_config(
    page_title="Corporate BI Studio · Analytics Avanzado",
    page_icon=":material/analytics:",
    layout="wide"
)

# Estilos Corporativos Premium estilo Power BI / Tableau
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Tarjetas KPI Corporativas */
    div[data-testid="metric-container"] {
        background-color: #FFFFFF;
        border: 1px solid #E1DFDD;
        padding: 16px 20px;
        border-radius: 8px;
        box-shadow: 0 1.6px 3.6px 0 rgba(0,0,0,0.06), 0 0.3px 0.9px 0 rgba(0,0,0,0.04);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    div[data-testid="metric-container"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px 0 rgba(0,0,0,0.1);
    }
    div[data-testid="metric-container"] > div {
        color: #323130;
    }
    div[data-testid="metric-container"] label {
        font-weight: 600;
        color: #605E5C;
    }
    
    /* Pestañas de navegación estilizadas */
    button[data-baseweb="tab"] {
        font-size: 0.95rem;
        font-weight: 600;
        padding: 10px 18px;
    }
    
    /* Contenedor de Alertas */
    .stAlert {
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_default_data() -> pd.DataFrame:
    client = DBClient()
    return client.get_default_data()

def process_file(uploaded_file: Any) -> Optional[pd.DataFrame]:
    """Carga y normaliza archivos subidos por el usuario de manera inteligente."""
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(uploaded_file)
        else:
            st.error("Formato no soportado. Por favor sube un archivo CSV o Excel.")
            return None
    except Exception as e:
        st.error(f"Error al leer el archivo: {e}")
        return None
    
    # Normalización de nombres de columnas
    df.columns = df.columns.str.lower().str.replace(' ', '_').str.strip()
    
    # Normalización inteligente de fechas
    date_candidates = ['date', 'fecha', 'timestamp', 'periodo', 'transaction_date', 'order_date']
    for candidate in date_candidates:
        if candidate in df.columns:
            df['date'] = pd.to_datetime(df[candidate], errors='coerce')
            break
            
    # Mapeo inteligente de métricas financieras clave
    col_mapping = {
        'ingresos': 'revenue', 'ventas': 'revenue', 'total_sales': 'revenue', 'facturacion': 'revenue',
        'costos': 'cost', 'costo': 'cost',
        'utilidad': 'profit', 'ganancia': 'profit', 'beneficio': 'profit',
        'cantidad': 'quantity', 'unidades': 'quantity', 'qty': 'quantity',
        'descuento': 'discount', 'rebaja': 'discount',
        'producto': 'product_name', 'articulo': 'product_name', 'item': 'product_name',
        'categoria': 'category', 'familia': 'category',
        'pais': 'country', 'país': 'country',
        'ciudad': 'city', 'region': 'region', 'región': 'region'
    }
    for old_col, new_col in col_mapping.items():
        if old_col in df.columns and new_col not in df.columns:
            df[new_col] = df[old_col]
            
    # Autocálculo de profit si faltara pero se cuenta con revenue y cost
    if 'revenue' in df.columns and 'cost' in df.columns and 'profit' not in df.columns:
        df['profit'] = df['revenue'] - df['cost']
        
    return df

def render_insights(
    trends_df: Optional[pd.DataFrame],
    products_df: Optional[pd.DataFrame],
    kpi_df: Optional[pd.DataFrame]
) -> None:
    st.subheader(":material/lightbulb: Inteligencia de Negocio & Oportunidades")
    
    col1, col2 = st.columns(2)
    
    # Insight 1: Crecimiento General (Tendencias)
    if trends_df is not None and len(trends_df) >= 2:
        last_month = trends_df.iloc[-1]
        growth = last_month.get('growth_pct', None)
        if pd.notna(growth):
            if growth > 0:
                col1.success(f"**Crecimiento Positivo:** Las ventas del último mes ({last_month['month']}) crecieron un **{growth:.1f}%**. ¡Buen momento para escalar campañas!", icon=":material/trending_up:")
            elif growth < 0:
                col1.error(f"**Alerta de Ventas:** Las ventas cayeron un **{abs(growth):.1f}%** en {last_month['month']}. Revisa tu abastecimiento y promociones.", icon=":material/trending_down:")
            else:
                col1.info(f"**Ventas Estables:** Sin crecimiento significativo respecto al mes anterior.", icon=":material/trending_flat:")
                
    # Insight 2: Producto Estrella
    if products_df is not None and not products_df.empty:
        top_product = products_df.loc[products_df['total_profit'].idxmax()]
        col2.info(f"**Producto Estrella:** **{top_product['product_name']}** lidera las utilidades globales con **${top_product['total_profit']:,.2f}**. ¡Asegura su inventario!", icon=":material/star:")
        
        # Insight 3: Oportunidad de Costos (Alto ingreso, bajo margen)
        avg_margin = kpi_df['overall_margin'][0] if ('overall_margin' in kpi_df.columns and len(kpi_df) > 0) else products_df['margin_percentage'].mean()
        revenue_threshold = products_df['total_revenue'].quantile(0.8)
        low_margin_products = products_df[(products_df['total_revenue'] >= revenue_threshold) & (products_df['margin_percentage'] < avg_margin)]
        
        if not low_margin_products.empty:
            opp_product = low_margin_products.sort_values('total_revenue', ascending=False).iloc[0]
            st.warning(f"**Oportunidad de Optimización:** El producto **{opp_product['product_name']}** tiene un altísimo volumen de ingresos (${opp_product['total_revenue']:,.2f}), pero su margen de rentabilidad ({opp_product['margin_percentage']:.1f}%) está por debajo del promedio del negocio ({avg_margin:.1f}%). Evalúa renegociar con proveedores o realizar un ajuste ligero de precio para disparar tus ganancias.", icon=":material/tips_and_updates:")

def main() -> None:
    # Encabezado Principal y Branding
    st.title(":material/insights: Corporate BI Studio · Analytics Avanzado")
    st.markdown("Plataforma interactiva de inteligencia comercial y toma de decisiones corporativas.")
    
    # Sidebar: Carga y Conexión de Datos
    st.sidebar.header(":material/database: Origen de Datos")
    uploaded_file = st.sidebar.file_uploader("Sube tu archivo (CSV o Excel)", type=['csv', 'xlsx', 'xls'])
    
    if uploaded_file:
        raw_df = process_file(uploaded_file)
        if raw_df is None: return
        st.sidebar.success(f"Archivo cargado: **{uploaded_file.name}** ({len(raw_df):,} registros)")
        data_source_badge = f":material/upload_file: Archivo Subido: `{uploaded_file.name}`"
    else:
        raw_df = load_default_data()
        st.sidebar.info("Usando base de datos corporativa local (SQLite).")
        data_source_badge = ":material/database: Base de Datos Local: `sales_database.db`"

    # Perfilado Inteligente del Conjunto de Datos
    profiler_info = SmartProfiler.profile_dataframe(raw_df)

    # Filtros Tradicionales en Sidebar
    st.sidebar.divider()
    st.sidebar.header(":material/filter_alt: Filtros Globales")
    
    min_date = raw_df['date'].min() if ('date' in raw_df.columns and pd.api.types.is_datetime64_any_dtype(raw_df['date'])) else None
    max_date = raw_df['date'].max() if ('date' in raw_df.columns and pd.api.types.is_datetime64_any_dtype(raw_df['date'])) else None
    
    start_date, end_date = None, None
    if min_date and max_date:
        date_range = st.sidebar.date_input(
            "Rango de Fechas",
            [min_date, max_date],
            min_value=min_date,
            max_value=max_date,
            key="sidebar_date_picker"
        )
        if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
            start_date, end_date = date_range
        
    if 'category' in raw_df.columns:
        categories = sorted(raw_df['category'].dropna().unique().tolist())
        selected_cats = st.sidebar.multiselect("Categorías", categories, default=categories, key="sidebar_cat_sel")
    else:
        selected_cats = None
        
    # Aplicar filtros base del sidebar
    sidebar_filtered = raw_df.copy()
    if start_date and end_date and 'date' in sidebar_filtered.columns:
        sidebar_filtered = sidebar_filtered[(sidebar_filtered['date'] >= pd.to_datetime(start_date)) & (sidebar_filtered['date'] <= pd.to_datetime(end_date))]
    if selected_cats and 'category' in sidebar_filtered.columns:
        sidebar_filtered = sidebar_filtered[sidebar_filtered['category'].isin(selected_cats)]

    # ========================================================
    # BARRA FLOTANTE DE FILTROS RÁPIDOS (STICKY / TOP RIBBON)
    # ========================================================
    filtered_df = render_floating_filters(sidebar_filtered, profiler_info)

    if filtered_df.empty:
        st.warning("No hay transacciones que coincidan con los filtros seleccionados. Ajusta o limpia los filtros para continuar.", icon=":material/filter_alt_off:")
        return

    # Actualizar profiler sobre el subconjunto filtrado
    active_profile = SmartProfiler.profile_dataframe(filtered_df)

    # Cálculos analíticos con DuckDB o Fallback Pandas
    client = DBClient()
    kpi_df = None
    trends_df = None
    products_df = None
    
    # 1. KPIs
    try:
        kpi_df = client.execute_advanced_query('kpi_summary.sql', filtered_df)
    except Exception:
        # Fallback pandas seguro si DuckDB encuentra discrepancias en nombres
        rev_sum = filtered_df['revenue'].sum() if 'revenue' in filtered_df.columns else 0
        cost_sum = filtered_df['cost'].sum() if 'cost' in filtered_df.columns else 0
        prof_sum = filtered_df['profit'].sum() if 'profit' in filtered_df.columns else (rev_sum - cost_sum)
        tx_count = len(filtered_df)
        kpi_df = pd.DataFrame([{
            'total_revenue': rev_sum,
            'total_cost': cost_sum,
            'total_profit': prof_sum,
            'total_transactions': tx_count,
            'overall_margin': ((prof_sum / rev_sum) * 100) if rev_sum > 0 else 0
        }])

    # 2. Tendencias
    if 'date' in filtered_df.columns:
        try:
            trends_df = client.execute_advanced_query('sales_trends.sql', filtered_df)
        except Exception:
            tdf = filtered_df.dropna(subset=['date']).copy()
            if not tdf.empty:
                tdf['month'] = tdf['date'].dt.strftime('%Y-%m')
                trends_df = tdf.groupby('month').agg({'revenue': 'sum', 'profit': 'sum'}).reset_index()
                trends_df = trends_df.rename(columns={'revenue': 'total_revenue', 'profit': 'total_profit'})
                trends_df['prev_month_revenue'] = trends_df['total_revenue'].shift(1)
                trends_df['growth_pct'] = ((trends_df['total_revenue'] - trends_df['prev_month_revenue']) / trends_df['prev_month_revenue'].replace(0, pd.NA)) * 100

    # 3. Productos
    if 'category' in filtered_df.columns and 'product_name' in filtered_df.columns:
        try:
            products_df = client.execute_advanced_query('product_performance.sql', filtered_df)
        except Exception:
            pdf = filtered_df.groupby(['category', 'product_name']).agg({
                'revenue': 'sum',
                'profit': 'sum',
                'quantity': 'sum' if 'quantity' in filtered_df.columns else 'count'
            }).reset_index().rename(columns={
                'revenue': 'total_revenue',
                'profit': 'total_profit',
                'quantity': 'items_sold'
            })
            pdf['margin_percentage'] = (pdf['total_profit'] / pdf['total_revenue'].replace(0, pd.NA) * 100).fillna(0)
            products_df = pdf.sort_values('total_profit', ascending=False)

    # ========================================================
    # NAVEGACIÓN PRINCIPAL POR PESTAÑAS (TABS CORPORATIVAS)
    # ========================================================
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        ":material/dashboard: Dashboard Ejecutivo",
        ":material/public: Mapa Coroplético & Geografía",
        ":material/scatter_plot: Matriz de Dispersión & Cuadrantes",
        ":material/balance: Comparador Multidimensional",
        ":material/auto_awesome: Recomendador & Visual Studio"
    ])

    # ========================================================
    # TAB 1: DASHBOARD EJECUTIVO & RESUMEN
    # ========================================================
    with tab1:
        # Selección de Enfoque (Global o Producto)
        selected_product = "(Vista Global)"
        if products_df is not None and not products_df.empty:
            st.sidebar.divider()
            st.sidebar.subheader(":material/center_focus_strong: Enfoque Específico")
            product_list = ["(Vista Global)"] + sorted(products_df['product_name'].unique().tolist())
            selected_product = st.sidebar.selectbox(":material/search: Buscar o seleccionar producto", product_list)

        if selected_product == "(Vista Global)":
            st.subheader("Resumen Ejecutivo de Negocio")
            
            # Tarjetas Principales de KPI con protección contra None
            rev_val = float(kpi_df['total_revenue'].iloc[0] or 0)
            cost_val = float(kpi_df['total_cost'].iloc[0] or 0)
            profit_val = float(kpi_df['total_profit'].iloc[0] or 0)
            tx_val = int(kpi_df['total_transactions'].iloc[0] or 0)
            margin_val = float(kpi_df['overall_margin'].iloc[0] or 0) if 'overall_margin' in kpi_df.columns else ((profit_val / rev_val * 100) if rev_val > 0 else 0)

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Ingresos", f"${rev_val:,.2f}")
            with col2:
                st.metric("Costo Total", f"${cost_val:,.2f}")
            with col3:
                st.metric("Utilidad Bruta", f"${profit_val:,.2f}", delta=f"{margin_val:.1f}% Margen", delta_color="normal")
            with col4:
                st.metric("Total Transacciones", f"{tx_val:,}")
                
            st.divider()
            
            # Alertas e Inteligencia de Negocio
            render_insights(trends_df, products_df, kpi_df)
            
            st.divider()
            
            # Gráficos de Tendencias y Top Productos
            col_chart1, col_chart2 = st.columns(2)
            with col_chart1:
                if trends_df is not None and not trends_df.empty:
                    st.subheader("Tendencia de Ingresos Mensuales")
                    fig_trend = px.line(
                        trends_df, x='month', y='total_revenue', markers=True,
                        labels={'month': 'Mes', 'total_revenue': 'Ingresos ($)'},
                        template='plotly_white', color_discrete_sequence=['#118DFF']
                    )
                    fig_trend.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig_trend, use_container_width=True)
                else:
                    st.info("No hay datos de fecha suficientes para trazar la tendencia mensual.")
                    
            with col_chart2:
                if products_df is not None and not products_df.empty:
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
                    st.info("Se requiere información de categoría y producto para mostrar el ranking de productos.")
        else:
            # Vista Específica por Producto
            st.subheader(f":material/inventory: Análisis Detallado del Producto: {selected_product}")
            prod_data = products_df[products_df['product_name'] == selected_product].iloc[0]
            
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
            
            st.subheader(":material/lightbulb: Insights del Producto")
            avg_margin = kpi_df['overall_margin'][0] if ('overall_margin' in kpi_df.columns and len(kpi_df) > 0) else 25.0
            
            if prod_data['margin_percentage'] > avg_margin:
                st.success(f"**Alta Rentabilidad:** Este producto supera el margen promedio del negocio ({avg_margin:.1f}%). Su venta es estratégica y muy favorable para las ganancias.", icon=":material/thumb_up:")
            else:
                st.warning(f"**Margen Bajo:** La rentabilidad de este producto ({prod_data['margin_percentage']:.1f}%) está por debajo del promedio del negocio ({avg_margin:.1f}%). Se recomienda revisar costos logísticos, de abastecimiento o reevaluar el precio de venta.", icon=":material/warning:")
                
            st.divider()
            
            if 'date' in filtered_df.columns and 'product_name' in filtered_df.columns:
                prod_transactions = filtered_df[filtered_df['product_name'] == selected_product].copy()
                if not prod_transactions.empty:
                    prod_transactions['month'] = prod_transactions['date'].dt.strftime('%Y-%m')
                    prod_trends = prod_transactions.groupby('month')[['revenue', 'profit']].sum().reset_index()
                    
                    st.subheader(f"Tendencia Mensual: {selected_product}")
                    fig_prod_trend = px.area(
                        prod_trends, x='month', y='revenue', markers=True,
                        labels={'month': 'Mes', 'revenue': 'Ingresos ($)'},
                        template='plotly_white', color_discrete_sequence=['#118DFF']
                    )
                    fig_prod_trend.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig_prod_trend, use_container_width=True)

    # ========================================================
    # TAB 2: MAPA COROPLÉTICO & GEOGRAFÍA
    # ========================================================
    with tab2:
        render_geo_analytics(filtered_df, active_profile)

    # ========================================================
    # TAB 3: MATRIZ DE DISPERSIÓN & CUADRANTES BCG
    # ========================================================
    with tab3:
        render_scatter_analytics(filtered_df, active_profile)

    # ========================================================
    # TAB 4: COMPARADOR MULTIDIMENSIONAL & BENCHMARKING
    # ========================================================
    with tab4:
        render_comparator_analytics(filtered_df, active_profile)

    # ========================================================
    # TAB 5: RECOMENDADOR & VISUAL STUDIO
    # ========================================================
    with tab5:
        subtab_rec, subtab_studio = st.tabs([
            ":material/recommend: Recomendaciones de Negocio",
            ":material/palette: Estudio de Gráficos Libres"
        ])
        with subtab_rec:
            render_smart_recommender(filtered_df, active_profile)
        with subtab_studio:
            render_custom_builder(filtered_df, active_profile)

if __name__ == "__main__":
    main()
