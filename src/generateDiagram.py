# generateDiagram.py
from src import dbLibrary as dbl
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import os
import random as ran

#=== GLOBAL VARIABLES ===#

#=== FUNCTIONS ===#
def generateRandomPositions(stations, minDistance=1, maxDistance=5):
    distance = {}
    position = 0
    for station in stations:
        distance[station] = position
        position += ran.randint(minDistance, maxDistance)
    return distance

def _split_times(t0, t1, k: int):
    try:
        k = max(int(k), 1)
    except:
        k = 1
    if k == 1 or t1 <= t0:
        return [t0, t1]
    delta = (t1 - t0) / k
    return [t0 + j * delta for j in range(k + 1)]

def generateDiagram(opt: int, canton_lines=None,
                    outputPath: str = "./railSim/railSimulator/static/img/diagrama.png"):

    collection = dbl.selectCollection("trainLines", "TFG")
    lines = list(dbl.readCollection(collection))

    colors = [
        "#E6194B", "#3CB44B", "#FFE119", "#0082C8", "#F58231", "#911EB4",
        "#46F0F0", "#F032E6", "#D2F53C", "#FABEBE", "#008080", "#E6BEFF",
        "#AA6E28", "#800000", "#FFD8B1", "#000075", "#808000", "#A9A9FF",
        "#B10DC9", "#FF7F00", "#1F77B4", "#2CA02C", "#D62728", "#9467BD",
        "#7F7F7F", "#BCBD22", "#17BECF", "#FF69B4", "#40E0D0", "#B22222",
        "#228B22", "#00CED1", "#FF1493", "#C71585", "#A0522D", "#6A5ACD",
        "#20B2AA", "#FFD700", "#8C564B", "#E377C2",
    ]

    if os.path.exists(outputPath):
        os.remove(outputPath)

    segments = []
    all_stations = set()
    for idx, line in enumerate(lines):
        color = colors[idx % len(colors)]
        departures = line["Timetable_Margins"][0]  # datetimes
        arrivals   = line["Timetable_Margins"][1]  # datetimes
        stations   = line["Stations"]
        all_stations.update(stations)

        for i in range(len(departures) - 1):
            segments.append({
                "station_origin": stations[i],
                "station_destiny": stations[i + 1],
                "departure": departures[i],
                "arrival": arrivals[i],
                "color": color,
                "line_index": idx,
                "seg_index": i,
            })

            segments.append({
                "station_origin": stations[i + 1],
                "station_destiny": stations[i + 1],
                "departure": arrivals[i],
                "arrival": departures[i + 1],
                "color": color,
                "line_index": idx,
                "seg_index": None,
            })

    if canton_lines:
        for seg in segments:
            i = seg["seg_index"]
            li = seg["line_index"]
            if i is not None and li < len(canton_lines) and i < len(canton_lines[li]):
                seg["cantons"] = max(int(canton_lines[li][i]), 1)

    stationlist = sorted(all_stations)
    est_to_x = generateRandomPositions(stationlist, minDistance=1, maxDistance=5)

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.set_xticks(list(est_to_x.values()))
    ax.set_xticklabels(list(est_to_x.keys()))
    ax.set_title("Diagrama de horarios de trenes")
    ax.yaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    ax.yaxis.set_major_locator(mdates.HourLocator(interval=1))
    ax.set_ylabel("Hora")
    ax.set_xlabel("Estaciones")
    ax.invert_yaxis()

    # 4) Pintado
    for seg in segments:
        x0 = est_to_x[seg["station_origin"]]
        x1 = est_to_x[seg["station_destiny"]]
        t0 = seg["departure"]
        t1 = seg["arrival"]

        if opt == 2 and seg.get("seg_index") is not None:
            k = int(seg.get("cantons", 1))
            times = _split_times(t0, t1, k)
            if k <= 1 or x1 == x0 or t1 <= t0:
                ax.fill_between([x0, x1], t0, t1, color=seg["color"], alpha=0.6)
            else:
                dx = (x1 - x0) / k
                for j in range(k):
                    xl = x0 + j * dx
                    xr = x0 + (j + 1) * dx
                    ax.fill_between([xl, xr], times[j], times[j + 1], color=seg["color"], alpha=0.6)
        else:
            ax.fill_between([x0, x1], t0, t1, color=seg["color"], alpha=0.6)

    plt.tight_layout()
    plt.savefig(outputPath)
    plt.close()
