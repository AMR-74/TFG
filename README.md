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
• Python 3.11 o superior
• Virtualenv
### 1. Configuración del entorno
```text
Se podrá proceder de 2 maneras, usando el archivo prepareWorkspace.bat, que configura la instalación de un entorno virtual
en el directorio donde se almacene el repositorio de manera local.

O en el caso de preferirlo, se podrá crear el entorno virtual con venv, de manera manual, siempre que se cree en la raiz del proyecto.
```
### 2. Instalar dependencias
De la misma manera que en el punto anterior, el archivo prepareWorkspace.bat, gestiona la instalación de dependencias, en el caso de que se quiera
realizar de manera manual, se procede, activando el entorno virtual mediante línea de comando y posteriormente ejecutando el siguiente comando:

pip install -r requirements.txt
### 3. Ejecutar la aplicación web
Se dispone de un archivo startWorkspace.bat, que inicializa el entorno virtual previamente creado y lanza el servidor de desarrollo de Django.
Si se desea realizar de manera manual, se debe ejecutar el siguiente comando, con el entorno virtual activo, y en el directorio raiz del proyecto:

python railSim\manage.py runserver
## Tecnologías
```text
• Lógica: Python (Scripts en src/)
• Web Framework: Django
• Datos: MongoDB
```
## Autores
• Alberto Martín - Desarrollo del TFG
