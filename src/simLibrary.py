import random as ran
import src.dbLibrary as dbl
import src.generateDiagram as gd
import re
import os
from datetime import timedelta, datetime


#=== GLOBAL VARIABLES ===#
parameters = {
    "format": r"^(?:[01]\d|2[0-3]):[0-5]\d$",
    "formatHour": "%H:%M",
    "trip": None,
    "upperTimeLimit": None ,
    "lowerTimeLimit": None,
    "nLines": None,
    "hourMargin": 0,
    "lowerMinuteMargin": 10,
    "higherMinuteMargin": 30,
    "securityMargin": None,
    "MaxIterations": 500000,
    "lineOffset": 10,
    "minStations": 4
}

#=== SEED ===#
ran.seed(ran.randint(1,300))

#=== FUNCTIONS ===#
def changeSeed():
   ran.seed(ran.randint(1,500))

def checkFormat(formatReference,name):
    if re.match(formatReference, name):
        return True
    
    else:
        return False

def visualHourFormat(hour):
    return hour.strftime(parameters["formatHour"])

def generateTrip(n):
    start = 65
    if n > 0 and n <= 26:
        end = 65+n-1

    else:
        raise ValueError("Supera el máximo de estaciones permitido")
    
    return (chr(start),chr(end))

def stationsDefault(trip:list) -> dict:
    return {chr(i): [] for i in range(ord(trip[0]), ord(trip[1]) + 1)}

def hourFormat(hour, formatHour):
    return datetime.strptime(hour, formatHour)

def generateLines(route, min_stations_per_line):
    estaciones = [chr(i) for i in range(ord(route[0]), ord(route[1]) + 1)]
    posibles_lineas = []

    # Generar TODAS las líneas posibles que tengan al menos `min_stations_per_line` estaciones
    for i in range(len(estaciones)):
        for j in range(i + min_stations_per_line, len(estaciones)):
            posibles_lineas.append((estaciones[i], estaciones[j]))

    if not posibles_lineas:
        print(f"[ERROR] No hay suficientes estaciones para formar líneas de mínimo {min_stations_per_line} estaciones.")
        return

    generadas = []
    total_a_generar = parameters["nLines"]

    # Permitir repeticiones de líneas
    while len(generadas) < total_a_generar:
        generadas.append(ran.choice(posibles_lineas))

    print(f"[DEBUG] Líneas generadas: {generadas}", flush=True)

    for idx, line in enumerate(generadas):
        listLines = [chr(station) for station in range(ord(line[0]), ord(line[1]) + 1)]
        dbl.dbInputsTL(idx + 1, listLines, [], [], 'TFG', [], [])
    
def setTimeLimit(formatReference):
    if checkFormat(formatReference, parameters["upperTimeLimit"]) == False:
        raise ValueError("Error en el formato de hora introducido.")
    
    else:
        start = hourFormat(parameters["upperTimeLimit"], parameters["formatHour"])
    
    if checkFormat(formatReference, parameters["lowerTimeLimit"]) == False:
        raise ValueError("Error en el formato de hora introducido.")
    
    else:
        end = hourFormat(parameters["lowerTimeLimit"], parameters["formatHour"])

    return(start, end)

def marginsTimetable(opt:int, times:list, line:int) -> list:
    if opt == 1:
        return([times[0]] + [times[i] - timedelta(minutes=parameters["securityMargin"]) for i in range(1, len(times))])
        
    elif opt == 2:
        return([times[i] + timedelta(minutes=parameters["securityMargin"]) for i in range(0, len(times))])
    
def conflictDetection(station, newDeparture, newArrival, margin, ocuStations):
    new_start = newDeparture - margin
    new_end = newArrival + margin

    for start, end in ocuStations[station]:
        if new_start < end and new_end > start:
            return True
    return False
    

def generateTimetable(limits: tuple, trip: tuple):
    print("[DEBUG] Entrando en generateTimetable")

    lines = dbl.selectData(dbl.selectCollection("trainLines", 'TFG'), "Linea")
    stations = dbl.selectData(dbl.selectCollection("trainLines", 'TFG'), "Stations")
    timeTable = dbl.selectData(dbl.selectCollection("trainLines", 'TFG'), "Timetable")
    used_lines = lines.copy()
    valid_lines = []
    valid_timeTables = []

    ocuStations = {chr(i): [] for i in range(ord(trip[0]), ord(trip[1]) + 1)}
    security_margin = timedelta(minutes=parameters["securityMargin"])

    print(f"[DEBUG] Líneas disponibles: {used_lines}", flush=True)

    while used_lines:
        current_line = ran.choice(used_lines)
        current_timeTable = timeTable[lines.index(current_line)]
        current_stations = stations[lines.index(current_line)]

        lineStations = current_stations
        departureTimes = []
        arrivalTimes = []

        startLine = limits[0] + timedelta(minutes=len(valid_lines) * parameters["lineOffset"])

        iterations = 0
        validLine = False

        while not validLine:
            if iterations > parameters["MaxIterations"]:
                if os.path.exists("./railSim/railSimulator/static/img/diagrama.png"):
                    os.remove("./railSim/railSimulator/static/img/diagrama.png")
                
                print("[ERROR] No se pudo generar horario sin solapamientos.")
                return

            startLine = limits[0] + timedelta(minutes=(len(valid_lines) + iterations) * parameters["lineOffset"])
            departureTimes = []
            arrivalTimes = []
            conflicts = False

            for idx, station in enumerate(lineStations):
                segmentDuration = timedelta(minutes=ran.randint(parameters["lowerMinuteMargin"], parameters["higherMinuteMargin"]))

                if idx == 0:
                    departure = startLine
                else:
                    departure = arrivalTimes[-1]

                arrival = departure + segmentDuration

                if arrival > limits[1] or departure > limits[1]:
                    conflicts = True
                    break

                if conflictDetection(station, departure, arrival, security_margin, ocuStations):
                    conflicts = True
                    break

                departureTimes.append(departure)
                arrivalTimes.append(arrival)

            if not conflicts:
                for i, station in enumerate(lineStations):
                    start_ocup = departureTimes[i] - security_margin
                    end_ocup = arrivalTimes[i] + security_margin
                    ocuStations[station].append((start_ocup, end_ocup))

                validLine = True
            else:
                iterations += 1


        current_timeTable.append(departureTimes)
        current_timeTable.append(arrivalTimes)

        try:
            result1 = dbl.modifyEntry(
                dbl.selectCollection("trainLines", 'TFG'),
                {"Linea": current_line},
                {"Timetable": current_timeTable}
            )

            result2 = dbl.modifyEntry(
                dbl.selectCollection("trainLines", 'TFG'),
                {"Linea": current_line},
                {
                    "Timetable_Margins": [
                        marginsTimetable(1, departureTimes, current_line),
                        marginsTimetable(2, arrivalTimes, current_line)
                    ]
                }
            )

        except Exception as e:
            print(f"[ERROR] Fallo modificando MongoDB para {current_line}: {e}", flush=True)

        used_lines.remove(current_line)
        valid_lines.append(current_line)
        valid_timeTables.append(current_timeTable)

    gd.generateDiagram(1, [])



