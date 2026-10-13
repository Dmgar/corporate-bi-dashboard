import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

def render_smart_recommender(df: pd.DataFrame, profiler_info: dict):
    st.subheader(":material/auto_awesome: Motor de Recomendación de Visuales de Negocio")
    st.markdown("El sistema analiza la estructura de tus datos y te sugiere las visualizaciones más valiosas para la toma de decisiones estratégicas.")

    recs = profiler_info.get('recommendations', [])
    metrics = profiler_info.get('metrics', {})
    dimensions = profiler_info.get('dimensions', {})

    # 1. Resumen de tu Negocio
    col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
    with col_stat1:
        st.metric("Ventas Registradas", f"{profiler_info.get('row_count', len(df)):,}", help="Número total de transacciones analizadas.")
    with col_stat2:
        st.metric("Datos de Dinero y Cantidad", len(profiler_info.get('numeric_cols', [])), help="Ventas, costos, ganancias, precios y unidades detectadas.")
    with col_stat3:
        st.metric("Grupos (Productos, Canales)", len(profiler_info.get('categorical_cols', [])), help="Familias de productos, clientes y canales identificados.")
    with col_stat4:
        geo_count = sum(1 for v in profiler_info.get('geo_cols', {}).values() if v is not None)
        st.metric("Ciudades y Países", geo_count, help="Variables de ubicación geográfica reconocidas.")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### :material/recommend: Visualizaciones Recomendadas para tu Negocio")

    if not recs:
        st.info("Tus datos tienen una estructura estándar. Explora las pestañas superiores o crea tus propios gráficos en el Estudio de Visuales.")
    else:
        # Renderizar tarjetas de recomendaciones en columnas de 2 en 2
        for i in range(0, len(recs), 2):
            cols = st.columns(2)
            for j in range(2):
                if i + j < len(recs):
                    rec = recs[i + j]
                    with cols[j]:
                        with st.container(border=True):
                            st.caption(f"**{rec['badge']}**")
                            st.markdown(f"##### {rec['icon']} {rec['title']}")
                            st.write(rec['why'])
                            
                            cols_str = ", ".join([f"`{c}`" for c in rec['detected_cols']])
                            st.caption(f"Columnas detectadas: {cols_str}")
                            
                            btn_label = f"Explorar en pestaña '{rec['suggested_view']}'"
                            if st.button(
                                f":material/arrow_forward: {btn_label}",
                                key=f"btn_rec_{rec['id']}",
                                help=f"Ve a la pestaña '{rec['suggested_view']}' en la barra superior para interactuar con este análisis.",
                                use_container_width=True
                            ):
                                target_idx = rec.get('target_tab_index', 0)
                                js_nav = f"""
                                <script>
                                    const tabs = window.parent.document.querySelectorAll('button[data-baseweb="tab"]');
                                    if (tabs && tabs[{target_idx}]) {{
                                        tabs[{target_idx}].click();
                                        tabs[{target_idx}].scrollIntoView({{behavior: 'smooth'}});
                                    }}
                                </script>
                                """
                                components.html(js_nav, height=0, width=0)

    # 2. Análisis Automatizado de Pareto (Regla 80/20)
    st.divider()
    st.subheader(":material/equalizer: Análisis de Concentración de Pareto (Curva 80/20)")
    st.markdown("Identifica el subconjunto crítico de tu catálogo que genera el mayor impacto en tus ventas.")

    prod_col = dimensions.get('product') or dimensions.get('category') or (profiler_info.get('categorical_cols', [None])[0])
    rev_col = metrics.get('revenue') or ('revenue' if 'revenue' in df.columns else None)

    if prod_col and rev_col and prod_col in df.columns and rev_col in df.columns:
        pareto_df = df.groupby(prod_col)[rev_col].sum().reset_index()
        pareto_df = pareto_df.sort_values(rev_col, ascending=False).reset_index(drop=True)
        
        total_rev = pareto_df[rev_col].sum()
        pareto_df['cum_rev'] = pareto_df[rev_col].cumsum()
        pareto_df['cum_pct'] = (pareto_df['cum_rev'] / total_rev) * 100
        pareto_df['rank'] = pareto_df.index + 1
        pareto_df['rank_pct'] = (pareto_df['rank'] / len(pareto_df)) * 100

        # Encontrar cuántos productos representan el 80%
        items_80 = pareto_df[pareto_df['cum_pct'] <= 80]
        count_80 = len(items_80) + 1 if len(items_80) < len(pareto_df) else len(pareto_df)
        pct_catalog_80 = (count_80 / len(pareto_df)) * 100

        c_par1, c_par2 = st.columns([1, 2])
        with c_par1:
            st.metric("Total Elementos en Catálogo", len(pareto_df))
            st.metric("Elementos que generan el 80% de ventas", f"{count_80} ({pct_catalog_80:.1f}%)")
            
            if pct_catalog_80 <= 25:
                st.warning(
                    f"**Alta Concentración (Regla 80/20 Confirmada):** Solo el **{pct_catalog_80:.1f}%** de tus productos genera el 80% de la facturación. "
                    f"Existe una fuerte dependencia en pocos artículos estrella. Asegura su cadena de suministro y abastecimiento.",
                    icon=":material/warning:"
                )
            else:
                st.info(
                    f"**Catálogo Diversificado:** El 80% de tus ventas está distribuido en el **{pct_catalog_80:.1f}%** de tus artículos. "
                    f"Menor riesgo de concentración unitaria.",
                    icon=":material/check_circle:"
                )

        with c_par2:
            # Gráfico de Pareto combinado (Barras + Línea Acumulada)
            fig_pareto = go.Figure()
            
            # Barras individuales
            fig_pareto.add_trace(
                go.Bar(
                    x=pareto_df[prod_col].head(15),
                    y=pareto_df[rev_col].head(15),
                    name='Ingresos ($)',
                    marker_color='#118DFF',
                    yaxis='y'
                )
            )
            # Línea acumulada
            fig_pareto.add_trace(
                go.Scatter(
                    x=pareto_df[prod_col].head(15),
                    y=pareto_df['cum_pct'].head(15),
                    name='% Acumulado',
                    marker_color='#E66C37',
                    line=dict(width=3),
                    yaxis='y2'
                )
            )
            # Línea de referencia 80%
            fig_pareto.add_hline(y=80, line_dash="dash", line_color="#D13438", yref="y2", annotation_text="Umbral 80%")

            fig_pareto.update_layout(
                title="Top 15 Elementos & Curva Acumulada de Pareto",
                template='plotly_white',
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                yaxis=dict(title="Ingresos ($)"),
                yaxis2=dict(title="% Acumulado", overlaying='y', side='right', range=[0, 105]),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                margin=dict(l=20, r=20, t=40, b=20)
            )
            st.plotly_chart(fig_pareto, use_container_width=True)
    else:
        st.info("Se requiere una columna de producto/categoría e ingresos para trazar la curva de Pareto.")
