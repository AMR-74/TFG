from src import dbLibrary as dbl
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os
import random as ran

matplotlib.use("Agg")  # Necessary for servers/Django

# === CONSTANTS ===
COLORS = [
    "#E6194B",
    "#3CB44B",
    "#FFE119",
    "#0082C8",
    "#F58231",
    "#911EB4",
    "#46F0F0",
    "#F032E6",
    "#D2F53C",
    "#FABEBE",
    "#008080",
    "#E6BEFF",
    "#AA6E28",
    "#800000",
    "#FFD8B1",
    "#000075",
    "#808000",
    "#A9A9FF",
    "#B10DC9",
    "#FF7F00",
    "#1F77B4",
    "#2CA02C",
    "#D62728",
    "#9467BD",
    "#7F7F7F",
    "#BCBD22",
    "#17BECF",
    "#FF69B4",
    "#40E0D0",
    "#B22222",
    "#228B22",
    "#00CED1",
    "#FF1493",
    "#C71585",
    "#A0522D",
    "#6A5ACD",
    "#20B2AA",
    "#FFD700",
    "#8C564B",
    "#E377C2",
]

# === FUNCTIONS ===


def generate_random_positions(stations, minDistance=1, maxDistance=5):
    """
    Assigns relative positions to stations for the x-axis.
    """
    distance = {}
    position = 0
    for station in stations:
        distance[station] = position
        position += ran.randint(minDistance, maxDistance)
    return distance


def split_times(t0, t1, k):
    """
    Returns [t0, t1, ..., tk] by dividing the interval [t0, t1] into k equal parts.
    """
    try:
        k = max(int(k), 1)
    except (ValueError, TypeError):
        k = 1
    if k == 1 or t1 <= t0:
        return [t0, t1]
    delta = (t1 - t0) / k
    return [t0 + j * delta for j in range(k + 1)]


def generate_diagram(
    opt,
    cantonLines=None,
    outputPath="./railSim/railSimulator/static/img/diagrama.png",
):
    """
    Generates a train schedule diagram.

    opt:
      1 -> Standard diagram.
      2 -> Diagram with temporal sub-segments by cantons (no overlaps within segments).
    cantonLines: List per line with the number of cantons per segment.
    """
    collection = dbl.select_collection("trainLines", "TFG")
    lines = list(dbl.read_collection(collection))

    if os.path.exists(outputPath):
        os.remove(outputPath)

    # 1) Build segments from database
    segments = []
    allStations = set()
    for idx, line in enumerate(lines):
        color = COLORS[idx % len(COLORS)]
        departures = line["Timetable_Margins"][0]  # Datetimes
        arrivals = line["Timetable_Margins"][1]  # Datetimes
        stations = line["Stations"]
        allStations.update(stations)

        for i in range(len(departures) - 1):
            segments.append(
                {
                    "stationOrigin": stations[i],
                    "stationDestiny": stations[i + 1],
                    "departure": departures[i],
                    "arrival": arrivals[i],
                    "color": color,
                    "lineIndex": idx,
                    "segIndex": i,
                }
            )
            # Intermediate stop
            segments.append(
                {
                    "stationOrigin": stations[i + 1],
                    "stationDestiny": stations[i + 1],
                    "departure": arrivals[i],
                    "arrival": departures[i + 1],
                    "color": color,
                    "lineIndex": idx,
                    "segIndex": None,
                }
            )

    # 2) Inject number of cantons per segment if provided
    if cantonLines:
        for seg in segments:
            i = seg["segIndex"]
            li = seg["lineIndex"]
            if i is not None and li < len(cantonLines) and i < len(cantonLines[li]):
                seg["cantons"] = max(int(cantonLines[li][i]), 1)

    # 3) Axes and positions
    stationList = sorted(allStations)
    estToX = generate_random_positions(stationList, minDistance=1, maxDistance=5)

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.set_xticks(list(estToX.values()))
    ax.set_xticklabels(list(estToX.keys()))
    ax.set_title("Train Schedule Diagram")
    ax.yaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    ax.yaxis.set_major_locator(mdates.HourLocator(interval=1))
    ax.set_ylabel("Time")
    ax.set_xlabel("Stations")
    ax.invert_yaxis()

    # 4) Rendering
    for seg in segments:
        x0 = estToX[seg["stationOrigin"]]
        x1 = estToX[seg["stationDestiny"]]
        t0 = seg["departure"]
        t1 = seg["arrival"]

        if opt == 2 and seg.get("segIndex") is not None:
            # New behavior: divide the segment into k temporal sub-segments
            k = int(seg.get("cantons", 1))
            times = split_times(t0, t1, k)
            if k <= 1 or x1 == x0 or t1 <= t0:
                ax.fill_between([x0, x1], t0, t1, color=seg["color"], alpha=0.6)
            else:
                dx = (x1 - x0) / k
                for j in range(k):
                    xl = x0 + j * dx
                    xr = x0 + (j + 1) * dx
                    ax.fill_between(
                        [xl, xr], times[j], times[j + 1], color=seg["color"], alpha=0.6
                    )
        else:
            # Standard mode
            ax.fill_between([x0, x1], t0, t1, color=seg["color"], alpha=0.6)

    plt.tight_layout()
    plt.savefig(outputPath)
    plt.close()
