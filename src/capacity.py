import src.dbLibrary as dbl
import src.simLibrary as simlb
from datetime import timedelta, datetime

# === GLOBAL CONSTANTS === #
CAPACITY_PARAMS = {
    "stationOrg": "A",
    "stationEnd": "B",
    "startHour": "00:00",
    "endHour": "00:00",
    "extraTime": timedelta(minutes=30),
}


# === FUNCTIONS === #


def select_time_zone(stationOrg, stationEnd, earlyHour, endHour):
    """
    Validates time format and station range, returning a tuple with formatted data.
    """
    formatHour = "%H:%M"
    formatReference = r"^(?:[01]\d|2[0-3]):[0-5]\d$"

    if simlb.check_format(formatReference, earlyHour):
        startTime = simlb.hour_format(earlyHour, formatHour)
    else:
        raise ValueError("Error in the provided hour format.")

    if simlb.check_format(formatReference, endHour):
        endTime = simlb.hour_format(endHour, formatHour)
    else:
        raise ValueError("Error in the provided hour format.")

    if 65 <= ord(stationOrg) <= 90 and 65 <= ord(stationEnd) <= 90:
        return (stationOrg, stationEnd, startTime, endTime)
    else:
        raise ValueError("Stations out of permitted range.")


def identify_line_times(option, timeZone):
    """
    Identifies train lines operating within the selected timeframe.
    """
    collection = dbl.select_collection("trainLines", "TFG")
    linesData = dbl.read_collection(collection)

    if option == 2:
        validLinesList = []
        for line in linesData:
            originalTimes = line["Timetable_Margins"]
            lineNumber = line["Lines"]
            stationsList = line["Stations"]

            # Filter stations that belong strictly to the requested timeZone
            validStations = [s for s in stationsList if timeZone[0] <= s <= timeZone[1]]
            
            # If the train has less than 2 stations in this zone, there is no route segment
            if len(validStations) < 2:
                continue

            i0 = stationsList.index(validStations[0])
            i1 = stationsList.index(validStations[-1])

            valid = False
            for i in range(i0, i1):
                if timeZone[2] <= originalTimes[0][i] < timeZone[3]:
                    valid = True
                    break

            if valid:
                validLinesList.append(lineNumber)
                
        return validLinesList


def adjust_and_save(option, difference, lineData, collection, stationsTimes):
    """
    Adjusts arrival/departure times based on the compression difference and saves to DB.
    """
    departuresList = []
    arrivalsList = []
    
    compStations = lineData.get("Compressed_Stations", lineData["Stations"])

    if option == 1 or option == 2:
        for departure in lineData["Compressed_Timetable"][0]:
            departuresList.append(departure - difference)

        for i, arrival in enumerate(lineData["Compressed_Timetable"][-1]):
            arrivalsList.append(arrival - difference)
            
            station_key = compStations[i + 1]
            if station_key in stationsTimes:
                stationsTimes[station_key].append(arrival - difference)

        dbl.modify_entry(
            collection,
            {"Lines": lineData["Lines"]},
            {"Compressed_Timetable": [departuresList, arrivalsList]},
        )

    elif option == 3:
        for departure in lineData["Compressed_Timetable"][0]:
            departuresList.append(departure + difference)

        for i, arrival in enumerate(lineData["Compressed_Timetable"][-1]):
            arrivalsList.append(arrival + difference)
            
            station_key = compStations[i + 1]
            if station_key in stationsTimes:
                stationsTimes[station_key].append(arrival + difference)


def compress_lines(sortedLines, timeZone):
    """
    Compresses valid lines sequentially according to the UIC Leaflet 406 methodology.
    """
    firstLine = None
    maxLinesCount = len(sortedLines)
    refTime = None
    currentTime = None
    stationsData = {
        chr(i): []
        for i in range(
            ord(CAPACITY_PARAMS["stationOrg"]), ord(CAPACITY_PARAMS["stationEnd"]) + 1
        )
    }

    for sLine in sortedLines:
        collection = dbl.select_collection("trainLines", "TFG")
        allLines = dbl.read_collection(collection)

        for line in allLines:
            if line["Lines"] == sLine:
                compStations = line.get("Compressed_Stations", line["Stations"])
                
                if maxLinesCount == len(sortedLines):
                    firstLine = line
                    refTime = timeZone[2]
                    for t in line["Compressed_Timetable"][0]:
                        if currentTime is None or currentTime > t:
                            currentTime = t

                    timeDifference = abs(currentTime - refTime)
                    if ord(compStations[0]) <= ord(CAPACITY_PARAMS["stationOrg"]):
                        adjust_and_save(1, timeDifference, line, collection, stationsData)
                    else:
                        adjust_and_save(2, timeDifference, line, collection, stationsData)
                    refTime, currentTime = None, None
                    maxLinesCount -= 1

                else:
                    if ord(compStations[0]) <= ord(CAPACITY_PARAMS["stationOrg"]):
                        for i, t in enumerate(line["Compressed_Timetable"][0]):
                            stationKey = compStations[i]
                            if stationKey in stationsData and len(stationsData[stationKey]) > 0:
                                if (refTime is None) or (abs(refTime - currentTime)) > (abs(stationsData[stationKey][-1] - t)):
                                    refTime = stationsData[stationKey][-1]
                                    currentTime = t
                        
                        if refTime is None:
                            refTime = timeZone[2]
                            for t in line["Compressed_Timetable"][0]:
                                if currentTime is None or currentTime > t:
                                    currentTime = t

                        timeDifference = abs(currentTime - refTime)
                        adjust_and_save(1, timeDifference, line, collection, stationsData)
                    else:
                        for i, t in enumerate(line["Compressed_Timetable"][0]):
                            stationKey = compStations[i]
                            if stationKey in stationsData and len(stationsData[stationKey]) > 0:
                                if (refTime is None) or (abs(refTime - currentTime)) > (abs(stationsData[stationKey][-1] - t)):
                                    refTime = stationsData[stationKey][-1]
                                    currentTime = t
                                    
                        if refTime is None:
                            refTime = timeZone[2]
                            for t in line["Compressed_Timetable"][0]:
                                if currentTime is None or currentTime > t:
                                    currentTime = t
                        
                        timeDifference = abs(currentTime - refTime)
                        adjust_and_save(2, timeDifference, line, collection, stationsData)
                        maxLinesCount -= 1
                    refTime, currentTime = None, None

    compStations = firstLine.get("Compressed_Stations", firstLine["Stations"])
    for i, t in enumerate(firstLine["Compressed_Timetable"][0]):
        stationKey = compStations[i]
        if stationKey not in stationsData or not stationsData[stationKey]:
            continue
        if (refTime is None) or (abs(refTime - currentTime) < abs(stationsData[stationKey][-1] - t)):
            refTime = stationsData[stationKey][-1]
            currentTime = t

    if refTime is None:
        timeDifference = timedelta(minutes=0)
    else:
        timeDifference = abs(currentTime - refTime)
    
    adjust_and_save(3, timeDifference, firstLine, collection, stationsData)
    return stationsData


def capacity_calculator(stationTimes, extraTime, timeZone):
    """
    Calculates the final capacity percentage.
    """
    maxArrivalTime = None
    for station in stationTimes:
        if len(stationTimes[station]) > 0:
            if (maxArrivalTime is None) or stationTimes[station][-1] > maxArrivalTime:
                maxArrivalTime = stationTimes[station][-1]

    if (abs(maxArrivalTime - timeZone[2]) + extraTime) >= abs(
        timeZone[2] - timeZone[3]
    ):
        capacityResult = float(100)
    else:
        capacityResult = (
            float(
                (abs(timeZone[2] - maxArrivalTime) + extraTime)
                / (abs(timeZone[2] - timeZone[3]))
            )
            * 100
        )
    return capacityResult


def sort_stations(validLines, stationOrg, stationEnd):
    """
    Sorts lines to determine the compression sequence.
    """
    collection = dbl.select_collection("trainLines", "TFG")
    linesData = dbl.read_collection(collection)
    stationsMap = {chr(i): [] for i in range(ord(stationOrg), ord(stationEnd) + 1)}
    allEntriesList = []

    for line in linesData:
        ct = line.get("Compressed_Timetable")
        if not ct or len(ct) < 1 or not ct[0]:
            continue
        firstDeparture = ct[0][0]

        if line["Lines"] in validLines:
            compStations = line.get("Compressed_Stations", line["Stations"])
            if ord(stationOrg) >= ord(compStations[0]):
                stationsMap[stationOrg].append([line["Lines"], firstDeparture])
            else:
                for i in range(ord(stationOrg), ord(stationEnd) + 1):
                    if ord(compStations[0]) <= i <= ord(compStations[-1]):
                        stationsMap[chr(i)].append([line["Lines"], firstDeparture])
                        break

    for station in stationsMap:
        for item in stationsMap[station]:
            allEntriesList.append(item)
    sortedData = sorted(allEntriesList, key=lambda x: x[1])
    return [indexLine[0] for indexLine in sortedData]


def save_line(lineNumber, timeZone):
    """
    Saves the specific slice of the timetable for the compression process.
    """
    collection = dbl.select_collection("trainLines", "TFG")
    linesData = dbl.read_collection(collection)

    for line in linesData:
        if line["Lines"] != lineNumber:
            continue
            
        stationsList = line["Stations"]
        
        validStations = [s for s in stationsList if timeZone[0] <= s <= timeZone[1]]
        
        if len(validStations) < 2:
            return

        i0 = stationsList.index(validStations[0])
        i1 = stationsList.index(validStations[-1])

        depSlice = line["Timetable_Margins"][0][i0 : i1]
        arrSlice = line["Timetable_Margins"][1][i0 : i1]
        
        compStations = stationsList[i0 : i1 + 1]

        dbl.modify_entry(
            collection,
            {"Lines": lineNumber},
            {
                "Compressed_Timetable": [depSlice, arrSlice],
                "Compressed_Stations": compStations
            },
        )


def generate_selected_tt(stationOrg, stationEnd, startHour, endHour):
    """
    Main execution flow for capacity analysis.
    Updates global parameters with view data and executes the calculation logic.
    """
    # 1. Update global constants with form data
    CAPACITY_PARAMS["stationOrg"] = stationOrg
    CAPACITY_PARAMS["stationEnd"] = stationEnd
    CAPACITY_PARAMS["startHour"] = startHour
    CAPACITY_PARAMS["endHour"] = endHour

    # 2. Validation
    timeZone = select_time_zone(stationOrg, stationEnd, startHour, endHour)

    # 3. Execution logic
    linesVal = identify_line_times(2, timeZone)

    # If no lines are found in range, avoid subsequent errors
    if not linesVal:
        raise ValueError("No lines found within the specified time range or stations.")

    for lineIndex in linesVal:
        save_line(lineIndex, timeZone)

    sortedLines = sort_stations(linesVal, stationOrg, stationEnd)
    stationsCompressed = compress_lines(sortedLines, timeZone)

    return round(
        capacity_calculator(stationsCompressed, CAPACITY_PARAMS["extraTime"], timeZone),
        2,
    )
