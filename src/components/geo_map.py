import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def render_geo_analytics(df: pd.DataFrame, profiler_info: dict):
    if df is None or df.empty:
        st.info("No hay transacciones geográficas disponibles para los filtros seleccionados.", icon=":material/info:")
        return

    st.subheader(":material/public: Mapa Coroplético & Inteligencia Territorial")
    st.markdown("Analiza la penetración geográfica de tu negocio, identifica territorios de alto margen y descubre zonas desatendidas.")
    
    geo_cols = profiler_info.get('geo_cols', {})
    metrics = profiler_info.get('metrics', {})
    
    # Identificar columna geográfica óptima
    avail_geo_cols = []
    for k in ['country', 'country_code', 'region', 'city']:
        if geo_cols.get(k) and geo_cols[k] in df.columns:
            avail_geo_cols.append(geo_cols[k])
            
    # Otras columnas posibles si el profiler no las capturó
    for col in df.columns:
        if col not in avail_geo_cols and any(w in str(col).lower() for w in ['pais', 'país', 'country', 'region', 'región', 'zona', 'territorio', 'ciudad', 'estado']):
            avail_geo_cols.append(col)
            
    if not avail_geo_cols:
        st.warning("No se encontraron columnas geográficas reconocibles en el conjunto de datos activo. Para visualizar el mapa coroplético, asegúrate de que tu archivo incluya columnas como 'país', 'country', 'región' o 'código ISO'.")
        return

    # Controles de Configuración del Mapa
    col_ctrl1, col_ctrl2, col_ctrl3, col_ctrl4 = st.columns([2, 2, 2, 2])
    
    with col_ctrl1:
        default_geo_idx = 0
        # Prefer country or country_code
        for idx, col in enumerate(avail_geo_cols):
            if any(k in col.lower() for k in ['country', 'pais', 'país', 'iso']):
                default_geo_idx = idx
                break
        selected_geo_col = st.selectbox("Dimensión Geográfica", avail_geo_cols, index=default_geo_idx)

    # Identificar métricas numéricas disponibles
    numeric_options = {}
    if metrics.get('revenue') and metrics['revenue'] in df.columns:
        numeric_options['Ingresos Totales ($)'] = metrics['revenue']
    elif 'revenue' in df.columns:
        numeric_options['Ingresos Totales ($)'] = 'revenue'
        
    if metrics.get('profit') and metrics['profit'] in df.columns:
        numeric_options['Utilidad Neta ($)'] = metrics['profit']
    elif 'profit' in df.columns:
        numeric_options['Utilidad Neta ($)'] = 'profit'
        
    if metrics.get('quantity') and metrics['quantity'] in df.columns:
        numeric_options['Unidades Vendidas (#)'] = metrics['quantity']
    elif 'quantity' in df.columns:
        numeric_options['Unidades Vendidas (#)'] = 'quantity'
        
    # Añadir cualquier otra métrica numérica
    for num_col in profiler_info.get('numeric_cols', []):
        if num_col not in numeric_options.values() and num_col not in ['transaction_id', 'id', 'lat', 'lon']:
            numeric_options[num_col.replace('_', ' ').title()] = num_col

    with col_ctrl2:
        metric_label = st.selectbox("Métrica a Visualizar", list(numeric_options.keys()))
        selected_metric_col = numeric_options[metric_label]

    with col_ctrl3:
        map_scope = st.selectbox("Alcance Geográfico", [
            "Mundial (World)",
            "Latinoamérica (South America)",
            "Norteamérica (North America)",
            "Europa (Europe)",
            "Estados Unidos (USA)",
            "África (Africa)",
            "Asia (Asia)"
        ])
        scope_mapping = {
            "Mundial (World)": "world",
            "Latinoamérica (South America)": "south america",
            "Norteamérica (North America)": "north america",
            "Europa (Europe)": "europe",
            "Estados Unidos (USA)": "usa",
            "África (Africa)": "africa",
            "Asia (Asia)": "asia"
        }
        chosen_scope = scope_mapping[map_scope]

    with col_ctrl4:
        color_theme = st.selectbox("Paleta Cromática", [
            "Blues (Corporativo)",
            "Viridis (Alto Contraste)",
            "Tealrose (Divergente Suave)",
            "Plasma (Vibrante)",
            "Greens (Financiero)"
        ])
        palette_mapping = {
            "Blues (Corporativo)": "Blues",
            "Viridis (Alto Contraste)": "Viridis",
            "Tealrose (Divergente Suave)": "Tealrose",
            "Plasma (Vibrante)": "Plasma",
            "Greens (Financiero)": "Greens"
        }
        chosen_palette = palette_mapping[color_theme]

    # Preparación y Agregación de Datos Geográficos
    agg_dict = {selected_metric_col: 'sum'}
    
    rev_col = metrics.get('revenue') if (metrics.get('revenue') and metrics.get('revenue') in df.columns) else ('revenue' if 'revenue' in df.columns else None)
    prof_col = metrics.get('profit') if (metrics.get('profit') and metrics.get('profit') in df.columns) else ('profit' if 'profit' in df.columns else None)
    
    if rev_col and rev_col != selected_metric_col:
        agg_dict[rev_col] = 'sum'
    if prof_col and prof_col != selected_metric_col:
        agg_dict[prof_col] = 'sum'
        
    geo_summary = df.groupby(selected_geo_col).agg(agg_dict).reset_index()
    geo_summary['transactions_count'] = df.groupby(selected_geo_col).size().values
    
    # Calcular Margen % si disponemos de revenue y profit
    if rev_col and prof_col and rev_col in geo_summary.columns and prof_col in geo_summary.columns:
        geo_summary['margin_pct'] = (geo_summary[prof_col] / geo_summary[rev_col].replace(0, pd.NA)) * 100
        geo_summary['margin_pct'] = geo_summary['margin_pct'].fillna(0).round(1)
        
    # Calcular Ticket Promedio si disponemos de revenue
    if rev_col and rev_col in geo_summary.columns:
        geo_summary['avg_ticket'] = geo_summary[rev_col] / geo_summary['transactions_count'].replace(0, 1)

    # Cobertura y tarjetas de resumen
    total_val = geo_summary[selected_metric_col].sum()
    top_territory = geo_summary.loc[geo_summary[selected_metric_col].idxmax()]
    
    col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
    with col_kpi1:
        st.metric(
            label=f"Total {metric_label}",
            value=f"${total_val:,.2f}" if "($)" in metric_label else f"{total_val:,.0f}"
        )
    with col_kpi2:
        top_name = str(top_territory[selected_geo_col])
        st.metric(
            label=f"Territorio Líder: {top_name}",
            value=f"${top_territory[selected_metric_col]:,.2f}" if "($)" in metric_label else f"{top_territory[selected_metric_col]:,.0f}"
        )
    with col_kpi3:
        if 'margin_pct' in geo_summary.columns:
            top_margin_row = geo_summary.loc[geo_summary['margin_pct'].idxmax()]
            st.metric(
                label=f"Mayor Margen: {top_margin_row[selected_geo_col]}",
                value=f"{top_margin_row['margin_pct']:.1f}%"
            )
        else:
            st.metric("Territorios Activos", f"{len(geo_summary):,}")
    with col_kpi4:
        st.metric("Territorios Analizados", f"{len(geo_summary)}")

    st.markdown("<br>", unsafe_allow_html=True)
    
    # Determinar si la columna es ISO-3 o Nombre de País o Región
    is_iso = geo_summary[selected_geo_col].astype(str).str.len().isin([3]).mean() > 0.6
    
    country_spanish_to_iso = {
        'méxico': 'MEX', 'mexico': 'MEX',
        'colombia': 'COL',
        'españa': 'ESP', 'espana': 'ESP',
        'argentina': 'ARG',
        'chile': 'CHL',
        'perú': 'PER', 'peru': 'PER',
        'estados unidos': 'USA', 'eeuu': 'USA', 'usa': 'USA',
        'brasil': 'BRA', 'brazil': 'BRA'
    }
    locations_col = selected_geo_col
    location_mode = "ISO-3" if is_iso else "country names"

    if not is_iso:
        geo_summary['iso_mapped'] = geo_summary[selected_geo_col].astype(str).str.lower().str.strip().map(country_spanish_to_iso)
        if geo_summary['iso_mapped'].notna().mean() > 0.3:
            locations_col = 'iso_mapped'
            location_mode = "ISO-3"
    
    # Construcción de hover data
    hover_cols = {selected_geo_col: True, selected_metric_col: ':.2f'}
    if 'margin_pct' in geo_summary.columns:
        hover_cols['margin_pct'] = ':.1f%'
    if 'transactions_count' in geo_summary.columns:
        hover_cols['transactions_count'] = True

    tab_map1, tab_map2 = st.tabs([":material/map: Mapa Coroplético", ":material/pin_drop: Mapa de Burbujas Geográficas"])
    
    with tab_map1:
        try:
            fig_map = px.choropleth(
                geo_summary,
                locations=locations_col,
                locationmode=location_mode,
                color=selected_metric_col,
                scope=chosen_scope,
                hover_name=selected_geo_col,
                hover_data=hover_cols,
                color_continuous_scale=chosen_palette,
                labels={
                    selected_metric_col: metric_label,
                    selected_geo_col: 'Territorio',
                    'margin_pct': 'Margen (%)',
                    'transactions_count': 'Transacciones'
                }
            )
            fig_map.update_geos(
                showcountries=True,
                countrycolor="#CCCCCC",
                showcoastlines=True,
                coastlinecolor="#EEEEEE",
                showland=True,
                landcolor="#F9F9FB",
                showocean=True,
                oceancolor="#F0F4F8"
            )
            fig_map.update_layout(
                margin={"r": 0, "t": 20, "l": 0, "b": 0},
                paper_bgcolor='rgba(0,0,0,0)',
                coloraxis_colorbar=dict(
                    title=metric_label,
                    thicknessmode="pixels", thickness=15,
                    lenmode="pixels", len=260
                )
            )
            st.plotly_chart(fig_map, use_container_width=True)
        except Exception as e:
            st.info(f"No fue posible proyectar las formas poligonales con los nombres de la columna seleccionada ({e}). Alternando automáticamente al mapa de barras/burbujas territoriales.")
            fig_bar = px.bar(
                geo_summary.sort_values(selected_metric_col, ascending=False),
                x=selected_geo_col,
                y=selected_metric_col,
                color=selected_metric_col,
                color_continuous_scale=chosen_palette,
                labels={selected_metric_col: metric_label, selected_geo_col: 'Territorio'},
                template='plotly_white'
            )
            st.plotly_chart(fig_bar, use_container_width=True)

    with tab_map2:
        # Si hay lat y lon en el dataset original
        has_coords = 'lat' in df.columns and 'lon' in df.columns
        if has_coords:
            coord_summary = df.groupby([selected_geo_col, 'lat', 'lon']).agg(agg_dict).reset_index()
            coord_summary['bubble_size'] = coord_summary[selected_metric_col].clip(lower=0)
            fig_bubble = px.scatter_geo(
                coord_summary,
                lat='lat',
                lon='lon',
                size='bubble_size',
                color=selected_metric_col,
                color_continuous_scale=chosen_palette,
                scope=chosen_scope,
                hover_name=selected_geo_col,
                template='plotly_white',
                labels={selected_metric_col: metric_label, 'bubble_size': metric_label}
            )
            fig_bubble.update_geos(showcountries=True, countrycolor="#CCCCCC", showland=True, landcolor="#F9F9FB")
            fig_bubble.update_layout(margin={"r": 0, "t": 20, "l": 0, "b": 0}, paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_bubble, use_container_width=True)
        else:
            # Burbujas usando los nombres de países
            geo_summary['bubble_size'] = geo_summary[selected_metric_col].clip(lower=0)
            fig_bubble = px.scatter_geo(
                geo_summary,
                locations=locations_col,
                locationmode=location_mode,
                size='bubble_size',
                color=selected_metric_col,
                color_continuous_scale=chosen_palette,
                scope=chosen_scope,
                hover_name=selected_geo_col,
                template='plotly_white',
                labels={selected_metric_col: metric_label, 'bubble_size': metric_label}
            )
            fig_bubble.update_geos(showcountries=True, countrycolor="#CCCCCC", showland=True, landcolor="#F9F9FB")
            fig_bubble.update_layout(margin={"r": 0, "t": 20, "l": 0, "b": 0}, paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_bubble, use_container_width=True)

    # Ranking Territorial
    st.divider()
    st.subheader(":material/leaderboard: Ranking y Participación por Territorio")
    geo_ranking = geo_summary.sort_values(selected_metric_col, ascending=False).copy()
    geo_ranking['share_pct'] = (geo_ranking[selected_metric_col] / total_val * 100).round(2)
    
    col_rank_tbl, col_rank_chart = st.columns([3, 2])
    with col_rank_tbl:
        display_cols = [selected_geo_col, selected_metric_col, 'share_pct', 'transactions_count']
        if 'margin_pct' in geo_ranking.columns:
            display_cols.append('margin_pct')
            
        format_dict = {
            selected_metric_col: "${:,.2f}" if "($)" in metric_label else "{:,.0f}",
            'share_pct': "{:.2f}%",
            'transactions_count': "{:,}",
            'margin_pct': "{:.1f}%"
        }
        st.dataframe(
            geo_ranking[display_cols].rename(columns={
                selected_geo_col: 'Territorio',
                selected_metric_col: metric_label,
                'share_pct': 'Cuota de Mercado (%)',
                'transactions_count': 'N° Transacciones',
                'margin_pct': 'Margen Rentabilidad (%)'
            }).style.format({k: v for k, v in format_dict.items() if k in display_cols}),
            use_container_width=True,
            hide_index=True
        )

    with col_rank_chart:
        fig_donut = px.pie(
            geo_ranking.head(6),
            names=selected_geo_col,
            values=selected_metric_col,
            hole=0.45,
            color_discrete_sequence=['#118DFF', '#12239E', '#E66C37', '#00B7C3', '#6B2D5C', '#A0AEC0'],
            labels={selected_geo_col: 'Territorio', selected_metric_col: metric_label}
        )
        fig_donut.update_layout(
            title_text="Distribución Top Territorios",
            margin={"r": 20, "t": 40, "l": 20, "b": 20},
            paper_bgcolor='rgba(0,0,0,0)',
            showlegend=True
        )
        st.plotly_chart(fig_donut, use_container_width=True)
