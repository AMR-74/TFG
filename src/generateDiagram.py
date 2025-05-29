from src import dbLibrary as dbl
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
        "#1f77b4",  # azul
        "#ff7f0e",  # naranja
        "#2ca02c",  # verde
        "#d62728",  # rojo
        "#9467bd",  # morado
        "#8c564b",  # marrón oscuro
        "#e377c2",  # rosa fuerte
        "#7f7f7f",  # gris
        "#bcbd22",  # verde oliva
        "#17becf",  # azul celeste
        "#393b79",  # azul marino
        "#637939",  # verde musgo
        "#8c6d31",  # marrón dorado
        "#843c39",  # rojo vino
        "#7b4173"   # púrpura intenso
    ]
    rangeStations = 0
    stationEnd = 0
    stationOrg = 0
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
            

                if ord(stations[0]) < 65 or ord(stations[0]) < stationOrg:
                    stationOrg = ord(stations[0])

                if ord(stations[1]) < 65 or ord(stations[1]) > stationEnd:
                    stationEnd = ord(stations[1])

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

