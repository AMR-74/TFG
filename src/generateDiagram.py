from src import dbLibrary as dbl
import matplotlib
matplotlib.use('Agg') # Necessary for servers/Django
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os
import random as ran

def generateRandomPositions(stations, minDistance=1, maxDistance=5):
    """Assigns relative positions to stations for the x-axis."""
    distance = {}
    position = 0
    for station in stations:
        distance[station] = position
        position += ran.randint(minDistance, maxDistance)
    return distance

def generateDiagram(opt: int, canton_lines=None, outputPath: str = "./railSim/railSimulator/static/img/diagrama.png"):
    """
    Generates the train graph. 
    Includes logs to debug why the file might not be updating.
    """
    print(f"--- Starting Diagram Generation at {outputPath} ---")
    
    # 1. Ensure directory exists
    outputDir = os.path.dirname(outputPath)
    if not os.path.exists(outputDir):
        os.makedirs(outputDir, exist_ok=True)
        
    # 2. Get data using the 'Lines' key
    collection = dbl.selectCollection("trainLines", "TFG")
    lines = list(dbl.readCollection(collection))
    
    if not lines:
        print("[WARNING] No lines found in MongoDB. Diagram will not be generated.")
        return

    # 3. Handle file removal with protection
    if os.path.exists(outputPath):
        try:
            os.remove(outputPath)
            print("[INFO] Existing diagram deleted successfully.")
        except Exception as e:
            print(f"[ERROR] Could not delete old diagram (file might be locked): {e}")

    colors = [
        "#E6194B", "#3CB44B", "#FFE119", "#0082C8", "#F58231", "#911EB4",
        "#46F0F0", "#F032E6", "#D2F53C", "#FABEBE", "#008080", "#E6BEFF",
        "#AA6E28", "#800000", "#FFD8B1", "#000075", "#808000", "#A9A9FF",
        "#B10DC9", "#FF7F00", "#1F77B4", "#2CA02C", "#D62728", "#9467BD",
        "#7F7F7F", "#BCBD22", "#17BECF", "#FF69B4", "#40E0D0", "#B22222",
        "#228B22", "#00CED1", "#FF1493", "#C71585", "#A0522D", "#6A5ACD",
        "#20B2AA", "#FFD700", "#8C564B", "#E377C2",
    ]
    
    segments = []
    all_stations = set()

    # 4. Process segments
    for idx, line in enumerate(lines):
        # We look specifically for Timetable_Margins (created in simLibrary)
        margins = line.get("Timetable_Margins")
        stations = line.get("Stations")

        if not margins or not stations:
            print(f"[DEBUG] Line {line.get('Lines')} skipped: Missing margins or stations.")
            continue
        
        color = colors[idx % len(colors)]
        departures = margins[0]
        arrivals = margins[1]
        all_stations.update(stations)

        for i in range(len(departures) - 1):
            segments.append({
                "station_origin": stations[i],
                "station_destiny": stations[i + 1],
                "departure": departures[i],
                "arrival": arrivals[i],
                "color": color
            })

    if not segments:
        print("[WARNING] No segments found to draw. Check if Timetable_Margins are populated.")
        return

    # 5. Drawing
    print(f"[INFO] Drawing {len(segments)} segments...")
    stationlist = sorted(all_stations)
    est_to_x = generateRandomPositions(stationlist)

    plt.figure(figsize=(12, 6))
    ax = plt.gca()
    ax.set_xticks(list(est_to_x.values()))
    ax.set_xticklabels(list(est_to_x.keys()))
    ax.invert_yaxis()
    ax.yaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))

    for seg in segments:
        x0, x1 = est_to_x[seg["station_origin"]], est_to_x[seg["station_destiny"]]
        t0, t1 = seg["departure"], seg["arrival"]
        ax.fill_between([x0, x1], t0, t1, color=seg["color"], alpha=0.6)

    plt.tight_layout()
    plt.savefig(outputPath)
    plt.close('all') # Important to free memory and file handles
    print(f"--- Diagram Successfully Saved ---")