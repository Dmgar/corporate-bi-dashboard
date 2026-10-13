import streamlit as st
import pandas as pd
import numpy as np
import re

class SmartProfiler:
    """
    Motor inteligente de análisis de datos y recomendador de visualizaciones de negocio.
    Detecta automáticamente tipos de columnas, calidad y genera recomendaciones contextuales.
    """
    
    @staticmethod
    @st.cache_data(show_spinner=False)
    def profile_dataframe(df: pd.DataFrame) -> dict:
        """Examina un DataFrame y clasifica sus columnas por propósito de negocio."""
        if df is None or df.empty:
            return {
                'row_count': 0,
                'col_count': 0,
                'date_cols': [],
                'geo_cols': {},
                'numeric_cols': [],
                'categorical_cols': [],
                'metrics': {},
                'dimensions': {},
                'recommendations': []
            }
            
        columns_lower = {col: str(col).lower().strip() for col in df.columns}
        
        # 1. Detectar fechas
        date_cols = []
        short_date_tokens = {'mes', 'año', 'anio', 'dia', 'date', 'fecha', 'year', 'month'}
        long_date_substrings = ['timestamp', 'periodo', 'fech']

        for orig_col, lower_col in columns_lower.items():
            if pd.api.types.is_datetime64_any_dtype(df[orig_col]):
                if orig_col not in date_cols:
                    date_cols.append(orig_col)
                continue

            tokens = set(re.split(r'[_\s\-]+', lower_col))
            if bool(tokens & short_date_tokens) or any(sub in lower_col for sub in long_date_substrings):
                if orig_col not in date_cols:
                    date_cols.append(orig_col)
                    
        # 2. Detectar columnas geográficas
        geo_cols = {
            'country': None,
            'country_code': None,
            'region': None,
            'city': None,
            'lat': None,
            'lon': None
        }
        for orig_col, lower_col in columns_lower.items():
            if lower_col in ['country', 'pais', 'país', 'nacion', 'nación'] or ('country' in lower_col and 'code' not in lower_col):
                if not geo_cols['country']: geo_cols['country'] = orig_col
            elif lower_col in ['country_code', 'codigo_pais', 'iso', 'iso3', 'iso_code']:
                if not geo_cols['country_code']: geo_cols['country_code'] = orig_col
            elif any(k in lower_col for k in ['region', 'región', 'zona', 'territorio', 'departamento', 'estado', 'provincia']):
                if not geo_cols['region']: geo_cols['region'] = orig_col
            elif lower_col in ['city', 'ciudad', 'municipio', 'localidad']:
                if not geo_cols['city']: geo_cols['city'] = orig_col
            elif lower_col in ['lat', 'latitude', 'latitud']:
                if not geo_cols['lat']: geo_cols['lat'] = orig_col
            elif lower_col in ['lon', 'lng', 'longitude', 'longitud']:
                if not geo_cols['lon']: geo_cols['lon'] = orig_col
                
        # 3. Detectar métricas numéricas y dimensiones
        numeric_cols = []
        categorical_cols = []
        metrics = {
            'revenue': None,
            'profit': None,
            'cost': None,
            'margin': None,
            'discount': None,
            'quantity': None,
            'price': None
        }
        
        for orig_col, lower_col in columns_lower.items():
            if pd.api.types.is_numeric_dtype(df[orig_col]):
                numeric_cols.append(orig_col)
                if any(k in lower_col for k in ['revenue', 'ingreso', 'ventas', 'total_sales', 'facturacion', 'facturación', 'monto']):
                    if not metrics['revenue']: metrics['revenue'] = orig_col
                elif any(k in lower_col for k in ['profit', 'utilidad', 'ganancia', 'beneficio', 'rentabilidad']):
                    if not metrics['profit']: metrics['profit'] = orig_col
                elif any(k in lower_col for k in ['cost', 'costo']):
                    if not metrics['cost']: metrics['cost'] = orig_col
                elif any(k in lower_col for k in ['margin', 'margen', 'margin_pct', 'pct_margin']):
                    if not metrics['margin']: metrics['margin'] = orig_col
                elif any(k in lower_col for k in ['discount', 'descuento', 'rebaja']):
                    if not metrics['discount']: metrics['discount'] = orig_col
                elif any(k in lower_col for k in ['quantity', 'cantidad', 'unidades', 'items', 'qty', 'volumen']):
                    if not metrics['quantity']: metrics['quantity'] = orig_col
                elif any(k in lower_col for k in ['price', 'precio', 'unit_price', 'precio_unitario']):
                    if not metrics['price']: metrics['price'] = orig_col
            else:
                if orig_col not in date_cols:
                    categorical_cols.append(orig_col)
                    
        # 4. Dimensiones comunes
        dimensions = {
            'product': None,
            'category': None,
            'channel': None,
            'segment': None,
            'customer': None
        }
        for orig_col, lower_col in columns_lower.items():
            if any(k in lower_col for k in ['product', 'producto', 'articulo', 'artículo', 'item']):
                if not dimensions['product']: dimensions['product'] = orig_col
            elif any(k in lower_col for k in ['category', 'categoria', 'categoría', 'familia', 'linea', 'línea']):
                if not dimensions['category']: dimensions['category'] = orig_col
            elif any(k in lower_col for k in ['channel', 'canal', 'medio']):
                if not dimensions['channel']: dimensions['channel'] = orig_col
            elif any(k in lower_col for k in ['segment', 'segmento', 'tipo_cliente']):
                if not dimensions['segment']: dimensions['segment'] = orig_col
            elif any(k in lower_col for k in ['customer', 'cliente', 'comprador']):
                if not dimensions['customer']: dimensions['customer'] = orig_col
                
        # 5. Generar Recomendaciones de Negocio Inteligentes
        recommendations = SmartProfiler._generate_recommendations(df, date_cols, geo_cols, numeric_cols, categorical_cols, metrics, dimensions)
        
        return {
            'row_count': len(df),
            'col_count': len(df.columns),
            'date_cols': date_cols,
            'geo_cols': geo_cols,
            'numeric_cols': numeric_cols,
            'categorical_cols': categorical_cols,
            'metrics': metrics,
            'dimensions': dimensions,
            'recommendations': recommendations
        }

    @staticmethod
    def _generate_recommendations(df, date_cols, geo_cols, numeric_cols, categorical_cols, metrics, dimensions) -> list:
        recs = []
        
        # Recomendación 1: Mapa Coroplético Territorial
        has_geo = any(geo_cols[k] is not None for k in ['country', 'country_code', 'region'])
        if has_geo:
            target_geo = geo_cols['country'] or geo_cols['region'] or geo_cols['country_code']
            recs.append({
                'id': 'choropleth_map',
                'title': 'Mapa Coroplético de Penetración Territorial',
                'badge': 'Estratégico · Expansión Geográfica',
                'icon': ':material/public:',
                'why': f"Tu dataset contiene variables geográficas ('{target_geo}'). Un mapa coroplético te permite identificar de un vistazo las zonas con mayor concentración de ingresos y aquellos territorios desatendidos con potencial de crecimiento.",
                'suggested_view': 'Mapa Coroplético',
                'detected_cols': [c for c in [target_geo, metrics['revenue'], metrics['profit']] if c],
                'target_tab_index': 1
            })

        # Recomendación 2: Dispersión y Elasticidad de Descuentos
        if metrics['discount'] and (metrics['profit'] or metrics['revenue'] or metrics['margin']):
            y_col = metrics['margin'] or metrics['profit'] or metrics['revenue']
            recs.append({
                'id': 'scatter_discount_margin',
                'title': 'Gráfico de Dispersión: Impacto de Descuentos en Rentabilidad',
                'badge': 'Financiero · Política de Precios',
                'icon': ':material/scatter_plot:',
                'why': f"Detectamos columna de descuentos ('{metrics['discount']}') y rentabilidad ('{y_col}'). Correlacionar ambas variables en un gráfico de dispersión revela si los descuentos están dinamizando las ventas o canibalizando el margen neto de tu negocio.",
                'suggested_view': 'Matriz de Dispersión',
                'detected_cols': [metrics['discount'], y_col],
                'target_tab_index': 2
            })
            
        # Recomendación 3: Matriz Cuadrante BCG (Margen vs Volumen)
        product_col = dimensions['product'] or dimensions['category']
        vol_col = metrics['quantity'] or metrics['revenue']
        margin_col = metrics['profit'] or metrics['margin']
        if product_col and vol_col and margin_col:
            recs.append({
                'id': 'bcg_matrix',
                'title': 'Matriz Estratégica BCG: Cuadrantes de Margen vs Volumen',
                'badge': 'Portafolio · Toma de Decisiones',
                'icon': ':material/grid_view:',
                'why': f"Tienes productos ('{product_col}') con métricas de volumen y margen. Clasificarlos en cuadrantes (Estrellas, Vacas Lecheras, Oportunidades y En Riesgo) permite renegociar costos o descatalogar artículos improductivos.",
                'suggested_view': 'Matriz de Dispersión',
                'detected_cols': [product_col, vol_col, margin_col],
                'target_tab_index': 2
            })

        # Recomendación 4: Comparador de Benchmarking A vs B
        dim_comp = dimensions['category'] or dimensions['channel'] or dimensions['segment'] or (categorical_cols[0] if categorical_cols else None)
        if dim_comp and (metrics['revenue'] or metrics['profit']):
            recs.append({
                'id': 'entity_comparator',
                'title': f"Comparador de Benchmarking A vs B ({dim_comp.title()})",
                'badge': 'Operativo · Eficiencia de Canales/Categorías',
                'icon': ':material/compare_arrows:',
                'why': f"La dimensión '{dim_comp}' tiene múltiples grupos. Comparar dos elementos cara a cara (ej. Tienda Física vs Online o Categoría A vs B) te ayuda a estandarizar mejores prácticas y reasignar presupuestos comerciales.",
                'suggested_view': 'Comparador Multidimensional',
                'detected_cols': [dim_comp, metrics['revenue']],
                'target_tab_index': 3
            })

        # Recomendación 5: Análisis Temporal MoM y Comparador de Períodos
        if date_cols and metrics['revenue']:
            recs.append({
                'id': 'period_comparator',
                'title': 'Comparador de Períodos Temporales (Mes vs Mes / Rango)',
                'badge': 'Dirección · Crecimiento y Variaciones',
                'icon': ':material/calendar_month:',
                'why': f"Con la columna temporal ('{date_cols[0]}') puedes auditar variaciones interperiódicas de ingresos, costos y márgenes con tarjetas de deltas (Δ) para entender qué catalizó el crecimiento reciente.",
                'suggested_view': 'Comparador Multidimensional',
                'detected_cols': [date_cols[0], metrics['revenue']],
                'target_tab_index': 3
            })

        # Recomendación 6: Regla de Pareto (80/20)
        if product_col and metrics['revenue']:
            recs.append({
                'id': 'pareto_analysis',
                'title': 'Análisis de Concentración de Pareto (Curva 80/20)',
                'badge': 'Gestión de Inventario · Riesgo Comercial',
                'icon': ':material/leaderboard:',
                'why': f"Evalúa si el 20% de tus '{product_col}' concentra el 80% de tus ingresos. La concentración excesiva representa un riesgo operativo que debe mitigarse diversificando el catálogo.",
                'suggested_view': 'Recomendador & Visual Studio',
                'detected_cols': [product_col, metrics['revenue']],
                'target_tab_index': 4
            })

        return recs
