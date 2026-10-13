import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def render_custom_builder(df: pd.DataFrame, profiler_info: dict):
    st.subheader(":material/palette: Estudio de Visuales & Constructor Libre")
    st.markdown("Diseña y personaliza tus propios gráficos interactivos a partir de cualquier columna de tu base de datos.")

    numeric_cols = profiler_info.get('numeric_cols', [])
    categorical_cols = profiler_info.get('categorical_cols', [])
    date_cols = profiler_info.get('date_cols', [])
    
    all_cols = df.columns.tolist()

    col_cfg1, col_cfg2, col_cfg3, col_cfg4 = st.columns(4)

    with col_cfg1:
        chart_type = st.selectbox(
            "Tipo de Gráfico",
            [
                "Barras Verticales",
                "Barras Horizontales",
                "Líneas de Tendencia",
                "Área",
                "Dispersión (Scatter)",
                "Circular / Donut",
                "Diagrama de Caja (Boxplot)",
                "Treemap Jerárquico",
                "Histograma"
            ]
        )

    with col_cfg2:
        x_candidate = categorical_cols + date_cols + numeric_cols
        x_col = st.selectbox("Clasificar por (ej. Categoría, Fecha, Canal)", x_candidate, index=0 if x_candidate else 0)

    with col_cfg3:
        y_candidate = numeric_cols if numeric_cols else all_cols
        y_col = st.selectbox("Valor a calcular (ej. Ventas, Ganancia)", y_candidate, index=0 if y_candidate else 0)

    with col_cfg4:
        agg_func = st.selectbox(
            "Forma de calcular",
            ["Sumar el total acumulado", "Calcular el promedio", "Contar número de ventas", "Ver el valor más alto", "Ver el valor más bajo"],
            index=0
        )

    col_sub1, col_sub2, col_sub3 = st.columns(3)
    with col_sub1:
        color_candidates = ["(Ninguno)"] + [c for c in categorical_cols if c != x_col]
        color_col = st.selectbox("Separar por color (opcional)", color_candidates, index=0)

    with col_sub2:
        top_n = st.slider("Cuántos elementos mostrar (Top)", min_value=5, max_value=50, value=15, step=5)

    with col_sub3:
        palette_choice = st.selectbox(
            "Esquema de Color",
            ["Corporativo (Azul/Naranja)", "Viridis", "Tealrose", "Plotly Default", "Pastel"]
        )
        palettes = {
            "Corporativo (Azul/Naranja)": ['#118DFF', '#E66C37', '#12239E', '#00B7C3', '#6B2D5C'],
            "Viridis": px.colors.sequential.Viridis,
            "Tealrose": px.colors.diverging.Tealrose,
            "Plotly Default": px.colors.qualitative.Plotly,
            "Pastel": px.colors.qualitative.Pastel
        }
        chosen_pal = palettes[palette_choice]

    # Procesar agregación
    agg_map = {
        "Sumar el total acumulado": "sum",
        "Calcular el promedio": "mean",
        "Contar número de ventas": "count",
        "Ver el valor más alto": "max",
        "Ver el valor más bajo": "min"
    }
    actual_agg = agg_map.get(agg_func, "sum")

    chart_df = df.copy()

    # Si es Boxplot o Histograma, podemos graficar sobre datos crudos
    if "Boxplot" in chart_type:
        fig = px.box(
            chart_df,
            x=x_col,
            y=y_col,
            color=color_col if color_col != "(Ninguno)" else None,
            template='plotly_white',
            color_discrete_sequence=chosen_pal if isinstance(chosen_pal, list) else None
        )
    elif "Histograma" in chart_type:
        fig = px.histogram(
            chart_df,
            x=y_col,
            color=color_col if color_col != "(Ninguno)" else None,
            marginal="box",
            template='plotly_white',
            color_discrete_sequence=chosen_pal if isinstance(chosen_pal, list) else None
        )
    else:
        # Agregación previa
        group_cols = [x_col]
        if color_col != "(Ninguno)" and color_col in chart_df.columns:
            group_cols.append(color_col)

        if actual_agg == "count":
            grouped = chart_df.groupby(group_cols).size().reset_index(name='conteo')
            metric_plot_col = 'conteo'
        else:
            grouped = chart_df.groupby(group_cols)[y_col].agg(actual_agg).reset_index()
            metric_plot_col = y_col

        # Limitar a Top N
        top_cats = grouped.groupby(x_col)[metric_plot_col].sum().nlargest(top_n).index
        grouped = grouped[grouped[x_col].isin(top_cats)]

        if "Barras Verticales" in chart_type:
            fig = px.bar(
                grouped,
                x=x_col,
                y=metric_plot_col,
                color=color_col if color_col != "(Ninguno)" else None,
                barmode='group',
                template='plotly_white',
                color_discrete_sequence=chosen_pal if isinstance(chosen_pal, list) else None
            )
        elif "Barras Horizontales" in chart_type:
            fig = px.bar(
                grouped.sort_values(metric_plot_col, ascending=True),
                y=x_col,
                x=metric_plot_col,
                orientation='h',
                color=color_col if color_col != "(Ninguno)" else None,
                template='plotly_white',
                color_discrete_sequence=chosen_pal if isinstance(chosen_pal, list) else None
            )
        elif "Líneas de Tendencia" in chart_type:
            fig = px.line(
                grouped,
                x=x_col,
                y=metric_plot_col,
                markers=True,
                color=color_col if color_col != "(Ninguno)" else None,
                template='plotly_white',
                color_discrete_sequence=chosen_pal if isinstance(chosen_pal, list) else None
            )
        elif "Área" in chart_type:
            fig = px.area(
                grouped,
                x=x_col,
                y=metric_plot_col,
                color=color_col if color_col != "(Ninguno)" else None,
                template='plotly_white',
                color_discrete_sequence=chosen_pal if isinstance(chosen_pal, list) else None
            )
        elif "Dispersión (Scatter)" in chart_type:
            scatter_df = grouped.copy()
            scatter_df['bubble_size'] = scatter_df[metric_plot_col].clip(lower=0)
            fig = px.scatter(
                scatter_df,
                x=x_col,
                y=metric_plot_col,
                size='bubble_size',
                color=color_col if color_col != "(Ninguno)" else None,
                template='plotly_white',
                color_discrete_sequence=chosen_pal if isinstance(chosen_pal, list) else None,
                labels={'bubble_size': metric_plot_col}
            )
        elif "Circular / Donut" in chart_type:
            fig = px.pie(
                grouped.head(10),
                names=x_col,
                values=metric_plot_col,
                hole=0.4,
                template='plotly_white',
                color_discrete_sequence=chosen_pal if isinstance(chosen_pal, list) else None
            )
        elif "Treemap" in chart_type:
            path_cols = [x_col]
            if color_col != "(Ninguno)":
                path_cols = [color_col, x_col]
            grouped_pos = grouped[grouped[metric_plot_col] > 0]
            if len(grouped_pos) < len(grouped):
                st.info("Se omitieron valores menores o iguales a cero, ya que el gráfico Treemap requiere valores estrictamente positivos.")
            if not grouped_pos.empty:
                fig = px.treemap(
                    grouped_pos,
                    path=path_cols,
                    values=metric_plot_col,
                    color=metric_plot_col,
                    template='plotly_white',
                    color_continuous_scale='Blues'
                )
            else:
                st.warning("No hay valores positivos para renderizar el gráfico Treemap.")
                return
        else:
            fig = px.bar(grouped, x=x_col, y=metric_plot_col, template='plotly_white')

    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=20, t=30, b=20)
    )
    st.plotly_chart(fig, use_container_width=True)

    # Descarga de datos
    with st.expander(":material/download: Ver y Exportar Datos de este Gráfico"):
        st.dataframe(grouped if 'grouped' in locals() else chart_df.head(100), use_container_width=True)
        csv_data = (grouped if 'grouped' in locals() else chart_df).to_csv(index=False).encode('utf-8')
        st.download_button(
            label=":material/file_download: Descargar Resumen en CSV",
            data=csv_data,
            file_name="resumen_grafico_personalizado.csv",
            mime="text/csv"
        )
