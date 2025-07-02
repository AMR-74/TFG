import src.dbLibrary as dbl
import src.simLibrary as simlb
from datetime import timedelta, datetime

#=== GLOBAL PARAMETERS ===#
capacityParams = {
    "stationOrg": "B",
    "stationEnd": "H",
    "startHour": "07:00",
    "endHour": "09:30",
    "extraTime": timedelta(minutes=30)
}

#=== FUNCTIONS ===#
def selectTimeZone(stationOrg: str, stationEnd: str, earlyHour: str, endHour: str) -> tuple:
    formatHour = "%H:%M"
    formatReference = r"^(?:[01]\d|2[0-3]):[0-5]\d$"

    if simlb.checkFormat(formatReference, earlyHour) == True:
        start = simlb.hourFormat(earlyHour, formatHour)

    else:
        raise ValueError("Error en el formato de hora introducido.")
    
    if simlb.checkFormat(formatReference, endHour) == True:
        end = simlb.hourFormat(endHour, formatHour)

    else:
        raise ValueError("Error en el formato de hora introducido.")
    
    if 65 <= ord(stationOrg) <= 90 and 65 <= ord(stationEnd) <= 90:
        return (stationOrg, stationEnd, start, end)
    
    else:
        raise ValueError("Estaciones fuera del rángo permitido.")
    
def identifyLineTimes(opt:int, timeZone:tuple):
    collection = dbl.selectCollection("trainLines", "TFG")
    lines = dbl.readCollection(collection)
       
    if opt == 2:
        lineasVal = []
        for line in lines:
            timesOriginal = line["Timetable_Margins"]
            nLine = line["Linea"]
            stations = line["Stations"]

            if ((ord(stations[1]) >= ord(timeZone[0]) >= ord(stations[0])) or (ord(stations[0]) <= ord(timeZone[1]) <= ord(stations[1]))) and (ord(stations[1]) > ord(timeZone[0])) and (stations[0] != timeZone[1]):
                if ((ord(stations[1]) >= ord(timeZone[0]) >= ord(stations[0])) and (timeZone[2] <= timesOriginal[0][(ord(timeZone[0]) - ord(stations[0]))])):
                    for i in range(0, (ord(stations[1]) - ord(stations[0]))):
                        if (ord(timeZone[1]) > (ord(stations[0]) + i) >= ord(stations[0])):
                            if (timeZone[3] >= timesOriginal[0][i] >= timeZone[2]):
                                lineasVal.append(nLine)
                                break
                
                elif ((ord(stations[0]) <= ord(timeZone[0])) and (timeZone[2] <= timesOriginal[0][(ord(timeZone[0]) - ord(stations[0]))])):
                    for i in range(0, (ord(stations[1]) - ord(stations[0]))):
                        if (ord(timeZone[1]) > (ord(stations[0]) + i) >= ord(stations[0])):
                            if (timeZone[3] >= timesOriginal[0][i] >= timeZone[2]):
                                lineasVal.append(nLine)
                                break

                elif (ord(timeZone[1]) >= ord(stations[0]) >= ord(timeZone[0])):
                    for i in range(0, (ord(stations[1]) - ord(stations[0]))):
                        if (ord(timeZone[1]) > (ord(stations[0]) + i) >= ord(timeZone[0])):
                            if (timeZone[3] >= timesOriginal[0][i] >= timeZone[2]):
                                lineasVal.append(nLine)
                                break
                
                else:
                    pass

        
        return lineasVal

def adjustAndSave(opt:int, difference:timedelta, line, collection, stationsTimes:dict) -> None:
    """
    This function adjust the times for the compressed ones.

    Parameters:
    opt(int): Option to save it is possible to choose between 2 different ones.
    difference(timedelta): The absolute time that represent the leat distance between two lines
    line: Line in MongoDB
    collection: Collection in MongoDB
    stationTimes(dict): Dictionary to save arrival times for compression.

    Returns:
    None
    """

    departures = []
    arrivals = []

    if opt == 1:
        for departure in line["Compressed_Timetable"][0]:
            departures.append(departure-difference)

        for i, arrival in enumerate(line["Compressed_Timetable"][1]):
            arrivals.append(arrival - difference)
            stationsTimes[chr(ord(capacityParams["stationOrg"]) + i)].append(arrival - difference)

        dbl.modifyEntry(collection,
                            {"Linea": line["Linea"]},
                            {"Compressed_Timetable": [departures, arrivals]})
        
    elif opt == 2:
        for departure in line["Compressed_Timetable"][0]:
            departures.append(departure-difference)

        for i, arrival in enumerate(line["Compressed_Timetable"][1]):
            arrivals.append(arrival - difference)
            stationsTimes[chr(ord(line["Stations"][0]) + i)].append(arrival - difference)


        dbl.modifyEntry(collection,
                            {"Linea": line["Linea"]},
                            {"Compressed_Timetable": [departures, arrivals]})
        
    elif opt == 3:
        for departure in line["Compressed_Timetable"][0]:
            departures.append(departure + difference)

        for i, arrival in enumerate(line["Compressed_Timetable"][1]):
            arrivals.append(arrival + difference)

def compressLines(sortedLines:list, timeZone:tuple) -> dict:
    """
    This function compresses valid lines

    Parameters:
    sortedLines(list): List with the lines that need to be compressed in the order of compression.

    Returns:
    stations(dict): Compressed arrivals
    """
    collection = dbl.selectCollection("trainLines", "TFG")
    lines = dbl.readCollection(collection)

    firstLine = None

    maxLines = len(sortedLines)
    tref = None
    tact = None

    stations = {chr(i): [] for i in range(ord(capacityParams["stationOrg"]), ord(capacityParams["stationEnd"]) + 1)}   

    for sLine in sortedLines:
        for line in lines:
            if line["Linea"] == sLine:
                if maxLines == len(sortedLines):
                    firstLine = line
                    tref = timeZone[2]
                    for time in line["Compressed_Timetable"][0]:
                        if tact == None:
                            tact = time

                        elif tact > time:
                            tact = time

                    difference = abs(tact - tref)
                    if ord(line["Stations"][0]) <= ord(capacityParams["stationOrg"]):
                        adjustAndSave(1, difference, line, collection, stations)
                        tref = None
                        tact = None

                    else:
                        adjustAndSave(2, difference, line, collection, stations)
                        tref = None
                        tact = None

                    maxLines -= 1

                else:
                    if ord(line["Stations"][0]) <= ord(capacityParams["stationOrg"]):
                        for i, time in enumerate(line["Compressed_Timetable"][0]):
                            if (tref == None) or (abs(tref - tact)) > (abs(stations[chr(ord(capacityParams) + i)][-1] - time)):
                                tref = stations[chr(ord(capacityParams["stationOrg"]) + i)][-1]
                                tact = time

                        difference = abs(tact - tref)
                        adjustAndSave(1, difference, line, collection, stations)
                        tref = None
                        tact = None
                    
                    else:
                        for i, time in enumerate(line["Compressed_Timetable"][0]):
                            if (tref == None) or (abs(tref - tact)) > (abs(stations[chr(ord(line["Stations"][0]) + i)][-1] - time)):
                                tref = stations[chr(ord(line["Stations"][0]) + i)][-1]
                                tact = time

                        difference = abs(tact - tref)
                        adjustAndSave(2, difference, line, collection, stations)
                        tref = None
                        tact = None 

                        maxLines -= 1

    for i, time in enumerate(firstLine["Compressed_Timetable"][0]):
        if (tref == None) or (abs(tref - tact) < abs(stations[chr(ord(firstLine["Stations"][0]) + i)][-1] - time)):
            tref = stations[chr(ord(firstLine["Stations"][0]) + i)][-1]
            tact = time

    difference = abs(tact-tref)
    adjustAndSave(3, difference, firstLine, collection, stations)
    tref = None
    tact = None

    return stations

def capacityCalculator(stationTimes:dict, extraTime:timedelta, timeZone:tuple) -> float:
    """
    Function that calculates the capacity as specified in UIC Leaflet 406 2013.

    Parameters:
    stationTimes(dict): Dictionary with the compressed arrivals
    extraTime(timedelta): Parameter of additional time.
    timeZone(tuple): 
    """

    maxArrivalTime = None

    for station in stationTimes:
        if len(stationTimes[station]) > 0:
            if (maxArrivalTime == None) or stationTimes[station][-1] < maxArrivalTime:
                maxArrivalTime = stationTimes[station][-1]

    if (abs(maxArrivalTime - timeZone[2]) + extraTime) >= abs(timeZone[2] - timeZone[3]):
        capacity = float(100)

    else:
        capacity = float((abs(timeZone[2] - maxArrivalTime) + extraTime)/(abs(timeZone[2] - timeZone[3]))) * 100

    return capacity

def sortStations(validLines:list, stationOrg:str, stationEnd:str) -> list:
    """
    This function, sorts the valid lines to let us know the order to do the compression.

    Parameters:
    validLines(list): List with the lines selected to be compressed.
    stationOrg(str): Origin station of the capacity section.
    stationEnd(str): Destiny station of the capacity section.

    Returns:
    list
    """
    collection = dbl.selectCollection("trainLines", "TFG")
    lines = dbl.readCollection(collection)

    stations = {chr(i): [] for i in range(ord(stationOrg), ord(stationEnd) + 1)}
    linesOrd = []

    for line in lines:
        if line["Linea"] in validLines:
            if ord(stationOrg) >= ord(line["Stations"][0]):
                stations[stationOrg].append([line["Linea"], line["Compressed_Timetable"][0][0]])

            else:
                for i in range(ord(stationOrg), ord(stationEnd) + 1):
                    if ord(line["Stations"][0]) <= i <= ord(line["Stations"][1]):
                        stations[chr(i)].append([line["Linea"], line["Compressed_Timetable"][0][0]])
                        break 

    for station in sorted(stations.keys()):
        sortedData = sorted(stations[station], key=lambda x: x[1])

        linesOrd.extend(indexLine[0] for indexLine in sortedData)

    return linesOrd
        

  
def saveLine(numberLine:int, timeZone:tuple):
    collection = dbl.selectCollection("trainLines", "TFG")
    lines = dbl.readCollection(collection)

    for line in lines:
        if (line["Linea"] == numberLine):
            ttOrg = line["Timetable_Margins"]
            ttSave = []
            stations = line["Stations"]
            temporaryList1 = []
            temporaryList2 = []

            for i in range(0, (ord(stations[1]) - ord(stations[0]))):
                if (ord(timeZone[0]) <= (ord(stations[0]) + i) < ord(timeZone[1])):
                    temporaryList1.append(ttOrg[0][i])
                    temporaryList2.append(ttOrg[1][i])

            ttSave.append(temporaryList1)
            ttSave.append(temporaryList2)

            dbl.modifyEntry(collection,
                            {"Linea": numberLine},
                            {"Compressed_Timetable": ttSave})


def generateSelectedtt():
    timeZone = selectTimeZone(capacityParams["stationOrg"],
                              capacityParams["stationEnd"],
                              capacityParams["startHour"],
                              capacityParams["endHour"])
    linesVal = identifyLineTimes(2, timeZone)

    for lineIndex in linesVal:
        saveLine(lineIndex, timeZone)

    sortedLines = sortStations(linesVal, capacityParams["stationOrg"], capacityParams["stationEnd"])
    stationsC = compressLines(sortedLines, timeZone)
    ocupation = round(capacityCalculator(stationsC, capacityParams["extraTime"], timeZone), 2)
    
    return ocupation
