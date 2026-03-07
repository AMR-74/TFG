import random as ran
import src.dbLibrary as dbl
import src.generateDiagram as gd
import re
import os
from datetime import timedelta, datetime

# === GLOBAL CONSTANTS ===#
# Global configuration dictionary for simulation settings
PARAMETERS = {
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
    "maxIterations": 500000,
    "lineOffset": 10,
    "minStations": 4,
}

# Initialize seed
ran.seed(ran.randint(1, 300))

# === FUNCTIONS ===#


def change_seed():
    """
    Resets the random seed for variation in simulations.
    """
    ran.seed(ran.randint(1, 500))


def check_format(formatReference, name):
    """
    Validates if a string matches the provided regex format.
    """
    return bool(re.match(formatReference, name))


def visual_hour_format(hour):
    """
    Converts a datetime object to a string for the Django template.
    """
    return hour.strftime(PARAMETERS["formatHour"])


def hour_format(hour, formatHour):
    """
    Parses a time string into a datetime object.
    """
    return datetime.strptime(hour, formatHour)


def generate_trip(n):
    """
    Generates an origin-destination tuple (e.g., 'A' to 'E').
    """
    startChar = 65  # 'A'
    if 0 < n <= 26:
        endChar = 65 + n - 1
        return (chr(startChar), chr(endChar))
    raise ValueError("Exceeds maximum allowed stations.")


def generate_lines(route, minStationsPerLine):
    """
    Generates random train lines and inserts them into the database.
    """
    stationsList = [chr(i) for i in range(ord(route[0]), ord(route[1]) + 1)]
    possibleLines = []
    for i in range(len(stationsList)):
        for j in range(i + minStationsPerLine, len(stationsList)):
            possibleLines.append((stationsList[i], stationsList[j]))

    if not possibleLines:
        return

    generatedLines = [ran.choice(possibleLines) for _ in range(PARAMETERS["nLines"])]
    for idx, line in enumerate(generatedLines):
        listStations = [chr(s) for s in range(ord(line[0]), ord(line[1]) + 1)]
        # We use the updated dbInputsTL which expects 'Lines'
        dbl.db_inputs_tl(idx + 1, listStations, [], [], "TFG", [], [])


def set_time_limit(formatRef):
    """
    Validates and returns the simulation time window boundaries.
    """
    startTime = hour_format(PARAMETERS["upperTimeLimit"], PARAMETERS["formatHour"])
    endTime = hour_format(PARAMETERS["lowerTimeLimit"], PARAMETERS["formatHour"])
    return (startTime, endTime)


def margins_timetable(option, times):
    """
    Applies security margins to schedule times.
    """
    if not times:
        return []
    secMargin = timedelta(minutes=PARAMETERS["securityMargin"])
    if option == 1:
        return [times[0]] + [t - secMargin for t in times[1:]]
    elif option == 2:
        return [t + secMargin for t in times]


def conflict_detection(station, newDep, newArr, margin, ocuStations):
    """
    Checks for track occupancy conflicts at a specific station.
    """
    newStart = newDep - margin
    newEnd = newArr + margin
    for start, end in ocuStations.get(station, []):
        if newStart < end and newEnd > start:
            return True
    return False


def generate_timetable(limits, trip):
    """
    Generates a collision-free timetable and triggers diagram generation.
    """
    print("--- Starting Timetable Generation ---")
    collection = dbl.select_collection("trainLines", "TFG")
    linesData = dbl.select_data(collection, "Lines")
    stationsData = dbl.select_data(collection, "Stations")

    if not linesData:
        print("[ERROR] No lines found. Did you run generate_lines?")
        return

    usedLines = linesData.copy()
    validLines = []
    ocuStations = {chr(i): [] for i in range(ord(trip[0]), ord(trip[1]) + 1)}
    securityMargin = timedelta(minutes=PARAMETERS["securityMargin"])

    while usedLines:
        currentLine = ran.choice(usedLines)
        lineIdx = linesData.index(currentLine)
        currentStations = stationsData[lineIdx]
        iterations = 0
        validLine = False

        while not validLine:
            if iterations > PARAMETERS["maxIterations"]:
                print(f"[FATAL] Max iterations reached for line {currentLine}")
                return

            startTime = limits[0] + timedelta(
                minutes=(len(validLines) + iterations) * PARAMETERS["lineOffset"]
            )
            departureTimes, arrivalTimes = [], []
            hasConflicts = False

            for i, st in enumerate(currentStations):
                duration = timedelta(
                    minutes=ran.randint(
                        PARAMETERS["lowerMinuteMargin"],
                        PARAMETERS["higherMinuteMargin"],
                    )
                )
                dep = startTime if i == 0 else arrivalTimes[-1]
                arr = dep + duration

                if arr > limits[1] or conflict_detection(
                    st, dep, arr, securityMargin, ocuStations
                ):
                    hasConflicts = True
                    break
                departureTimes.append(dep)
                arrivalTimes.append(arr)

            if not hasConflicts:
                for i, st in enumerate(currentStations):
                    ocuStations[st].append(
                        (
                            departureTimes[i] - securityMargin,
                            arrivalTimes[i] + securityMargin,
                        )
                    )
                validLine = True
            else:
                iterations += 1

        # Update MongoDB with 'Lines' key
        dbl.modify_entry(
            collection,
            {"Lines": currentLine},
            {"Timetable": [departureTimes, arrivalTimes]},
        )
        dbl.modify_entry(
            collection,
            {"Lines": currentLine},
            {
                "Timetable_Margins": [
                    margins_timetable(1, departureTimes),
                    margins_timetable(2, arrivalTimes),
                ]
            },
        )

        usedLines.remove(currentLine)
        validLines.append(currentLine)

    print("[SUCCESS] Timetable finished. Generating diagram...")
    gd.generate_diagram(1, [])
