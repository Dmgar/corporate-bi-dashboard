import streamlit as st
import pandas as pd
from datetime import timedelta

def render_floating_filters(df: pd.DataFrame, profiler_info: dict) -> pd.DataFrame:
    """
    Renderiza una barra flotante de filtros rápidos en la parte superior del dashboard
    y retorna el DataFrame filtrado.
    """
    date_cols = profiler_info.get('date_cols', [])
    dimensions = profiler_info.get('dimensions', {})
    geo_cols = profiler_info.get('geo_cols', {})
    
    # CSS para la barra flotante superior estilo Glassmorphism
    st.markdown("""
    <style>
    .floating-filter-bar {
        background: rgba(255, 255, 255, 0.92);
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        border: 1px solid #E1DFDD;
        border-radius: 8px;
        padding: 10px 16px;
        margin-bottom: 16px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .filter-badge {
        display: inline-block;
        background-color: #F0F4F8;
        color: #12239E;
        padding: 3px 8px;
        border-radius: 12px;
        font-size: 0.82rem;
        font-weight: 500;
        margin-right: 6px;
        border: 1px solid #D0DCE8;
    }
    </style>
    """, unsafe_allow_html=True)

    date_col = date_cols[0] if (date_cols and date_cols[0] in df.columns) else None
    
    # Inicializar estado de sesión para filtros rápidos
    if 'quick_date_filter' not in st.session_state:
        st.session_state.quick_date_filter = 'Todo'
        
    filtered_df = df.copy()
    
    # Detectar dimensiones clave
    cat_col = dimensions.get('category') or ('category' if 'category' in df.columns else None)
    geo_col = geo_cols.get('country') or geo_cols.get('region') or ('country' if 'country' in df.columns else ('region' if 'region' in df.columns else None))
    chan_col = dimensions.get('channel') or ('channel' if 'channel' in df.columns else None)
    seg_col = dimensions.get('segment') or ('segment' if 'segment' in df.columns else None)

    # Barra Flotante de Controles
    col_bar_left, col_bar_popover, col_bar_reset = st.columns([5, 2, 1])

    with col_bar_left:
        # Píldoras de Rango de Fecha Rápido si hay columna de fecha
        if date_col and pd.api.types.is_datetime64_any_dtype(df[date_col]):
            max_dt = df[date_col].max()
            min_dt = df[date_col].min()
            
            pills_options = ["Todo", "Último Año", "Último Trimestre", "Últimos 30 días"]
            selected_pill = st.pills(
                "Rango Temporal Rápido",
                options=pills_options,
                default=st.session_state.quick_date_filter,
                key="pill_date_selector",
                label_visibility="collapsed"
            )
            st.session_state.quick_date_filter = selected_pill or "Todo"

            if st.session_state.quick_date_filter == "Últimos 30 días" and pd.notna(max_dt):
                cutoff = max_dt - timedelta(days=30)
                filtered_df = filtered_df[filtered_df[date_col] >= cutoff]
            elif st.session_state.quick_date_filter == "Último Trimestre" and pd.notna(max_dt):
                cutoff = max_dt - timedelta(days=90)
                filtered_df = filtered_df[filtered_df[date_col] >= cutoff]
            elif st.session_state.quick_date_filter == "Último Año" and pd.notna(max_dt):
                cutoff = max_dt - timedelta(days=365)
                filtered_df = filtered_df[filtered_df[date_col] >= cutoff]

    with col_bar_popover:
        # Popover flotante para filtros detallados
        with st.popover(":material/tune: Filtros Flotantes", use_container_width=True):
            st.markdown("##### :material/filter_alt: Filtros Rápidos de Negocio")
            
            def sync_multiselect_state(key: str, unique_vals: list):
                current = st.session_state.get(key)
                if current is None or not isinstance(current, list):
                    st.session_state[key] = list(unique_vals)
                else:
                    valid_vals = [v for v in current if v in unique_vals]
                    st.session_state[key] = valid_vals if valid_vals else list(unique_vals)

            # Filtro por Categorías
            selected_cats = None
            if cat_col and cat_col in df.columns:
                unique_cats = sorted(df[cat_col].dropna().unique().tolist())
                sync_multiselect_state('floating_sel_cats', unique_cats)
                selected_cats = st.multiselect(
                    f"Categorías ({cat_col.title()})",
                    options=unique_cats,
                    key="floating_sel_cats"
                )
                if selected_cats:
                    filtered_df = filtered_df[filtered_df[cat_col].isin(selected_cats)]

            # Filtro por Territorio
            selected_geos = None
            if geo_col and geo_col in df.columns:
                unique_geos = sorted(df[geo_col].dropna().unique().tolist())
                sync_multiselect_state('floating_sel_geos', unique_geos)
                selected_geos = st.multiselect(
                    f"Territorios ({geo_col.title()})",
                    options=unique_geos,
                    key="floating_sel_geos"
                )
                if selected_geos:
                    filtered_df = filtered_df[filtered_df[geo_col].isin(selected_geos)]

            # Filtro por Canal
            selected_chans = None
            if chan_col and chan_col in df.columns:
                unique_chans = sorted(df[chan_col].dropna().unique().tolist())
                sync_multiselect_state('floating_sel_chans', unique_chans)
                selected_chans = st.multiselect(
                    f"Canales ({chan_col.title()})",
                    options=unique_chans,
                    key="floating_sel_chans"
                )
                if selected_chans:
                    filtered_df = filtered_df[filtered_df[chan_col].isin(selected_chans)]

            # Filtro por Segmento
            selected_segs = None
            if seg_col and seg_col in df.columns:
                unique_segs = sorted(df[seg_col].dropna().unique().tolist())
                sync_multiselect_state('floating_sel_segs', unique_segs)
                selected_segs = st.multiselect(
                    f"Segmento de Cliente ({seg_col.title()})",
                    options=unique_segs,
                    key="floating_sel_segs"
                )
                if selected_segs:
                    filtered_df = filtered_df[filtered_df[seg_col].isin(selected_segs)]

    with col_bar_reset:
        if st.button(":material/refresh: Limpiar", use_container_width=True, help="Restablece todos los filtros aplicados"):
            st.session_state.quick_date_filter = "Todo"
            if 'floating_sel_cats' in st.session_state: del st.session_state['floating_sel_cats']
            if 'floating_sel_geos' in st.session_state: del st.session_state['floating_sel_geos']
            if 'floating_sel_chans' in st.session_state: del st.session_state['floating_sel_chans']
            if 'floating_sel_segs' in st.session_state: del st.session_state['floating_sel_segs']
            st.rerun()

    # Resumen de registros visibles
    total_recs = len(df)
    visible_recs = len(filtered_df)
    if visible_recs < total_recs:
        st.caption(f":material/filter_alt_check: Mostrando **{visible_recs:,}** de **{total_recs:,}** transacciones ({visible_recs/total_recs*100:.1f}%) según los filtros activos.")

    return filtered_df
