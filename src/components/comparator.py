import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

def render_comparator_analytics(df: pd.DataFrame, profiler_info: dict):
    st.subheader(":material/balance: Comparadores Multidimensionales & Benchmarking")
    st.markdown("Compara períodos históricos para medir crecimiento o enfrenta dos productos, canales o regiones para identificar ventajas competitivas.")

    date_cols = profiler_info.get('date_cols', [])
    metrics = profiler_info.get('metrics', {})
    dimensions = profiler_info.get('dimensions', {})
    categorical_cols = profiler_info.get('categorical_cols', [])

    tab_period, tab_entity = st.tabs([
        ":material/calendar_month: Comparador de Períodos Temporales (A vs B)",
        ":material/compare_arrows: Comparador de Entidades / Benchmarking"
    ])

    # ===============================================
    # TAB 1: COMPARADOR DE PERÍODOS TEMPORALES (A vs B)
    # ===============================================
    with tab_period:
        if not date_cols or date_cols[0] not in df.columns:
            st.info("No se detectó una columna de fechas para habilitar el comparador temporal de períodos.")
        else:
            date_col = date_cols[0]
            temp_df = df.copy()
            temp_df['period_month'] = pd.to_datetime(temp_df[date_col]).dt.strftime('%Y-%m')
            available_months = sorted(temp_df['period_month'].dropna().unique().tolist(), reverse=True)

            if len(available_months) < 2:
                st.warning("Se requieren al menos 2 meses o períodos diferentes para realizar la comparación.")
            else:
                col_sel1, col_sel2 = st.columns(2)
                with col_sel1:
                    p1 = st.selectbox("Período Base (A - Más reciente)", available_months, index=0, key="cmp_p1")
                with col_sel2:
                    p2 = st.selectbox("Período de Comparación (B - Anterior)", available_months, index=1 if len(available_months) > 1 else 0, key="cmp_p2")

                df_p1 = temp_df[temp_df['period_month'] == p1]
                df_p2 = temp_df[temp_df['period_month'] == p2]

                rev_col = metrics.get('revenue') or ('revenue' if 'revenue' in df.columns else None)
                prof_col = metrics.get('profit') or ('profit' if 'profit' in df.columns else None)
                cost_col = metrics.get('cost') or ('cost' if 'cost' in df.columns else None)

                # Calcular Métricas P1
                rev_p1 = df_p1[rev_col].sum() if rev_col else 0
                prof_p1 = df_p1[prof_col].sum() if prof_col else 0
                cost_p1 = df_p1[cost_col].sum() if cost_col else 0
                tx_p1 = len(df_p1)
                margin_p1 = (prof_p1 / rev_p1 * 100) if rev_p1 > 0 else 0
                ticket_p1 = (rev_p1 / tx_p1) if tx_p1 > 0 else 0

                # Calcular Métricas P2
                rev_p2 = df_p2[rev_col].sum() if rev_col else 0
                prof_p2 = df_p2[prof_col].sum() if prof_col else 0
                cost_p2 = df_p2[cost_col].sum() if cost_col else 0
                tx_p2 = len(df_p2)
                margin_p2 = (prof_p2 / rev_p2 * 100) if rev_p2 > 0 else 0
                ticket_p2 = (rev_p2 / tx_p2) if tx_p2 > 0 else 0

                # Calcular Deltas
                def calc_delta(v1, v2):
                    diff = v1 - v2
                    pct = ((diff / v2) * 100) if v2 != 0 else 0
                    return diff, pct

                d_rev, d_rev_pct = calc_delta(rev_p1, rev_p2)
                d_prof, d_prof_pct = calc_delta(prof_p1, prof_p2)
                d_cost, d_cost_pct = calc_delta(cost_p1, cost_p2)
                d_tx, d_tx_pct = calc_delta(tx_p1, tx_p2)
                d_margin = margin_p1 - margin_p2
                d_ticket, d_ticket_pct = calc_delta(ticket_p1, ticket_p2)

                st.markdown(f"##### Resumen de Variación: {p1} vs {p2}")

                # Tarjetas de KPI Comparativo
                kc1, kc2, kc3, kc4 = st.columns(4)
                with kc1:
                    st.metric(
                        "Ingresos Brutos",
                        f"${rev_p1:,.2f}",
                        delta=f"{d_rev_pct:+.1f}% (${d_rev:+,.2f})",
                        delta_color="normal"
                    )
                with kc2:
                    st.metric(
                        "Utilidad Neta",
                        f"${prof_p1:,.2f}",
                        delta=f"{d_prof_pct:+.1f}% (${d_prof:+,.2f})",
                        delta_color="normal"
                    )
                with kc3:
                    st.metric(
                        "Margen de Ganancia",
                        f"{margin_p1:.1f}%",
                        delta=f"{d_margin:+.1f} pp",
                        delta_color="normal"
                    )
                with kc4:
                    st.metric(
                        "Ticket Promedio",
                        f"${ticket_p1:,.2f}",
                        delta=f"{d_ticket_pct:+.1f}%",
                        delta_color="normal"
                    )

                st.markdown("<br>", unsafe_allow_html=True)

                # Desglose comparativo por Categoría
                cat_col = dimensions.get('category') or dimensions.get('channel') or (categorical_cols[0] if categorical_cols else None)
                if cat_col and rev_col:
                    p1_by_cat = df_p1.groupby(cat_col)[rev_col].sum().reset_index().rename(columns={rev_col: f'Ingresos {p1}'})
                    p2_by_cat = df_p2.groupby(cat_col)[rev_col].sum().reset_index().rename(columns={rev_col: f'Ingresos {p2}'})
                    
                    merged_cat = pd.merge(p1_by_cat, p2_by_cat, on=cat_col, how='outer').fillna(0)
                    merged_cat['Variación ($)'] = merged_cat[f'Ingresos {p1}'] - merged_cat[f'Ingresos {p2}']
                    merged_cat['Crecimiento (%)'] = (merged_cat['Variación ($)'] / merged_cat[f'Ingresos {p2}'].replace(0, pd.NA) * 100).fillna(0).round(1)

                    col_chart_comp1, col_chart_comp2 = st.columns(2)
                    with col_chart_comp1:
                        st.markdown(f"**Comparación de Ingresos por {cat_col.title()}**")
                        # Transformar a formato largo para plotly
                        melted_cat = merged_cat.melt(
                            id_vars=[cat_col],
                            value_vars=[f'Ingresos {p1}', f'Ingresos {p2}'],
                            var_name='Período',
                            value_name='Ingresos ($)'
                        )
                        fig_bars = px.bar(
                            melted_cat,
                            x=cat_col,
                            y='Ingresos ($)',
                            color='Período',
                            barmode='group',
                            template='plotly_white',
                            color_discrete_sequence=['#118DFF', '#A0AEC0']
                        )
                        fig_bars.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                        st.plotly_chart(fig_bars, use_container_width=True)

                    with col_chart_comp2:
                        st.markdown(f"**Variación Neta ($) por {cat_col.title()}**")
                        merged_sorted = merged_cat.sort_values('Variación ($)', ascending=True)
                        fig_diff = px.bar(
                            merged_sorted,
                            x='Variación ($)',
                            y=cat_col,
                            orientation='h',
                            color='Variación ($)',
                            color_continuous_scale=['#D13438', '#CCCCCC', '#107C41'],
                            template='plotly_white'
                        )
                        fig_diff.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                        st.plotly_chart(fig_diff, use_container_width=True)

    # ===============================================
    # TAB 2: COMPARADOR DE ENTIDADES / BENCHMARKING
    # ===============================================
    with tab_entity:
        st.markdown("#### Benchmarking Cara a Cara: Entidad A vs Entidad B")
        
        # Selección de la dimensión a comparar
        dim_candidates = []
        for k in ['category', 'product', 'channel', 'segment']:
            if dimensions.get(k) and dimensions[k] in df.columns:
                dim_candidates.append(dimensions[k])
        for c in categorical_cols:
            if c not in dim_candidates and c not in ['date', 'fecha']:
                dim_candidates.append(c)

        if not dim_candidates:
            st.warning("No se encontraron dimensiones categóricas para realizar comparaciones de entidades.")
            return

        col_ent_dim, col_ent_a, col_ent_b = st.columns([2, 3, 3])
        with col_ent_dim:
            selected_dim = st.selectbox("Dimensión a Comparar", dim_candidates, key="cmp_dim_ent")

        unique_entities = sorted(df[selected_dim].dropna().unique().tolist())
        if len(unique_entities) < 2:
            st.warning("La dimensión seleccionada contiene menos de 2 elementos para comparar.")
            return

        with col_ent_a:
            ent_a = st.selectbox("Elemento A", unique_entities, index=0, key="cmp_ent_a")
        with col_ent_b:
            ent_b = st.selectbox("Elemento B", unique_entities, index=1 if len(unique_entities) > 1 else 0, key="cmp_ent_b")

        df_a = df[df[selected_dim] == ent_a]
        df_b = df[df[selected_dim] == ent_b]

        rev_col = metrics.get('revenue') or ('revenue' if 'revenue' in df.columns else None)
        prof_col = metrics.get('profit') or ('profit' if 'profit' in df.columns else None)
        cost_col = metrics.get('cost') or ('cost' if 'cost' in df.columns else None)
        qty_col = metrics.get('quantity') or ('quantity' if 'quantity' in df.columns else None)
        disc_col = metrics.get('discount') or ('discount' if 'discount' in df.columns else None)

        def get_stats(sub_df):
            r = sub_df[rev_col].sum() if rev_col else 0
            p = sub_df[prof_col].sum() if prof_col else 0
            c = sub_df[cost_col].sum() if cost_col else 0
            q = sub_df[qty_col].sum() if qty_col else 0
            d = (sub_df[disc_col].mean() * 100) if disc_col else 0
            tx = len(sub_df)
            m = (p / r * 100) if r > 0 else 0
            t = (r / tx) if tx > 0 else 0
            return {
                'Ingresos ($)': r,
                'Utilidad ($)': p,
                'Costo ($)': c,
                'Margen (%)': m,
                'Unidades': q,
                'Descuento Promedio (%)': d,
                'Transacciones': tx,
                'Ticket Promedio ($)': t
            }

        stats_a = get_stats(df_a)
        stats_b = get_stats(df_b)

        # Construir Scorecard de Comparación
        scorecard_rows = []
        for m_name in stats_a.keys():
            va = stats_a[m_name]
            vb = stats_b[m_name]
            diff = va - vb
            pct = ((diff / vb) * 100) if vb != 0 else 0
            
            # Ganador
            if "Costo" in m_name or "Descuento" in m_name:
                winner = ent_a if va < vb else (ent_b if vb < va else "Empate")
            else:
                winner = ent_a if va > vb else (ent_b if vb > va else "Empate")

            scorecard_rows.append({
                'Métrica': m_name,
                f'{ent_a}': f"${va:,.2f}" if "($)" in m_name else (f"{va:.1f}%" if "(%)" in m_name else f"{va:,.0f}"),
                f'{ent_b}': f"${vb:,.2f}" if "($)" in m_name else (f"{vb:.1f}%" if "(%)" in m_name else f"{vb:,.0f}"),
                'Diferencia (A - B)': f"{diff:+,.2f}" if "($)" in m_name else (f"{diff:+.1f} pp" if "(%)" in m_name else f"{diff:+,.0f}"),
                'Var %': f"{pct:+.1f}%",
                'Líder': winner
            })

        score_df = pd.DataFrame(scorecard_rows)

        col_sc_tbl, col_sc_chart = st.columns([3, 2])
        with col_sc_tbl:
            st.markdown(f"**Scorecard Comparativo: {ent_a} vs {ent_b}**")
            st.dataframe(score_df, use_container_width=True, hide_index=True)

        with col_sc_chart:
            st.markdown("**Comparativa Visual Normalizada (Base 100)**")
            # Normalizar métricas clave para gráfico de radar o barras paralelas
            key_m = ['Ingresos ($)', 'Utilidad ($)', 'Margen (%)', 'Transacciones', 'Ticket Promedio ($)']
            norm_data = []
            for m in key_m:
                va = stats_a[m]
                vb = stats_b[m]
                max_v = max(va, vb) if max(va, vb) > 0 else 1
                norm_data.append({'Métrica': m.split(' ')[0], 'Elemento': ent_a, 'Puntaje': (va / max_v) * 100})
                norm_data.append({'Métrica': m.split(' ')[0], 'Elemento': ent_b, 'Puntaje': (vb / max_v) * 100})

            fig_norm = px.bar(
                pd.DataFrame(norm_data),
                x='Métrica',
                y='Puntaje',
                color='Elemento',
                barmode='group',
                template='plotly_white',
                color_discrete_sequence=['#118DFF', '#E66C37']
            )
            fig_norm.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_norm, use_container_width=True)

        # Veredicto Ejecutivo Inteligente
        st.divider()
        st.markdown("##### :material/lightbulb: Veredicto Ejecutivo Automatizado")
        rev_winner = ent_a if stats_a['Ingresos ($)'] >= stats_b['Ingresos ($)'] else ent_b
        margin_winner = ent_a if stats_a['Margen (%)'] >= stats_b['Margen (%)'] else ent_b
        
        if rev_winner == margin_winner:
            st.success(
                f"**Líder Absoluto:** **{rev_winner}** domina tanto en volumen de ingresos (${max(stats_a['Ingresos ($)'], stats_b['Ingresos ($)']):,.2f}) "
                f"como en rentabilidad ({max(stats_a['Margen (%)'], stats_b['Margen (%)']):.1f}%). "
                f"Recomendación: Asignar mayor cuota de presupuesto y modelar sus factores de éxito en el resto del catálogo.",
                icon=":material/trophy:"
            )
        else:
            st.info(
                f"**Equilibrio Estratégico:** **{rev_winner}** genera mayor volumen de facturación bruta, "
                f"mientras que **{margin_winner}** es más eficiente en margen de ganancia ({max(stats_a['Margen (%)'], stats_b['Margen (%)']):.1f}% vs {min(stats_a['Margen (%)'], stats_b['Margen (%)']):.1f}%). "
                f"Recomendación: Usar **{rev_winner}** como imán de adquisición / flujo y potenciar la venta cruzada hacia **{margin_winner}** para maximizar el margen neto combinado.",
                icon=":material/tips_and_updates:"
            )
