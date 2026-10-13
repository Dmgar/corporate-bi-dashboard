import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

def render_scatter_analytics(df: pd.DataFrame, profiler_info: dict):
    st.subheader(":material/scatter_plot: Análisis de Dispersión & Cuadrantes Estratégicos")
    st.markdown("Evalúa la correlación entre métricas comerciales clave (ej. Descuentos vs Margen) y clasifica tu catálogo en cuadrantes de negocio.")

    metrics = profiler_info.get('metrics', {})
    dimensions = profiler_info.get('dimensions', {})
    numeric_cols = profiler_info.get('numeric_cols', [])
    categorical_cols = profiler_info.get('categorical_cols', [])

    if len(numeric_cols) < 2:
        st.warning("Se requieren al menos 2 columnas numéricas para trazar gráficos de dispersión.")
        return

    tab_scatter, tab_bcg = st.tabs([
        ":material/query_stats: Gráfico de Dispersión & Correlación",
        ":material/grid_view: Matriz Estratégica BCG (Margen vs Volumen)"
    ])

    # ==========================================
    # TAB 1: GRÁFICO DE DISPERSIÓN & CORRELACIÓN
    # ==========================================
    with tab_scatter:
        st.markdown("#### Correlación entre Variables Comerciales")
        col_s1, col_s2, col_s3, col_s4 = st.columns(4)

        # Opciones para Eje X
        default_x_idx = 0
        if metrics.get('discount') and metrics['discount'] in numeric_cols:
            default_x_idx = numeric_cols.index(metrics['discount'])
        elif metrics.get('cost') and metrics['cost'] in numeric_cols:
            default_x_idx = numeric_cols.index(metrics['cost'])
            
        with col_s1:
            x_col = st.selectbox(
                "Variable que ajustas (ej. Descuento, Costo)",
                numeric_cols,
                index=default_x_idx,
                key="sc_x",
                help="Elige la variable comercial que deseas evaluar como causa (ejemplo: si aumentas descuentos o costos)."
            )

        # Opciones para Eje Y
        default_y_idx = 1 if len(numeric_cols) > 1 else 0
        if metrics.get('profit') and metrics['profit'] in numeric_cols and metrics['profit'] != x_col:
            default_y_idx = numeric_cols.index(metrics['profit'])
        elif metrics.get('revenue') and metrics['revenue'] in numeric_cols and metrics['revenue'] != x_col:
            default_y_idx = numeric_cols.index(metrics['revenue'])
            
        with col_s2:
            y_col = st.selectbox(
                "Resultado que quieres medir (ej. Ganancia, Ventas)",
                numeric_cols,
                index=default_y_idx,
                key="sc_y",
                help="Elige el resultado del negocio que deseas observar (ejemplo: tu ganancia o facturación)."
            )

        # Color / Categoría
        all_dims = [c for c in categorical_cols if c not in ['date', 'fecha']]
        default_color_idx = 0
        if dimensions.get('category') and dimensions['category'] in all_dims:
            default_color_idx = all_dims.index(dimensions['category'])
            
        with col_s3:
            color_col = st.selectbox(
                "Separar por grupo comercial",
                ["(Todos juntos)"] + all_dims,
                index=(default_color_idx + 1) if all_dims else 0,
                key="sc_color",
                help="Permite ver los puntos agrupados por categoría, canal o región."
            )

        # Agrupación por mapeo explícito
        prod_dim = dimensions.get('product') or dimensions.get('category')
        group_map = {"(Transacciones individuales)": None}
        if prod_dim and prod_dim in df.columns:
            group_map[f"Ver por {prod_dim.title()}"] = prod_dim
        if dimensions.get('category') and dimensions['category'] in df.columns and dimensions['category'] != prod_dim:
            group_map[f"Ver por {dimensions['category'].title()}"] = dimensions['category']

        group_options = list(group_map.keys())

        with col_s4:
            group_choice = st.selectbox(
                "Nivel de detalle",
                group_options,
                index=1 if len(group_options) > 1 else 0,
                key="sc_group",
                help="Puedes ver cada venta individual o resumir el desempeño por producto."
            )

        # Procesar DataFrame para dispersión
        plot_df = df.copy()
        hover_name_col = None
        selected_group_col = group_map.get(group_choice)

        if selected_group_col is not None and selected_group_col in df.columns:
            hover_name_col = selected_group_col
            group_by_cols = [selected_group_col]
            if color_col != "(Todos juntos)" and color_col != selected_group_col and color_col in df.columns:
                group_by_cols.append(color_col)
                
            # Asignar sum para métricas aditivas y mean para precios/tasas
            additive_keys = ['revenue', 'profit', 'cost', 'quantity', 'ingreso', 'venta', 'utilidad', 'ganancia', 'costo', 'unidades', 'items', 'volumen']
            rate_keys = ['discount', 'descuento', 'margin', 'margen', 'price', 'precio', 'rate', 'tasa', 'pct']

            def get_agg_op(col_name):
                c_lower = str(col_name).lower()
                if any(k in c_lower for k in rate_keys):
                    return 'mean'
                if any(k in c_lower for k in additive_keys):
                    return 'sum'
                return 'mean'

            agg_ops = {
                x_col: get_agg_op(x_col),
                y_col: get_agg_op(y_col)
            }
            if metrics.get('revenue') and metrics['revenue'] in df.columns and metrics['revenue'] not in agg_ops:
                agg_ops[metrics['revenue']] = 'sum'
            if metrics.get('quantity') and metrics['quantity'] in df.columns and metrics['quantity'] not in agg_ops:
                agg_ops[metrics['quantity']] = 'sum'
            if metrics.get('profit') and metrics['profit'] in df.columns and metrics['profit'] not in agg_ops:
                agg_ops[metrics['profit']] = 'sum'
                
            plot_df = plot_df.groupby(group_by_cols).agg(agg_ops).reset_index()

        # Filtrar valores NaN o infinitos
        clean_mask = plot_df[x_col].notna() & plot_df[y_col].notna() & np.isfinite(plot_df[x_col]) & np.isfinite(plot_df[y_col])
        plot_df = plot_df[clean_mask]

        if plot_df.empty or len(plot_df) < 2:
            st.warning("No hay suficientes datos válidos para calcular la correlación de dispersión.")
            return

        # Calcular Estadísticas de Correlación
        x_vals = plot_df[x_col].values.astype(float)
        y_vals = plot_df[y_col].values.astype(float)

        corr_matrix = np.corrcoef(x_vals, y_vals)
        r_val = corr_matrix[0, 1] if not np.isnan(corr_matrix[0, 1]) else 0.0
        r_squared = r_val ** 2

        # Regresión Lineal: y = mx + b
        try:
            poly = np.polyfit(x_vals, y_vals, 1)
            slope = poly[0]
            intercept = poly[1]
            x_line = np.linspace(x_vals.min(), x_vals.max(), 100)
            y_line = slope * x_line + intercept
            has_trendline = True
        except Exception:
            has_trendline = False

        # Visual KPI Cards de Correlación
        kpi_c1, kpi_c2, kpi_c3, kpi_c4 = st.columns(4)
        with kpi_c1:
            st.metric("Relación Comercial (r)", f"{r_val:.2f}", help="Si es positivo, ambas variables suben juntas; si es negativo, al subir una la otra baja.")
        with kpi_c2:
            st.metric("Grado de Influencia (R²)", f"{r_squared * 100:.0f}%", help="Mide qué porcentaje del resultado final se debe a esta variable.")
        with kpi_c3:
            tipo_rel = "Directa (Crecen juntas)" if r_val > 0.05 else ("Inversa (Al subir una, la otra cae)" if r_val < -0.05 else "Sin relación clara")
            st.metric("Comportamiento", tipo_rel)
        with kpi_c4:
            fuerza = "Fuerte" if abs(r_val) >= 0.7 else ("Moderada" if abs(r_val) >= 0.3 else "Baja o Dispersa")
            st.metric("Fuerza del Vínculo", fuerza)

        # Interpretación Ejecutiva de Negocio (En lenguaje directo de ventas y rentabilidad)
        var_x_name = x_col.replace('_', ' ').title()
        var_y_name = y_col.replace('_', ' ').title()
        
        if r_val <= -0.3:
            st.warning(
                f"**Recomendación de Negocio:** Detectamos una relación inversa {fuerza.lower()} ({r_val:.2f}) entre **{var_x_name}** y **{var_y_name}**. "
                f"Cada vez que aumenta {var_x_name}, tu {var_y_name} tiende a disminuir. "
                f"Si estás ofreciendo descuentos agresivos, verifica si estás regalando margen sin ganar suficiente volumen.",
                icon=":material/trending_down:"
            )
        elif r_val >= 0.3:
            st.success(
                f"**Recomendación de Negocio:** Hay una relación positiva {fuerza.lower()} ({r_val:.2f}) entre **{var_x_name}** y **{var_y_name}**. "
                f"A medida que sube {var_x_name}, tus resultados en {var_y_name} crecen de forma consistente.",
                icon=":material/trending_up:"
            )
        else:
            st.info(
                f"**Recomendación de Negocio:** El impacto de **{var_x_name}** sobre **{var_y_name}** es bajo o independiente ({r_val:.2f}). "
                f"Otros factores (como la demanda estacional, el tipo de cliente o la calidad del producto) tienen más peso en este resultado.",
                icon=":material/info:"
            )

        # Gráfico Plotly
        fig_scatter = px.scatter(
            plot_df,
            x=x_col,
            y=y_col,
            color=color_col if color_col != "(Todos juntos)" else None,
            hover_name=hover_name_col,
            template='plotly_white',
            labels={x_col: x_col.replace('_', ' ').title(), y_col: y_col.replace('_', ' ').title()},
            color_discrete_sequence=['#118DFF', '#E66C37', '#12239E', '#00B7C3', '#6B2D5C', '#28A745'],
            opacity=0.75
        )

        if has_trendline:
            fig_scatter.add_trace(
                go.Scatter(
                    x=x_line,
                    y=y_line,
                    mode='lines',
                    name=f'Línea de Tendencia (R²={r_squared:.2f})',
                    line=dict(color='#DC3545', width=2, dash='dash')
                )
            )

        fig_scatter.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=20, r=20, t=30, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

    # ==========================================
    # TAB 2: MATRIZ ESTRATÉGICA BCG
    # ==========================================
    with tab_bcg:
        st.markdown("#### Matriz BCG: Rentabilidad vs Volumen de Ventas")
        st.markdown("Identifica productos estrella, oportunidades de crecimiento y candidatos a optimización o descatalogación.")

        bcg_entity = dimensions.get('product') or dimensions.get('category') or (categorical_cols[0] if categorical_cols else None)
        if not bcg_entity:
            st.warning("Se requiere una columna de producto o categoría para la Matriz BCG.")
            return

        bcg_rev = metrics.get('revenue') or ('revenue' if 'revenue' in df.columns else None)
        bcg_prof = metrics.get('profit') or ('profit' if 'profit' in df.columns else None)
        bcg_cat = dimensions.get('category') if (dimensions.get('category') and dimensions.get('category') != bcg_entity) else None

        if not bcg_rev or not bcg_prof:
            st.warning("La Matriz BCG requiere columnas de Ingresos ('revenue') y Utilidad ('profit').")
            return

        # Agrupar a nivel de entidad
        bcg_group_cols = [bcg_entity]
        if bcg_cat and bcg_cat in df.columns:
            bcg_group_cols.append(bcg_cat)
            
        bcg_df = df.groupby(bcg_group_cols).agg({
            bcg_rev: 'sum',
            bcg_prof: 'sum'
        }).reset_index()

        bcg_df['margin_pct'] = (bcg_df[bcg_prof] / bcg_df[bcg_rev].replace(0, pd.NA)) * 100
        bcg_df['margin_pct'] = bcg_df['margin_pct'].fillna(0).round(1)

        # Umbrales de corte (Medianas)
        threshold_vol = bcg_df[bcg_rev].median()
        threshold_margin = bcg_df['margin_pct'].median()

        # Clasificación en 4 cuadrantes
        def classify_bcg(row):
            high_vol = row[bcg_rev] >= threshold_vol
            high_margin = row['margin_pct'] >= threshold_margin
            if high_vol and high_margin:
                return "Estrella (Alto Vol, Alto Margen)"
            elif not high_vol and high_margin:
                return "Oportunidad (Bajo Vol, Alto Margen)"
            elif high_vol and not high_margin:
                return "Vaca Lechera (Alto Vol, Bajo Margen)"
            else:
                return "En Riesgo (Bajo Vol, Bajo Margen)"

        bcg_df['cuadrante'] = bcg_df.apply(classify_bcg, axis=1)

        # Métricas de Cuadrantes
        counts = bcg_df['cuadrante'].value_counts()
        c_q1, c_q2, c_q3, c_q4 = st.columns(4)
        with c_q1:
            st.metric(":material/star: Productos Estrella", counts.get("Estrella (Alto Vol, Alto Margen)", 0))
        with c_q2:
            st.metric(":material/rocket_launch: Oportunidades", counts.get("Oportunidad (Bajo Vol, Alto Margen)", 0))
        with c_q3:
            st.metric(":material/savings: Vacas Lecheras", counts.get("Vaca Lechera (Alto Vol, Bajo Margen)", 0))
        with c_q4:
            st.metric(":material/warning: En Riesgo", counts.get("En Riesgo (Bajo Vol, Bajo Margen)", 0))

        # Gráfico Plotly BCG
        palette_bcg = {
            "Estrella (Alto Vol, Alto Margen)": "#107C41",     # Verde esmeralda
            "Oportunidad (Bajo Vol, Alto Margen)": "#0078D4",  # Azul corporativo
            "Vaca Lechera (Alto Vol, Bajo Margen)": "#F7630C", # Naranja cálido
            "En Riesgo (Bajo Vol, Bajo Margen)": "#D13438"     # Rojo alerta
        }

        fig_bcg = px.scatter(
            bcg_df,
            x=bcg_rev,
            y='margin_pct',
            color='cuadrante',
            hover_name=bcg_entity,
            hover_data={
                bcg_rev: ':$,.2f',
                bcg_prof: ':$,.2f',
                'margin_pct': ':.1f%'
            },
            color_discrete_map=palette_bcg,
            labels={
                bcg_rev: 'Volumen de Ingresos ($)',
                'margin_pct': 'Margen de Rentabilidad (%)',
                'cuadrante': 'Cuadrante BCG'
            },
            template='plotly_white'
        )

        # Líneas de división de cuadrantes
        fig_bcg.add_vline(x=threshold_vol, line_width=1.5, line_dash="dash", line_color="#888888")
        fig_bcg.add_hline(y=threshold_margin, line_width=1.5, line_dash="dash", line_color="#888888")

        # Anotaciones en los 4 cuadrantes calculadas mediante puntos medios seguros
        min_x = float(bcg_df[bcg_rev].min())
        max_x = float(bcg_df[bcg_rev].max())
        min_y = float(bcg_df['margin_pct'].min())
        max_y = float(bcg_df['margin_pct'].max())

        mid_x_low = min_x + (threshold_vol - min_x) * 0.5
        mid_x_high = threshold_vol + (max_x - threshold_vol) * 0.5

        mid_y_high = threshold_margin + (max_y - threshold_margin) * 0.75
        mid_y_low = min_y + (threshold_margin - min_y) * 0.35

        fig_bcg.add_annotation(x=mid_x_high, y=mid_y_high, text="<b>ESTRELLAS</b>", showarrow=False, font=dict(color="#107C41", size=13))
        fig_bcg.add_annotation(x=mid_x_low, y=mid_y_high, text="<b>OPORTUNIDADES</b>", showarrow=False, font=dict(color="#0078D4", size=13))
        fig_bcg.add_annotation(x=mid_x_high, y=mid_y_low, text="<b>VACAS LECHERAS</b>", showarrow=False, font=dict(color="#F7630C", size=13))
        fig_bcg.add_annotation(x=mid_x_low, y=mid_y_low, text="<b>EN RIESGO</b>", showarrow=False, font=dict(color="#D13438", size=13))

        fig_bcg.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=20, r=20, t=30, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_bcg, use_container_width=True)

        # Detalle de Acciones Tácticas por Cuadrante
        st.markdown("##### Detalle de Productos por Cuadrante")
        selected_quad = st.radio(
            "Filtrar Cuadrante:",
            ["Todos", "Estrella (Alto Vol, Alto Margen)", "Oportunidad (Bajo Vol, Alto Margen)", "Vaca Lechera (Alto Vol, Bajo Margen)", "En Riesgo (Bajo Vol, Bajo Margen)"],
            horizontal=True
        )

        display_bcg = bcg_df if selected_quad == "Todos" else bcg_df[bcg_df['cuadrante'] == selected_quad]
        st.dataframe(
            display_bcg[[bcg_entity, bcg_rev, bcg_prof, 'margin_pct', 'cuadrante']].sort_values(bcg_rev, ascending=False).rename(columns={
                bcg_entity: 'Producto / Elemento',
                bcg_rev: 'Total Ingresos ($)',
                bcg_prof: 'Utilidad Neta ($)',
                'margin_pct': 'Margen (%)',
                'cuadrante': 'Clasificación Estratégica'
            }).style.format({
                'Total Ingresos ($)': '${:,.2f}',
                'Utilidad Neta ($)': '${:,.2f}',
                'Margen (%)': '{:.1f}%'
            }),
            use_container_width=True,
            hide_index=True
        )
