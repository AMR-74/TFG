import src.dbLibrary as dbl
import src.simLibrary as simlb
from datetime import timedelta, datetime

#=== GLOBAL PARAMETERS ===#
capacityParams = {
    "stationOrg": None,
    "stationEnd": None,
    "startHour": None,
    "endHour": None
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

    objTime = None
    objLine = None
    if opt == 1:
        for line in lines:
            nline = line["Linea"]
            times = line["Timetable_Margins"]   
            stations = line["Stations"]
            if objTime == None and objLine == None:
                if ord(timeZone[0]) >= ord(stations[0]) and (stations[1] > timeZone[0]) and (times[0][(ord(timeZone[0]) - ord(stations[0]))] >= timeZone[2]):
                    objLine = nline
                    objTime = times[0][ord(timeZone[0]) - ord(stations[0])]

                else:
                    pass
            
            else:
                if (ord(timeZone[0]) >= ord(stations[0])) and (stations[1] > timeZone[0]):
                    if (times[0][ord(timeZone[0]) - ord(stations[0])] < objTime) and (times[0][ord(timeZone[0]) - ord(stations[0])] >= timeZone[2]):
                        objLine = nline
                        objTime = times[0][ord(timeZone[0]) - ord(stations[0])]
                    
                    else:
                        pass
                
                else:
                    pass

        return objLine
    
    elif opt == 2:
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
    nLine = identifyLineTimes(1, timeZone)
    linesVal = identifyLineTimes(2, timeZone)

    for lineIndex in linesVal:
        saveLine(lineIndex, timeZone)

    print("Done")
