# Plan Fénix: Analytics de Ventas (SQL + Python)

Este repositorio ha sido transformado como parte del **Plan Fénix** para evolucionar de un Jupyter Notebook tradicional a un **Dashboard Interactivo Profesional** con calidad de portafolio y un diseño corporativo estilo Power BI.

Demuestra cómo construir un motor analítico robusto extrayendo consultas en **SQL puro** (SQLite/DuckDB) y presentándolas a través de un Frontend dinámico construido en **Python (Streamlit)** y **Plotly**.

## Características Principales
- **Arquitectura Modular:** Separación clara entre la lógica de extracción de datos (archivos `.sql`), el motor de la base de datos y la interfaz gráfica.
- **Generación de Datos Sintéticos:** Un script en Python capaz de generar una base de datos relacional robusta simulando años de historial de ventas (usando la librería Faker).
- **Dashboard Dinámico y Corporativo:** Diseño moderno y minimalista en modo claro, con métricas clave, alertas inteligentes de negocio y capacidades de Drill-down por producto.

## Estructura del Repositorio

```text
sql-python-analytics-ventas/
├── archive/
│   └── Taller_consultas.ipynb      # Notebook original (Exploratorio)
├── data/                           # Base de datos SQLite (Generada localmente)
├── sql/
│   ├── kpi_summary.sql             # SQL para métricas principales
│   ├── sales_trends.sql            # SQL para tendencia temporal
│   └── product_performance.sql     # SQL para análisis de productos
├── src/
│   ├── data_generator.py           # Generador de datos con Faker
│   └── db_client.py                # Cliente de base de datos en Python
├── app.py                          # Interfaz interactiva de Streamlit
└── requirements.txt                # Dependencias del proyecto
```

## Instalación y Uso

Sigue estos pasos para levantar el entorno completo de forma local:

### 1. Clonar el repositorio
```bash
git clone https://github.com/Dmgar/corporate-bi-dashboard.git
cd corporate-bi-dashboard
```

### 2. Crear un Entorno Virtual y Activar
```bash
python -m venv .venv
# Windows:
.\.venv\Scripts\Activate.ps1
# Mac/Linux:
source .venv/bin/activate
```

### 3. Instalar Dependencias
```bash
pip install -r requirements.txt
```

### 4. Generar la Base de Datos
Este paso creará el archivo `data/sales_database.db` con aproximadamente 100,000 registros para simular la carga de transacciones.
```bash
python src/data_generator.py
```

### 5. Lanzar el Dashboard Interactivo
```bash
streamlit run app.py
```
*Se abrirá automáticamente una pestaña en tu navegador web en `http://localhost:8501`.*

---

**Tecnologías:** Python 3 | SQLite / DuckDB | Streamlit | Plotly | Pandas | Faker
