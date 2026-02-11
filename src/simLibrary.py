import random as ran
import src.dbLibrary as dbl
import src.generateDiagram as gd
import re
import os
from datetime import timedelta, datetime

#=== GLOBAL VARIABLES ===#
# This dictionary must exist for views.py to store simulation settings
parameters = {
    "format": r"^(?:[01]\d|2[0-3]):[0-5]\d$",
    "formatHour": "%H:%M",
    "trip": 5,
    "upperTimeLimit": "09:00",
    "lowerTimeLimit": "21:00",
    "nLines": 5,
    "hourMargin": 0,
    "lowerMinuteMargin": 10,
    "higherMinuteMargin": 20,
    "securityMargin": 5,
    "MaxIterations": 500000,
    "lineOffset": 10,
    "minStations": 4
}

# Initialize seed
ran.seed(ran.randint(1, 300))

#=== FUNCTIONS ===#

def changeSeed():
    """Resets the random seed for variation in simulations."""
    ran.seed(ran.randint(1, 500))

def checkFormat(formatReference, name):
    """Validates if a string matches the provided regex format."""
    return bool(re.match(formatReference, name))

def visualHourFormat(hour):
    """Converts a datetime object to a string for the Django template."""
    return hour.strftime(parameters["formatHour"])

def hourFormat(hour, formatHour):
    """Parses a time string into a datetime object."""
    return datetime.strptime(hour, formatHour)

def generateTrip(n):
    """Generates an origin-destination tuple (e.g., 'A' to 'E')."""
    start = 65  # 'A'
    if 0 < n <= 26:
        end = 65 + n - 1
        return (chr(start), chr(end))
    raise ValueError("Exceeds maximum allowed stations.")

def generateLines(route, min_stations_per_line):
    """Generates random train lines and inserts them into the database."""
    stations_list = [chr(i) for i in range(ord(route[0]), ord(route[1]) + 1)]
    possible_lines = []
    for i in range(len(stations_list)):
        for j in range(i + min_stations_per_line, len(stations_list)):
            possible_lines.append((stations_list[i], stations_list[j]))

    if not possible_lines:
        return

    generated = [ran.choice(possible_lines) for _ in range(parameters["nLines"])]
    for idx, line in enumerate(generated):
        list_stations = [chr(s) for s in range(ord(line[0]), ord(line[1]) + 1)]
        # We use the updated dbInputsTL which expects 'Lines'
        dbl.dbInputsTL(idx + 1, list_stations, [], [], 'TFG', [], [])

def setTimeLimit(format_ref):
    """Validates and returns the simulation time window boundaries."""
    start = hourFormat(parameters["upperTimeLimit"], parameters["formatHour"])
    end = hourFormat(parameters["lowerTimeLimit"], parameters["formatHour"])
    return (start, end)

def marginsTimetable(opt: int, times: list) -> list:
    """Applies security margins to schedule times."""
    if not times:
        return []
    sec_margin = timedelta(minutes=parameters["securityMargin"])
    if opt == 1:
        return [times[0]] + [t - sec_margin for t in times[1:]]
    elif opt == 2:
        return [t + sec_margin for t in times]

def conflictDetection(station, new_dep, new_arr, margin, ocu_stations):
    """Checks for track occupancy conflicts at a specific station."""
    new_start = new_dep - margin
    new_end = new_arr + margin
    for start, end in ocu_stations.get(station, []):
        if new_start < end and new_end > start:
            return True
    return False

def generateTimetable(limits: tuple, trip: tuple):
    """Generates a collision-free timetable and triggers diagram generation."""
    print("--- Starting Timetable Generation ---")
    collection = dbl.selectCollection("trainLines", 'TFG')
    lines = dbl.selectData(collection, "Lines")
    stations = dbl.selectData(collection, "Stations")
    
    if not lines:
        print("[ERROR] No lines found. Did you run generateLines?")
        return

    used_lines = lines.copy()
    valid_lines = []
    ocu_stations = {chr(i): [] for i in range(ord(trip[0]), ord(trip[1]) + 1)}
    security_margin = timedelta(minutes=parameters["securityMargin"])

    while used_lines:
        current_line = ran.choice(used_lines)
        line_idx = lines.index(current_line)
        current_stations = stations[line_idx]
        iterations = 0
        valid_line = False

        while not valid_line:
            if iterations > parameters["MaxIterations"]:
                print(f"[FATAL] Max iterations reached for line {current_line}")
                return

            start_time = limits[0] + timedelta(minutes=(len(valid_lines) + iterations) * parameters["lineOffset"])
            departure_times, arrival_times = [], []
            conflicts = False

            for i, st in enumerate(current_stations):
                duration = timedelta(minutes=ran.randint(parameters["lowerMinuteMargin"], parameters["higherMinuteMargin"]))
                dep = start_time if i == 0 else arrival_times[-1]
                arr = dep + duration

                if arr > limits[1] or conflictDetection(st, dep, arr, security_margin, ocu_stations):
                    conflicts = True
                    break
                departure_times.append(dep)
                arrival_times.append(arr)

            if not conflicts:
                for i, st in enumerate(current_stations):
                    ocu_stations[st].append((departure_times[i] - security_margin, arrival_times[i] + security_margin))
                valid_line = True
            else:
                iterations += 1

        # Update MongoDB with 'Lines' key
        dbl.modifyEntry(collection, {"Lines": current_line}, {"Timetable": [departure_times, arrival_times]})
        dbl.modifyEntry(collection, {"Lines": current_line}, {
            "Timetable_Margins": [marginsTimetable(1, departure_times), marginsTimetable(2, arrival_times)]
        })

        used_lines.remove(current_line)
        valid_lines.append(current_line)

    print("[SUCCESS] Timetable finished. Generating diagram...")
    gd.generateDiagram(1, [])