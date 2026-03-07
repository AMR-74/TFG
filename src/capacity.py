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

            if timeZone[0] not in stationsList or timeZone[1] not in stationsList:
                continue

            indexOrg = stationsList.index(timeZone[0])
            indexEnd = stationsList.index(timeZone[1])

            if indexEnd <= indexOrg:
                continue

            # Filtering logic for time and station alignment
            if (
                (
                    (ord(stationsList[-1]) >= ord(timeZone[0]) >= ord(stationsList[0]))
                    or (
                        ord(stationsList[0])
                        <= ord(timeZone[1])
                        <= ord(stationsList[-1])
                    )
                )
                and (ord(stationsList[-1]) > ord(timeZone[0]))
                and (stationsList[0] != timeZone[1])
            ):
                if (
                    ord(stationsList[-1]) >= ord(timeZone[0]) >= ord(stationsList[0])
                ) and (timeZone[2] <= originalTimes[0][indexOrg]):
                    for i in range(0, len(originalTimes[0])):
                        if (
                            ord(timeZone[1])
                            > (ord(stationsList[0]) + i)
                            >= ord(stationsList[0])
                        ):
                            if timeZone[3] >= originalTimes[0][i] >= timeZone[2]:
                                validLinesList.append(lineNumber)
                                break
                elif (ord(stationsList[0]) <= ord(timeZone[0])) and (
                    timeZone[2] <= originalTimes[0][indexOrg]
                ):
                    for i in range(0, len(originalTimes[0])):
                        if (
                            ord(timeZone[1])
                            > (ord(stationsList[0]) + i)
                            >= ord(stationsList[0])
                        ):
                            if timeZone[3] >= originalTimes[0][i] >= timeZone[2]:
                                validLinesList.append(lineNumber)
                                break
                elif ord(timeZone[1]) >= ord(stationsList[0]) >= ord(timeZone[0]):
                    for i in range(0, len(originalTimes[0])):
                        if (
                            ord(timeZone[1])
                            > (ord(stationsList[0]) + i)
                            >= ord(timeZone[0])
                        ):
                            if timeZone[3] >= originalTimes[0][i] >= timeZone[2]:
                                validLinesList.append(lineNumber)
                                break
        return validLinesList


def adjust_and_save(option, difference, lineData, collection, stationsTimes):
    """
    Adjusts arrival/departure times based on the compression difference and saves to DB.
    """
    departuresList = []
    arrivalsList = []

    if option == 1:
        for departure in lineData["Compressed_Timetable"][0]:
            departuresList.append(departure - difference)

        for i, arrival in enumerate(lineData["Compressed_Timetable"][-1]):
            arrivalsList.append(arrival - difference)
            stationsTimes[chr(ord(CAPACITY_PARAMS["stationOrg"]) + i)].append(
                arrival - difference
            )

        dbl.modify_entry(
            collection,
            {"Lines": lineData["Lines"]},
            {"Compressed_Timetable": [departuresList, arrivalsList]},
        )

    elif option == 2:
        for departure in lineData["Compressed_Timetable"][0]:
            departuresList.append(departure - difference)

        for i, arrival in enumerate(lineData["Compressed_Timetable"][-1]):
            arrivalsList.append(arrival - difference)
            stationsTimes[chr(ord(lineData["Stations"][0]) + i)].append(
                arrival - difference
            )

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
                if maxLinesCount == len(sortedLines):
                    firstLine = line
                    refTime = timeZone[2]
                    for t in line["Compressed_Timetable"][0]:
                        if currentTime is None:
                            currentTime = t
                        elif currentTime > t:
                            currentTime = t

                    timeDifference = abs(currentTime - refTime)
                    if ord(line["Stations"][0]) <= ord(CAPACITY_PARAMS["stationOrg"]):
                        adjust_and_save(
                            1, timeDifference, line, collection, stationsData
                        )
                    else:
                        adjust_and_save(
                            2, timeDifference, line, collection, stationsData
                        )
                    refTime, currentTime = None, None
                    maxLinesCount -= 1

                else:
                    # Logic for subsequent lines compression
                    if ord(line["Stations"][0]) <= ord(CAPACITY_PARAMS["stationOrg"]):
                        for i, t in enumerate(line["Compressed_Timetable"][0]):
                            stationKey = chr(ord(CAPACITY_PARAMS["stationOrg"]) + i)
                            if len(stationsData[stationKey]) > 0:
                                if (refTime is None) or (abs(refTime - currentTime)) > (
                                    abs(stationsData[stationKey][-1] - t)
                                ):
                                    refTime = stationsData[stationKey][-1]
                                    currentTime = t
                        timeDifference = abs(currentTime - refTime)
                        adjust_and_save(
                            1, timeDifference, line, collection, stationsData
                        )
                    else:
                        for i, t in enumerate(line["Compressed_Timetable"][0]):
                            stationKey = chr(ord(line["Stations"][0]) + i)
                            if len(stationsData[stationKey]) > 0:
                                if (refTime is None) or (abs(refTime - currentTime)) > (
                                    abs(stationsData[stationKey][-1] - t)
                                ):
                                    refTime = stationsData[stationKey][-1]
                                    currentTime = t
                        timeDifference = abs(currentTime - refTime)
                        adjust_and_save(
                            2, timeDifference, line, collection, stationsData
                        )
                        maxLinesCount -= 1
                    refTime, currentTime = None, None

    # Final adjustment for the first line
    for i, t in enumerate(firstLine["Compressed_Timetable"][0]):
        stationKey = chr(ord(CAPACITY_PARAMS["stationOrg"]) + i)
        if not stationsData[stationKey]:
            continue
        if (refTime is None) or (
            abs(refTime - currentTime) < abs(stationsData[stationKey][-1] - t)
        ):
            refTime = stationsData[stationKey][-1]
            currentTime = t

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
            if ord(stationOrg) >= ord(line["Stations"][0]):
                stationsMap[stationOrg].append([line["Lines"], firstDeparture])
            else:
                for i in range(ord(stationOrg), ord(stationEnd) + 1):
                    if ord(line["Stations"][0]) <= i <= ord(line["Stations"][-1]):
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
        if timeZone[0] not in stationsList or timeZone[1] not in stationsList:
            return

        i0 = stationsList.index(timeZone[0])
        i1 = stationsList.index(timeZone[1])
        if i1 <= i0:
            return

        depSlice = line["Timetable_Margins"][0][i0 : i1 + 1]
        arrSlice = line["Timetable_Margins"][1][i0 : i1 + 1]

        dbl.modify_entry(
            collection,
            {"Lines": lineNumber},
            {"Compressed_Timetable": [depSlice, arrSlice]},
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
