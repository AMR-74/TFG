import src.dbLibrary as dbl
import src.simLibrary as simlb
from datetime import timedelta, datetime

#=== GLOBAL PARAMETERS ===#
capacityParams = {
    "stationOrg": "A",
    "stationEnd": "B",
    "startHour": "00:00",
    "endHour": "00:00",
    "extraTime": timedelta(minutes=30)
}

#=== FUNCTIONS ===#
def selectTimeZone(stationOrg: str, stationEnd: str, earlyHour: str, endHour: str) -> tuple:
    """
    Validates time format and station range, returning a tuple with formatted data.
    """
    formatHour = "%H:%M"
    formatReference = r"^(?:[01]\d|2[0-3]):[0-5]\d$"

    if simlb.checkFormat(formatReference, earlyHour) == True:
        start = simlb.hourFormat(earlyHour, formatHour)
    else:
        raise ValueError("Error in the provided hour format.")
    
    if simlb.checkFormat(formatReference, endHour) == True:
        end = simlb.hourFormat(endHour, formatHour)
    else:
        raise ValueError("Error in the provided hour format.")
    
    if 65 <= ord(stationOrg) <= 90 and 65 <= ord(stationEnd) <= 90:
        return (stationOrg, stationEnd, start, end)
    else:
        raise ValueError("Stations out of permitted range.")
    
def identifyLineTimes(opt:int, timeZone:tuple):
    """
    Identifies train lines operating within the selected timeframe.
    """
    collection = dbl.selectCollection("trainLines", "TFG")
    lines = dbl.readCollection(collection)
       
    if opt == 2:
        lineasVal = []
        for line in lines:
            timesOriginal = line["Timetable_Margins"]
            nLine = line["Lines"] # Key updated to Lines
            stations = line["Stations"]

            if timeZone[0] not in stations or timeZone[1] not in stations:
                continue

            indx_org = stations.index(timeZone[0])
            indx_end = stations.index(timeZone[1])

            if indx_end <= indx_org:
                continue

            # Filtering logic for time and station alignment
            if ((ord(stations[-1]) >= ord(timeZone[0]) >= ord(stations[0])) or (ord(stations[0]) <= ord(timeZone[1]) <= ord(stations[-1]))) and (ord(stations[-1]) > ord(timeZone[0])) and (stations[0] != timeZone[1]):
                if ((ord(stations[-1]) >= ord(timeZone[0]) >= ord(stations[0])) and (timeZone[2] <= timesOriginal[0][indx_org])):
                    for i in range(0, len(timesOriginal[0])):
                        if (ord(timeZone[1]) > (ord(stations[0]) + i) >= ord(stations[0])):
                            if (timeZone[3] >= timesOriginal[0][i] >= timeZone[2]):
                                lineasVal.append(nLine)
                                break
                elif ((ord(stations[0]) <= ord(timeZone[0])) and (timeZone[2] <= timesOriginal[0][indx_org])):
                    for i in range(0, len(timesOriginal[0])):
                        if (ord(timeZone[1]) > (ord(stations[0]) + i) >= ord(stations[0])):
                            if (timeZone[3] >= timesOriginal[0][i] >= timeZone[2]):
                                lineasVal.append(nLine)
                                break
                elif (ord(timeZone[1]) >= ord(stations[0]) >= ord(timeZone[0])):
                    for i in range(0, len(timesOriginal[0])):
                        if (ord(timeZone[1]) > (ord(stations[0]) + i) >= ord(timeZone[0])):
                            if (timeZone[3] >= timesOriginal[0][i] >= timeZone[2]):
                                lineasVal.append(nLine)
                                break
        return lineasVal

def adjustAndSave(opt:int, difference, line, collection, stationsTimes:dict) -> None:
    """
    Adjusts arrival/departure times based on the compression difference and saves to DB.
    """
    departures = []
    arrivals = []

    if opt == 1:
        for departure in line["Compressed_Timetable"][0]:
            departures.append(departure-difference)

        for i, arrival in enumerate(line["Compressed_Timetable"][-1]):
            arrivals.append(arrival - difference)
            stationsTimes[chr(ord(capacityParams["stationOrg"]) + i)].append(arrival - difference)

        dbl.modifyEntry(collection,
                            {"Lines": line["Lines"]},
                            {"Compressed_Timetable": [departures, arrivals]})
        
    elif opt == 2:
        for departure in line["Compressed_Timetable"][0]:
            departures.append(departure-difference)

        for i, arrival in enumerate(line["Compressed_Timetable"][-1]):
            arrivals.append(arrival - difference)
            stationsTimes[chr(ord(line["Stations"][0]) + i)].append(arrival - difference)

        dbl.modifyEntry(collection,
                            {"Lines": line["Lines"]},
                            {"Compressed_Timetable": [departures, arrivals]})
        
    elif opt == 3:
        for departure in line["Compressed_Timetable"][0]:
            departures.append(departure + difference)

        for i, arrival in enumerate(line["Compressed_Timetable"][-1]):
            arrivals.append(arrival + difference)

def compressLines(sortedLines:list, timeZone:tuple) -> dict:
    """
    Compresses valid lines sequentially according to the UIC Leaflet 406 methodology.
    """
    firstLine = None
    maxLines = len(sortedLines)
    tref = None
    tact = None
    stations = {chr(i): [] for i in range(ord(capacityParams["stationOrg"]), ord(capacityParams["stationEnd"]) + 1)}   

    for sLine in sortedLines:
        collection = dbl.selectCollection("trainLines", "TFG")
        lines = dbl.readCollection(collection)
        
        for line in lines:
            if line["Lines"] == sLine:
                if maxLines == len(sortedLines):
                    firstLine = line
                    tref = timeZone[2]
                    for time in line["Compressed_Timetable"][0]:
                        if tact == None: tact = time
                        elif tact > time: tact = time

                    difference = abs(tact - tref)
                    if ord(line["Stations"][0]) <= ord(capacityParams["stationOrg"]):
                        adjustAndSave(1, difference, line, collection, stations)
                    else:
                        adjustAndSave(2, difference, line, collection, stations)
                    tref, tact = None, None
                    maxLines -= 1

                else:
                    # Logic for subsequent lines compression
                    if ord(line["Stations"][0]) <= ord(capacityParams["stationOrg"]):
                        for i, time in enumerate(line["Compressed_Timetable"][0]):
                            if len(stations[chr(ord(capacityParams["stationOrg"]) + i)]) > 0:
                                if (tref == None) or (abs(tref - tact)) > (abs(stations[chr(ord(capacityParams["stationOrg"]) + i)][-1] - time)):
                                    tref = stations[chr(ord(capacityParams["stationOrg"]) + i)][-1]
                                    tact = time
                        difference = abs(tact - tref)
                        adjustAndSave(1, difference, line, collection, stations)
                    else:
                        for i, time in enumerate(line["Compressed_Timetable"][0]):
                            if len(stations[chr(ord(line["Stations"][0]) + i)]) > 0:
                                if (tref == None) or (abs(tref - tact)) > (abs(stations[chr(ord(line["Stations"][0]) + i)][-1] - time)):
                                    tref = stations[chr(ord(line["Stations"][0]) + i)][-1]
                                    tact = time
                        difference = abs(tact - tref)
                        adjustAndSave(2, difference, line, collection, stations)
                        maxLines -= 1
                    tref, tact = None, None

    # Final adjustment for the first line
    for i, time in enumerate(firstLine["Compressed_Timetable"][0]):
        k = chr(ord(capacityParams["stationOrg"]) + i)
        if not stations[k]: continue
        if (tref is None) or (abs(tref - tact) < abs(stations[k][-1] - time)):
            tref = stations[k][-1]
            tact = time

    difference = abs(tact-tref)
    adjustAndSave(3, difference, firstLine, collection, stations)
    return stations

def capacityCalculator(stationTimes:dict, extraTime:timedelta, timeZone:tuple) -> float:
    """
    Calculates the final capacity percentage.
    """
    maxArrivalTime = None
    for station in stationTimes:
        if len(stationTimes[station]) > 0:
            if (maxArrivalTime == None) or stationTimes[station][-1] > maxArrivalTime:
                maxArrivalTime = stationTimes[station][-1]

    if (abs(maxArrivalTime - timeZone[2]) + extraTime) >= abs(timeZone[2] - timeZone[3]):
        capacity = float(100)
    else:
        capacity = float((abs(timeZone[2] - maxArrivalTime) + extraTime)/(abs(timeZone[2] - timeZone[3]))) * 100
    return capacity

def sortStations(validLines:list, stationOrg:str, stationEnd:str) -> list:
    """
    Sorts lines to determine the compression sequence.
    """
    collection = dbl.selectCollection("trainLines", "TFG")
    lines = dbl.readCollection(collection)
    stations = {chr(i): [] for i in range(ord(stationOrg), ord(stationEnd) + 1)}
    allEntries = []

    for line in lines:
        ct = line.get("Compressed_Timetable")
        if not ct or len(ct) < 1 or not ct[0]: continue
        first_departure = ct[0][0]

        if line["Lines"] in validLines:
            if ord(stationOrg) >= ord(line["Stations"][0]):
                stations[stationOrg].append([line["Lines"], first_departure])
            else:
                for i in range(ord(stationOrg), ord(stationEnd) + 1):
                    if ord(line["Stations"][0]) <= i <= ord(line["Stations"][-1]):
                        stations[chr(i)].append([line["Lines"], first_departure])
                        break 
    
    for station in stations:
        for item in stations[station]:
            allEntries.append(item)
    sortedData = sorted(allEntries, key=lambda x: x[1])
    return [indexLine[0] for indexLine in sortedData]

def saveLine(numberLine:int, timeZone:tuple):
    """
    Saves the specific slice of the timetable for the compression process.
    """
    collection = dbl.selectCollection("trainLines", "TFG")
    lines = dbl.readCollection(collection)

    for line in lines:
        if line["Lines"] != numberLine: continue
        stations = line["Stations"]
        if timeZone[0] not in stations or timeZone[1] not in stations: return

        i0 = stations.index(timeZone[0])
        i1 = stations.index(timeZone[1])
        if i1 <= i0: return

        dep = line["Timetable_Margins"][0][i0:i1+1]
        arr = line["Timetable_Margins"][1][i0:i1+1]

        dbl.modifyEntry(collection, {"Lines": numberLine}, {"Compressed_Timetable": [dep, arr]})

def generateSelectedtt(stationOrg, stationEnd, startHour, endHour):
    """
    Main execution flow for capacity analysis.
    Recibe los datos desde la vista, actualiza los parámetros y calcula.
    """
    # 1. Actualizamos los parámetros globales con lo que viene del formulario
    capacityParams["stationOrg"] = stationOrg
    capacityParams["stationEnd"] = stationEnd
    capacityParams["startHour"] = startHour
    capacityParams["endHour"] = endHour

    # 2. Validamos (selectTimeZone lanzará ValueError si el formato es malo)
    timeZone = selectTimeZone(stationOrg, stationEnd, startHour, endHour)
    
    # 3. Ejecutamos la lógica
    linesVal = identifyLineTimes(2, timeZone)

    # Si no hay líneas en ese rango, evitamos errores posteriores
    if not linesVal:
        raise ValueError("No se encontraron líneas en ese rango horario/estaciones.")

    for lineIndex in linesVal:
        saveLine(lineIndex, timeZone)

    sortedLines = sortStations(linesVal, stationOrg, stationEnd)
    stationsC = compressLines(sortedLines, timeZone)
    
    return round(capacityCalculator(stationsC, capacityParams["extraTime"], timeZone), 2)