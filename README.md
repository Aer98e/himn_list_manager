# Gestor de Himnos Litúrgicos

## Descripción

Este proyecto es un sistema de gestión de himnos diseñado para procesar datos de himnos desde archivos Excel. Sus funciones principales incluyen la normalización de títulos de himnos, la detección y el manejo de himnos nuevos o desconocidos, el análisis de frecuencia de uso de los himnos y la generación de reportes formateados en archivos Excel. El sistema está pensado para facilitar la planificación litúrgica mediante la organización y el seguimiento del uso de los himnos.

Las interacciones con el usuario, como la selección de archivos y las confirmaciones, se realizan en español.

## Características Principales

*   **Procesamiento de Archivos Excel:** Extrae datos de himnos directamente desde hojas de cálculo Excel.
*   **Normalización de Títulos:** Estandariza los títulos de los himnos para un manejo consistente (ej. elimina acentos, puntuación y convierte a minúsculas).
*   **Detección de Himnos Nuevos/Desconocidos:** Compara los himnos del archivo procesado con una base de datos de referencia y permite al usuario confirmar coincidencias para títulos no reconocidos mediante comparación por similitud (fuzzy matching).
*   **Gestión de Frecuencias:** Realiza un seguimiento de la frecuencia con la que se utiliza cada himno y actualiza una base de datos con esta información.
*   **Detección de Duplicados:** Identifica si un mismo himno se ha programado varias veces en el archivo procesado.
*   **Asistente de Análisis de Uso:** Proporciona herramientas interactivas en consola para analizar patrones de uso de himnos (ej. himnos más/menos usados, himnos usados recientemente).
*   **Generación de Reportes Excel:** Crea un nuevo archivo Excel con los himnos organizados y formateados según las especificaciones del usuario.
*   **Manejo de Configuración:** Utiliza archivos de configuración para parámetros de formato y extracción.
*   **Registro de Actividad (Logging):** Mantiene un registro de las operaciones y errores de la aplicación.

## Prerrequisitos

*   Python 3.x (se recomienda Python 3.7 o superior)
*   Pip (generalmente viene incluido con las instalaciones de Python)

## Configuración e Instalación

El proyecto utiliza un script `run.py` para automatizar la configuración del entorno y la ejecución de la aplicación.

1.  **Clonar o Descargar el Proyecto:**
    *   Si usa Git: `git clone <url_del_repositorio>`
    *   Alternativamente, descargue y descomprima los archivos del proyecto en un directorio de su elección.

2.  **Navegar al Directorio del Proyecto:**
    ```bash
    cd ruta/a/su/proyecto
    ```

3.  **Ejecutar el Script de Inicio:**
    El script `run.py` se encarga de:
    *   Crear un entorno virtual llamado `local_1/` dentro del directorio del proyecto si no existe.
    *   Verificar el archivo `requirements.txt`. Si ha cambiado desde la última ejecución, actualizará las dependencias. Si es la primera vez, instalará todas las dependencias necesarias.
    *   Finalmente, ejecutar el script principal de la aplicación (`main.py`).

    Para iniciar este proceso, ejecute:
    ```bash
    python run.py
    ```
    Asegúrese de tener Python añadido a su PATH. Si tiene múltiples versiones de Python, podría necesitar usar `python3 run.py`.

## Estructura de Directorios (Resumen)

*   `configs/`: Contiene archivos de configuración JSON para diversos aspectos de la aplicación.
*   `database/`: Almacena los archivos de base de datos SQLite.
*   `data_processing/`: Módulos encargados de la extracción, transformación y formateo de los datos de los himnos.
*   `database_interact/`: Módulos para la interacción con las bases de datos (consultas, actualizaciones).
*   `interact_user/`: Módulos para la interacción con el usuario (diálogos de selección de archivos, menús en consola).
*   `logs/`: (Si se configura un FileHandler en el logger) Contendría los archivos de registro de la aplicación. Actualmente, los logs se muestran en consola.
*   `others/`: Puede contener scripts misceláneos o artefactos guardados (como objetos `.pkl`).
*   `tests/`: Contiene los tests unitarios del proyecto.
*   `utils/`: Funciones de utilidad y helpers generales.
*   `local_1/`: Entorno virtual creado por `run.py` (no incluir en control de versiones si se usa Git).

**Nota sobre directorios de entrada/salida:**
*   **Archivos de Entrada:** El usuario selecciona el archivo Excel a procesar mediante un diálogo gráfico. No hay un directorio de entrada fijo; el sistema recuerda el último directorio utilizado.
*   **Archivos de Salida:** De forma similar, el usuario es consultado para elegir la ubicación y el nombre del archivo Excel generado.

## Uso

1.  **Preparar el Archivo Excel:** Asegúrese de que su archivo Excel con los datos de los himnos esté listo.
2.  **Ejecutar la Aplicación:**
    Abra una terminal o consola, navegue al directorio raíz del proyecto y ejecute:
    ```bash
    python run.py
    ```
3.  **Interacción con el Programa:**
    *   Se le pedirá que **seleccione el archivo Excel** a través de un diálogo gráfico.
    *   Si se encuentran **títulos de himnos desconocidos**, se le presentarán posibles coincidencias y deberá confirmar si son correctas (s/n).
    *   Se mostrarán **duplicaciones** de himnos si existen en la hoja actual.
    *   Tendrá acceso a un **asistente de análisis de uso de himnos** en la consola.
    *   Se le pedirá que ingrese un **título para la hoja de himnos** que se generará.
    *   Finalmente, se le pedirá que **elija la ubicación y el nombre para guardar el archivo Excel** resultante a través de un diálogo gráfico.

## Configuración

Los archivos de configuración principales se encuentran en el directorio `configs/`:

*   `formatting.json`: Define los estilos (fuentes, colores, rellenos, tamaños de fila/columna) que se aplican al archivo Excel generado.
*   `extraction_settings.json`: Contiene configuraciones para la extracción de datos, como el `hymn_identifier` (el texto que marca el inicio de un bloque de himnos en el Excel de entrada).
*   `path_file.json`: Almacena automáticamente la ruta del último directorio utilizado para la selección/guardado de archivos, facilitando futuras interacciones.

## Base de Datos

El sistema utiliza dos bases de datos SQLite ubicadas en el directorio `database/`:

*   `search_ref.db`:
    *   **Propósito:** Base de datos de referencia para los títulos de los himnos.
    *   **Tablas Clave (ejemplo):**
        *   `Himnos`: Contiene los ID de los himnos y sus títulos oficiales.
        *   `Indice_busqueda`: Mapea títulos normalizados a los ID de los himnos para facilitar búsquedas y coincidencias.
*   `Registro_General_Himnos_2.db`:
    *   **Propósito:** Almacena información general de los himnos y sus frecuencias de uso.
    *   **Tablas Clave (ejemplo):**
        *   `Himnos`: Podría contener detalles adicionales de los himnos (numeración, si es nuevo, etc.).
        *   `Frecuencias`: Registra la frecuencia de uso "útil" (reciente) y "real" (total) de cada himno.

## Ejecución de Pruebas

Para ejecutar los tests unitarios:

1.  Asegúrese de tener las dependencias de desarrollo instaladas (si las hubiera; actualmente, las dependencias de `requirements.txt` son suficientes).
2.  Navegue al directorio raíz del proyecto.
3.  Ejecute el siguiente comando para que `unittest` descubra y corra todas las pruebas en el directorio `tests/`:
    ```bash
    python -m unittest discover tests
    ```
    O, para ejecutar un archivo de prueba específico (por ejemplo, `test_helpers.py`):
    ```bash
    python tests/test_helpers.py
    ```

## Contribuciones

Actualmente, no hay guías formales para contribuciones. Si desea contribuir, por favor contacte al mantenedor del proyecto o abra un "issue" para discutir los cambios.
