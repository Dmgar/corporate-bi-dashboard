# Plan Fénix: Corporate BI Studio · Analytics Avanzado (SQL + Python)

Este repositorio ha sido transformado en un **Dashboard Interactivo Profesional de Inteligencia de Negocio** con calidad ejecutiva, arquitectura modular y un diseño corporativo estilo Power BI / Tableau.

Combina la potencia de **SQL puro** (SQLite / DuckDB) con una interfaz interactiva de alta fidelidad construida en **Python (Streamlit)** y **Plotly**, enriquecida con análisis geográfico coroplético, correlación estadística, matrices de cuadrantes, benchmarking comparativo y un motor inteligente de recomendación de visualizaciones.

---

## Módulos Analíticos & Capacidades

### 1. Mapas Coropléticos & Visualización Territorial
- **Mapas Coropléticos Poligonales:** Proyección a escala mundial, regional (Latinoamérica, Norteamérica, Europa) o por país (código ISO-3 o nombres oficiales).
- **Métricas Seleccionables:** Ingresos Totales, Margen de Rentabilidad (%), Utilidad Neta, Transacciones y Ticket Promedio.
- **Modo Dual:** Alterna entre mapa coroplético y mapa de burbujas geográficas (`px.scatter_geo`).
- **Ranking y Cuota de Mercado:** Tabla interactiva con participación porcentual (%) y gráfico de distribución territorial.

### 2. Barra de Filtros Flotantes & Filtros Rápidos
- **Píldoras Temporales Rápidas:** Filtra al instante por *Todo el Historial*, *Último Año*, *Último Trimestre* o *Últimos 30 días*.
- **Popover Flotante de Filtros:** Ajusta categorías, territorios, canales y segmentos sin ocupar espacio permanente en pantalla.
- **Sincronización Total:** Integrado bidireccionalmente con los filtros detallados del panel lateral.

### 3. Matriz de Dispersión & Cuadrantes Estratégicos BCG
- **Gráfico de Dispersión y Correlación:** Análisis multivariable con cálculo dinámico de regresión lineal, coeficiente de Pearson ($r$), coeficiente de determinación ($R^2$) y diagnóstico de negocio sobre el impacto de los descuentos en los márgenes.
- **Matriz de Cuadrantes BCG:** Clasificación automática de todo el catálogo en 4 cuadrantes con umbrales calculados por mediana:
  - **Estrellas:** Alto Volumen + Alto Margen (Motores de rentabilidad).
  - **Oportunidades:** Bajo Volumen + Alto Margen (Potencial para escalar campañas).
  - **Vacas Lecheras:** Alto Volumen + Bajo Margen (Generadores de flujo; optimizar costos).
  - **En Riesgo:** Bajo Volumen + Bajo Margen (Candidatos a revisión o descontinuación).

### 4. Comparadores Multidimensionales (Benchmarking)
- **Comparador Temporal de Períodos (A vs B):** Enfrenta dos meses o períodos históricos con tarjetas Scorecard de variación ($\Delta \$$ y $\Delta \%$), barras agrupadas y gráfico de variación neta.
- **Comparador de Entidades Cara a Cara:** Compara dos productos, dos canales (ej. Online vs Tienda Física) o dos regiones en un Scorecard normalizado, acompañado de un **Veredicto Ejecutivo Inteligente** generado por reglas.

### 5. Motor de Recomendación Inteligente de Visuales & Pareto (80/20)
- **Perfilado Automático de Datos:** Analiza cualquier archivo cargado (CSV o Excel) o la base de datos predeterminada, detectando columnas temporales, geográficas, financieras y categóricas.
- **Recomendaciones de Negocio:** Sugiere visualizaciones estratégicas personalizadas justificando el valor de cada una para la toma de decisiones.
- **Curva de Concentración de Pareto (80/20):** Identifica automáticamente qué porcentaje de tu catálogo concentra el 80% de tus ingresos.

### 6. Estudio de Visuales & Constructor Libre (Visual Studio)
- Crea gráficos libres a la medida: Barras, Líneas, Dispersión, Áreas, Boxplots, Treemaps, Donut e Histogramas.
- Selecciona ejes, agregaciones (Suma, Promedio, Conteo, Min, Max), esquemas cromáticos y descarga los datos procesados en CSV.

---

## 📁 Estructura del Repositorio

```text
corporate-bi-dashboard/
├── archive/
│   └── Taller_consultas.ipynb          # Notebook original
├── data/
│   └── sales_database.db              # Base de datos relacional SQLite con atributos geo
├── sql/
│   ├── kpi_summary.sql                 # Métricas globales de negocio
│   ├── sales_trends.sql                # Agregación temporal mensual y tasas MoM
│   ├── product_performance.sql         # Desempeño y ranking por producto
│   └── regional_performance.sql        # Rendimiento por región y canal
├── src/
│   ├── components/
│   │   ├── geo_map.py                  # Mapas coropléticos y analítica territorial
│   │   ├── scatter_matrix.py           # Dispersión, correlación y matriz BCG
│   │   ├── comparator.py               # Comparadores temporales y benchmarking A vs B
│   │   ├── floating_filters.py         # Barra flotante y filtros rápidos
│   │   ├── smart_profiler.py           # Detección inteligente de esquema y perfilado
│   │   ├── smart_recommender_ui.py     # Tarjetas de recomendación y curva de Pareto
│   │   └── custom_builder.py           # Estudio de gráficos libres y exportación
│   ├── data_generator.py               # Generador de datos sintéticos enriquecidos
│   └── db_client.py                    # Conector SQLite + DuckDB con fallback seguro
├── app.py                              # Aplicación interactiva principal en Streamlit
└── requirements.txt                    # Dependencias del proyecto
```

---

## 🛠️ Instalación y Puesta en Marcha

### 1. Activar Entorno Virtual
```bash
# Windows:
.\.venv\Scripts\Activate.ps1

# Mac/Linux:
source .venv/bin/activate
```

### 2. Instalar Dependencias
```bash
pip install -r requirements.txt
```

### 3. Generar la Base de Datos (Opcional si ya existe)
```bash
python src/data_generator.py
```

### 4. Iniciar el Dashboard
```bash
streamlit run app.py
```
*El panel se abrirá automáticamente en tu navegador web en `http://localhost:8501`.*

---

**Tecnologías:** Python 3 | SQLite & DuckDB | Streamlit | Plotly | Pandas | NumPy | Faker
