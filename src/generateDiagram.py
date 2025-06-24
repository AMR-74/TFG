from src import dbLibrary as dbl
import matplotlib

matplotlib.use('Agg')

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.colors as mcolors
from datetime import datetime
import random as ran
import os

def generateRandomPositions(stations, minDistance=1, maxDistance=5):
    distance = {}
    position = 0
    for station in stations:
        distance[station] = position
        position += ran.randint(minDistance, maxDistance)

    return distance
            

def generateDiagram(outputPath="./railSim/railSimulator/static/img/diagrama.png"):
    #=== CONFIGURATION ===
    segments = []
    collection = dbl.selectCollection("trainLines", "TFG")
    lines = dbl.readCollection(collection)
    
    colors = [
    "#E6194B",  # Rojo fuerte
    "#3CB44B",  # Verde brillante
    "#FFE119",  # Amarillo
    "#0082C8",  # Azul eléctrico
    "#F58231",  # Naranja
    "#911EB4",  # Púrpura
    "#46F0F0",  # Cian claro
    "#F032E6",  # Fucsia
    "#D2F53C",  # Lima
    "#FABEBE",  # Rosa claro
    "#008080",  # Verde petróleo
    "#E6BEFF",  # Lavanda
    "#AA6E28",  # Marrón
    "#800000",  # Rojo oscuro
    "#FFD8B1",  # Melocotón claro
    "#000075",  # Azul marino
    "#808000",  # Oliva
    "#A9A9FF",  # Azul pastel
    "#B10DC9",  # Violeta
    "#FF7F00"   # Naranja oscuro
]
    rangeStations = 0
    stationOrg = float('inf')
    stationEnd = float('-inf')
    indice = 0
    
    if os.path.exists("./railSim/railSimulator/static/img/diagrama.png"):
        os.remove("./railSim/railSimulator/static/img/diagrama.png")

    #=== SEGMENTS TO DRAW ===#
    for line in lines:
        color = colors[indice] 

        stations = line["Stations"]

        departures = line["Timetable_Margins"][0]
        arrivals = line["Timetable_Margins"][1]

        indice += 1
    
        for i in range(len(departures)):
                seg = {
                    "station_origin": chr(ord(stations[0]) + i),
                    "station_destiny": chr(ord(stations[0]) + i + 1),
                    "departure": departures[i],
                    "arrival": arrivals[i],
                    "color": color
                }

                if i < (len(departures) - 1):
                    seg_uni = {
                        "station_origin": chr(ord(stations[0]) + i + 1),
                        "station_destiny": chr(ord(stations[0]) + i + 1),
                        "departure": arrivals[i],
                        "arrival": departures[i+1],
                        "color": color  
                    }

                    segments.append(seg_uni)

                segments.append(seg)
            

                stationOrg = min(stationOrg, ord(stations[0]))
                stationEnd = max(stationEnd, ord(stations[-1]))

                rangeStations = stationEnd - stationOrg

        stationsDiagram = [chr(stationOrg), chr(stationOrg + rangeStations)]
        stationlist = [chr(i) for i in range(ord(stationsDiagram[0]), ord(stationsDiagram[1]) + 1)]

    est_to_y = generateRandomPositions(stationlist, minDistance=1, maxDistance=5)
    fig, ax = plt.subplots(figsize=(12,6))
    ax.set_xticks(list(est_to_y.values()))
    ax.set_xticklabels(list(est_to_y.keys()))
    ax.set_title("Diagrama de horarios de trenes")
    ax.yaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    ax.yaxis.set_major_locator(mdates.HourLocator(interval=1))
    ax.set_ylabel("Hour")
    ax.set_xlabel("Stations")
    ax.invert_yaxis()

    for seg in segments:
        y0 = est_to_y[seg["station_origin"]]
        y1 = est_to_y[seg["station_destiny"]]
        x0 = seg["departure"]
        x1 = seg["arrival"]
        ax.fill_between([y0,y1], x0, x1, color=seg["color"], alpha=0.6)

    plt.tight_layout()
    plt.savefig(outputPath)
    plt.close()
    print(f"Diagrama guardado como {outputPath}")

