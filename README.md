# Aplicación de Inteligencia de Precios para el Sector Retail Venezolano

[![Licencia](https://img.shields.io/badge/Licencia-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Poetry](https://img.shields.io/badge/dependency%20management-Poetry-blue.svg)](https://python-poetry.org/)
[![Dash](https://img.shields.io/badge/Dashboard-Dash-brightgreen.svg)](https://dash.plotly.com/)

Repositorio del Trabajo Especial de Grado (TEG) para la carrera de Computación de la **Facultad Experimental de Ciencias y Tecnología (FACYT)** de la Universidad de Carabobo.

**Título del Proyecto:** _Aplicación para comparar precios de la competencia del sector retail de alimentos venezolano, con Web Scraping y Aprendizaje Automático. Un enfoque de Inteligencia de Negocio._

---

## 📌 Descripción del Proyecto

Este proyecto presenta una solución integral de **Inteligencia de Precios** diseñada para el sector retail de alimentos en Venezuela. La aplicación automatiza el proceso de recolección de datos de precios de competidores mediante técnicas de **Web Scraping**, los procesa, almacena en una base de datos robusta, y aplica modelos de **Aprendizaje Automático** para predecir precios óptimos y descubrir patrones.

El sistema culmina en un **Dashboard interactivo** que sirve como una herramienta de Inteligencia de Negocios (BI), permitiendo a los usuarios (administradores, analistas de precios, analistas de datos) visualizar tendencias, comparar precios, simular escenarios y entender las predicciones del modelo de ML.

### Objetivos Clave Alcanzados

- **Automatización de la Recolección de Datos:** Se desarrolló un módulo de *price scraping* robusto y escalable.
- **Procesamiento y Almacenamiento Centralizado:** Los datos se limpian, normalizan y almacenan en una base de datos PostgreSQL, asegurando consistencia e integridad.
- **Modelado Predictivo:** Se implementó un pipeline de Machine Learning que se re-entrena periódicamente para sugerir precios óptimos.
- **Inteligencia de Negocios Visual:** Un dashboard con control de acceso por roles permite la exploración de datos históricos, el análisis de precios de la competencia y la interpretación del modelo de ML.
- **Arquitectura Modular:** El sistema se diseñó con componentes desacoplados (scraper, base de datos, pipeline de ML, dashboard) para facilitar el mantenimiento y la escalabilidad.

---

## 🛠️ Stack Tecnológico

- **Lenguaje Principal:** Python 3.10+
- **Gestión de Dependencias:** [Poetry](https://python-poetry.org/)
- **Web Scraping:** Selenium, BeautifulSoup
- **Procesamiento de Datos:** Pandas, NumPy, Scikit-learn
- **Machine Learning & XAI:** Scikit-learn, SHAP, LIME
- **Base de Datos:** PostgreSQL
- **Dashboard y Visualización:** Dash, Plotly, Dash Mantine Components, Dash Bootstrap Components
- **Tareas Programadas:** Schedule
- **Calidad de Código:** Black, isort, Pylint

---

## ⚙️ Instalación y Configuración

Este proyecto utiliza **Poetry** para la gestión de dependencias, lo que garantiza un entorno de desarrollo reproducible.

### Prerrequisitos
- Python 3.10 o superior.
- [Poetry](https://python-poetry.org/docs/#installation) instalado.
- Un servidor de PostgreSQL en ejecución.
- Drivers de navegador para Selenium (ej. ChromeDriver) accesibles en el `PATH` del sistema.

### Pasos de Instalación

1.  **Clonar el repositorio:**
    ```bash
    git clone https://github.com/Pitiyanky/prices_scrapper_teg.git
    cd prices_scrapper_teg
    ```

2.  **Configurar el entorno de Poetry:**
    Poetry leerá el archivo `pyproject.toml` y creará un entorno virtual aislado para el proyecto.
    ```bash
    poetry install
    ```
    *Este comando instalará todas las dependencias necesarias para ejecutar la aplicación y las herramientas de desarrollo.*

3.  **Configurar la Base de Datos:**
    - Copia el archivo `.env.example` a un nuevo archivo llamado `.env`.
    - Edita el archivo `.env` y rellena las credenciales de tu base de datos PostgreSQL. Estas serán utilizadas tanto por la aplicación principal como por los scripts.

4.  **Activar el entorno virtual:**
    Para ejecutar los scripts, primero debes activar el entorno virtual que Poetry ha creado.
    ```bash
    poetry shell
    ```

---

## 📊 Uso de la Aplicación

La aplicación se lanza desde un único punto de entrada que inicia tanto el servidor del dashboard como el scheduler en segundo plano.

1.  **Iniciar la Aplicación:**
    Desde la raíz del proyecto y con el entorno de Poetry activado (`poetry shell`), ejecuta:
    ```bash
    python main.py 
    ```

2.  **Acceder al Dashboard:**
    - Abre tu navegador y ve a `http://localhost:8050` (o el puerto que hayas configurado).
    - Inicia sesión con las credenciales de administrador por defecto la primera vez:
      - **Usuario:** `admin`
      - **Contraseña:** `1234`
    - **¡Importante!** Se recomienda cambiar la contraseña del administrador desde el panel de configuración después del primer inicio de sesión.

### Flujo de Trabajo del Sistema

- **Tareas Programadas:** Un scheduler se ejecuta en un hilo en segundo plano. Por defecto, está configurado para ejecutarse diariamente (la hora es configurable en el dashboard). Este proceso:
    1.  Ejecuta los scrapers para recolectar datos frescos.
    2.  Preprocesa y guarda los nuevos datos en la base de datos.
    3.  Ejecuta el pipeline de entrenamiento del modelo de Machine Learning con los datos actualizados.
    4.  Refresca los datos del `CentralAnalyzer` del dashboard para que los usuarios vean la información más reciente.

- **Panel de Administración:** Permite crear, editar y eliminar usuarios, así como modificar parámetros del sistema, como la hora de ejecución del scheduler.

---

## 🤝 Contribuciones

Este proyecto es parte de un trabajo académico, pero las sugerencias y contribuciones son bienvenidas para futuras mejoras. Si deseas contribuir:

1.  **Abre un _Issue_**: Discute el cambio que deseas hacer o el bug que has encontrado.
2.  **Haz un _Fork_**: Crea una copia del repositorio en tu propia cuenta.
3.  **Crea una _Branch_**: `git checkout -b feature/nombre-de-tu-feature`.
4.  **Envía un _Pull Request_**: Envía tus cambios para su revisión.

---

## 📜 Licencia

Este proyecto está distribuido bajo la licencia MIT. Consulta el archivo `LICENSE` para más detalles.

---

## 🙏 Agradecimientos

- A la **Universidad de Carabobo** y a la **FACYT** por el apoyo académico y los recursos proporcionados.
- Al tutor del proyecto, por su inestimable guía técnica y metodológica.
- A las comunidades de código abierto cuyas herramientas y bibliotecas hicieron posible este proyecto.