from src import dbLibrary as dbl
import matplotlib

# Usar backend 'Agg' para generar imágenes sin entorno gráfico
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import random as ran
import os


def generateRandomPositions(stations, minDistance=1, maxDistance=5):
    """
    Asigna posiciones espaciales aleatorias (pero progresivas) a las estaciones para visualización en el gráfico.

    Parameters
    ----------
    stations : list
        Lista de estaciones (códigos o letras).
    minDistance : int, optional
        Distancia mínima entre estaciones consecutivas (default = 1).
    maxDistance : int, optional
        Distancia máxima entre estaciones consecutivas (default = 5).

    Returns
    -------
    dict
        Diccionario con la estación como clave y su posición en el eje X como valor.
    """
    distance = {}
    position = 0
    for station in stations:
        distance[station] = position
        position += ran.randint(minDistance, maxDistance)

    return distance
            

def generateDiagram(outputPath="./railSim/railSimulator/static/img/diagrama.png"):
    """
    Genera un diagrama visual de horarios ferroviarios a partir de los datos almacenados en la base de datos.

    La función lee las líneas de tren desde la base de datos, simula las estaciones si no están guardadas todas,
    y genera un gráfico de tipo diagrama de tiempos donde el eje X representa estaciones y el eje Y las horas.

    Parameters
    ----------
    outputPath : str, optional
        Ruta donde se guardará el gráfico generado (default = "./railSim/railSimulator/static/img/diagrama.png").

    Returns
    -------
    None
        La imagen se guarda como archivo y no se retorna nada.
    """
    segments = []
    collection = dbl.selectCollection("trainLines", "TFG")
    lines = dbl.readCollection(collection)
    
    # Colores para diferenciar líneas
    colors = [
    "#E6194B", "#3CB44B", "#FFE119", "#0082C8", "#F58231", "#911EB4",
    "#46F0F0", "#F032E6", "#D2F53C", "#FABEBE", "#008080", "#E6BEFF",
    "#AA6E28", "#800000", "#FFD8B1", "#000075", "#808000", "#A9A9FF",
    "#B10DC9", "#FF7F00", "#1F77B4", "#2CA02C", "#D62728", "#9467BD", 
    "#7F7F7F", "#BCBD22", "#17BECF", "#FF69B4", "#40E0D0", "#B22222",
    "#228B22", "#00CED1", "#FF1493", "#C71585", "#A0522D", "#6A5ACD",
    "#20B2AA", "#FFD700", "#8C564B", "#E377C2",
]

    # Eliminar imagen previa si existe
    if os.path.exists(outputPath):
        os.remove(outputPath)

    all_stations = set()
    indice = 0

    # Recorrer cada línea registrada
    for line in lines:
        color = colors[indice % len(colors)] 
        indice += 1

        # Extraer márgenes horarios
        departures = line["Timetable_Margins"][0]
        arrivals = line["Timetable_Margins"][1]
        stations = line["Stations"]

        all_stations.update(stations)

        for i in range(len(departures) - 1):
            # Segmento de desplazamiento
            seg = {
                "station_origin": stations[i],
                "station_destiny": stations[i + 1],
                "departure": departures[i],
                "arrival": arrivals[i],
                "color": color
            }
            segments.append(seg)

            # Segmento de parada (excepto el último tramo)
            if i < len(departures) - 1:
                seg_stop = {
                    "station_origin": stations[i + 1],
                    "station_destiny": stations[i + 1],
                    "departure": arrivals[i],
                    "arrival": departures[i + 1],
                    "color": color
                }
                segments.append(seg_stop)

    # Asignar posiciones visuales a estaciones simuladas
    stationlist = sorted(all_stations)
    est_to_y = generateRandomPositions(stationlist, minDistance=1, maxDistance=5)

    # Crear gráfico
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.set_xticks(list(est_to_y.values()))
    ax.set_xticklabels(list(est_to_y.keys()))
    ax.set_title("Diagrama de horarios de trenes")
    ax.yaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    ax.yaxis.set_major_locator(mdates.HourLocator(interval=1))
    ax.set_ylabel("Hora")
    ax.set_xlabel("Estaciones")
    ax.invert_yaxis()

    # Pintar los segmentos
    for seg in segments:
        y0 = est_to_y[seg["station_origin"]]
        y1 = est_to_y[seg["station_destiny"]]
        x0 = seg["departure"]
        x1 = seg["arrival"]
        ax.fill_between([y0, y1], x0, x1, color=seg["color"], alpha=0.6)

    plt.tight_layout()
    plt.savefig(outputPath)
    plt.close()
    print(f"Diagrama guardado como {outputPath}")
