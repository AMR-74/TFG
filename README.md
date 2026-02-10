# RailSys - Herramienta de Simulación Ferroviaria

Este proyecto es una aplicación web desarrollada en Django diseñada para realizar simulaciones ferroviarias, cálculos de capacidad y gestión de cantones. Forma parte de un Trabajo de Fin de Grado (TFG).

## Descripción

RailSys permite procesar datos de infraestructura y suministro (supply data) definidos en archivos YAML para generar diagramas y cálculos relacionados con la operación ferroviaria.

### Funcionalidades principales
*   **Simulación Core (src/):** Lógica independiente de simulación que incluye:
    *   `cantonCalculator.py`: Algoritmos para el cálculo de cantones.
    *   `capacity.py`: Análisis de capacidad de la línea.
    *   `generateDiagram.py`: Generación de gráficos y diagramas.
    *   `readYamlFiles.py`: Procesamiento de archivos de entrada.
*   **Interfaz Web (railSim):** Aplicación Django que sirve como interfaz de usuario para configurar y visualizar las simulaciones.

## Estructura del Proyecto

La organización del código separa la lógica de simulación (`src`) del framework web (`railSim`):

```text
├── railSim/                # Proyecto Django (Backend/Frontend)
│   ├── manage.py           # Script de gestión de Django
│   ├── railSim/            # Configuración del proyecto (settings, urls)
│   └── railSimulator/      # Aplicación principal
│       ├── templates/      # Plantillas HTML
│       ├── static/         # Archivos estáticos
│       ├── models.py       # Modelos de datos
│       └── views.py        # Controladores de la vista
├── src/                    # Motor de Simulación (Scripts Python)
│   ├── cantonCalculator.py
│   ├── capacity.py
│   ├── dbLibrary.py
│   ├── generateDiagram.py
│   ├── readYamlFiles.py
│   ├── simLibrary.py
│   └── supply_data.yaml    # Datos de simulación locales
├── supply_data.yaml        # Archivo de datos en raíz
└── requirements.txt        # Dependencias del proyecto
```
## Instalación y Despliegue
Prerrequisitos
• Python 3.x
• Virtualenv
### 1. Configuración del entorno
```text
Crear y activar entorno virtual
python -m venv tfg_env
source tfg_env/bin/activate  # Linux/Mac
.\tfg_env\Scripts\activate   # Windows
```
### 2. Instalar dependencias
pip install -r requirements.txt
### 3. Ejecutar la aplicación web
Navega al directorio del proyecto Django y ejecuta el servidor:
```text
cd railSim
python manage.py runserver
La aplicación estará disponible en http://127.0.0.1:8000/.
```
## Tecnologías
```text
• Lógica: Python (Scripts en src/)
• Web Framework: Django
• Datos: MongoDB
```
## Autores
• AMR - Desarrollo del TFG
