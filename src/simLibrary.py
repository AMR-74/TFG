import random as ran
import src.dbLibrary as dbl
import re
from datetime import timedelta, datetime

# GLOBAL VARIABLES
parameters = {
    "format": r"^(?:[01]\d|2[0-3]):[0-5]\d$",
    "formatHour": "%H:%M",
    "trip": 10,
    "upperTimeLimit": "06:30",
    "lowerTimeLimit": "23:00",
    "nLines": 7,
    "hourMargin": 0,
    "lowerMinuteMargin": 15,
    "higherMinuteMargin": 45,
    "securityMargin": 15
}

# SEED
ran.seed(ran.randint(1,300))

# FUNCTIONS
def changeSeed():
   ran.seed(ran.randint(1,500))

def checkFormat(format,name):
    if re.match(format, name):
        return True
    
    else:
        return False

def generateTrip(n):
    start = 65
    if n > 0 and n <= 26:
        end = 65+n-1

    else:
        raise ValueError("Supera el máximo de estaciones permitido")
    
    return (chr(start),chr(end))

def stationsDefault(trip:list) -> dict:
    return {chr(i): [] for i in range(ord(trip[0]), ord(trip[1]) + 1)}

def hourFormat(hour):
    return datetime.strptime(hour, parameters["formatHour"])

def generateLines(route):
    for n in range(parameters["nLines"]):
        changeSeed()
        stationOrigin = ran.randint(ord(route[0]), ord(route[1]))
        stationDestination = ran.randint(stationOrigin, ord(route[1]))

        if stationOrigin == stationDestination:
            raise ValueError("Error de simulación, línea sin movimiento")
    
        else:
            line = (chr(stationOrigin), chr(stationDestination))
            dbl.dbInputsTL(n+1, line, [], [], 'TFG')   
    
def setTimeLimit(format):
    if checkFormat(format, parameters["upperTimeLimit"]) == False:
        raise ValueError("Error en el formato de hora introducido.")
    
    else:
        start = hourFormat(parameters["upperTimeLimit"])
    
    if checkFormat(format, parameters["lowerTimeLimit"]) == False:
        raise ValueError("Error en el formato de hora introducido.")
    
    else:
        end = hourFormat(parameters["lowerTimeLimit"])

    return(start, end)

def marginsTimetable(opt:int, times:list, line:int) -> list:
    if opt == 1:
        return([times[0]] + [times[i] - timedelta(minutes=parameters["securityMargin"]) for i in range(1, len(times))])
        
    elif opt == 2:
        return([times[i] + timedelta(minutes=parameters["securityMargin"]) for i in range(0, len(times))])

def generateTimetable(limits:tuple, trip:tuple):
    lines = dbl.selectData(dbl.selectCollection("trainLines",'TFG'), "Linea")
    stations = dbl.selectData(dbl.selectCollection("trainLines", 'TFG'), "Stations")
    timeTable = dbl.selectData(dbl.selectCollection("trainLines", 'TFG'), "Timetable")
    used_lines = lines.copy()
    valid_timeTables = []
    valid_lines = []
    tt = stationsDefault(trip)
    counter = 0
    
    while len(used_lines) > 0:
        changeSeed()
        horas_salida = []
        horas_llegada = []
        
        if len(valid_timeTables) == 0:
            current_line = ran.choice(used_lines)
            current_timeTable = timeTable[lines.index(current_line)]
            current_stations = stations[lines.index(current_line)]

            for i in range(ord(current_stations[0]), ord(current_stations[1])):
                
                if len(horas_salida) == 0:
                    departure = limits[0] + timedelta(minutes=parameters["securityMargin"]) + timedelta(minutes=ran.randint(parameters["lowerMinuteMargin"], 
                                                                          parameters["higherMinuteMargin"]))
                    arrival = departure + timedelta(hours=ran.randint(0, parameters["hourMargin"]), minutes=ran.randint(parameters["lowerMinuteMargin"], 
                                                                                                                        parameters["higherMinuteMargin"]))
                    
                    while arrival > limits[1] and (arrival + timedelta(minutes=parameters["securityMargin"])) > limits[1]:
                        counter += 1
                        if counter > 10:
                            raise ValueError("Simulación fallida.")
                        
                        else:
                            changeSeed()
                            departure = limits[0] + timedelta(minutes=parameters["securityMargin"]) + timedelta(minutes=ran.randint(parameters["lowerMinuteMargin"], 
                                                                                  parameters["higherMinuteMargin"]))
                            arrival = departure + timedelta(hours=ran.randint(0, parameters["hourMargin"]), minutes=ran.randint(parameters["lowerMinuteMargin"], 
                                                                                                                                parameters["higherMinuteMargin"]))
                    
                    counter = 0
                    horas_salida.append(departure)
                    horas_llegada.append(arrival)

                else:
                    departure = horas_llegada[len(horas_llegada)-1] + timedelta(minutes=ran.randint(parameters["lowerMinuteMargin"], 
                                                                                                    parameters["higherMinuteMargin"]))
                    arrival = departure + timedelta(hours=ran.randint(0, parameters["hourMargin"]), minutes=ran.randint(parameters["lowerMinuteMargin"], 
                                                                                                                        parameters["higherMinuteMargin"]))

                    while arrival > limits[1] and (arrival + timedelta(minutes=parameters["securityMargin"])) > limits[1]:
                        counter += 1
                        if counter > 10:
                            raise ValueError("Simulación fallida.")
                        
                        else:
                            changeSeed()
                            departure = horas_llegada[len(horas_llegada)-1] + timedelta(minutes=ran.randint(parameters["lowerMinuteMargin"], 
                                                                                                            parameters["higherMinuteMargin"]))
                            arrival = departure + timedelta(hours=ran.randint(0, parameters["hourMargin"]), minutes=ran.randint(parameters["lowerMinuteMargin"], 
                                                                                                                                parameters["higherMinuteMargin"]))

                    counter = 0
                    horas_salida.append(departure)
                    horas_llegada.append(arrival)

        else:
            current_line = ran.choice(used_lines)
            current_timeTable:list = timeTable[lines.index(current_line)]
            current_stations:list = stations[lines.index(current_line)]
            
            for station in range(ord(stations[lines.index(valid_lines[len(valid_lines) - 1])][0]), ord(stations[lines.index(valid_lines[len(valid_lines) - 1])][1])):
                tt[chr(station)].append(valid_timeTables[valid_lines.index(valid_lines[len(valid_lines) - 1])][1][ord(stations[lines.index(valid_lines[len(valid_lines) - 1])][1]) - station - 1])
            
            for station in range(ord(current_stations[0]), ord(current_stations[1])):
                                    
                if len(tt[chr(station)]) != 0:
                    referenceHour = max(tt[chr(station)])
                        
                    if len(horas_llegada) == 0 or referenceHour > horas_llegada[len(horas_llegada) - 1]:
                        departure = referenceHour + timedelta(minutes=ran.randint(parameters["lowerMinuteMargin"], 
                                                                                  parameters["higherMinuteMargin"]))
                        arrival = departure + timedelta(hours=ran.randint(0, parameters["hourMargin"]), minutes=ran.randint(parameters["lowerMinuteMargin"], 
                                                                                                                            parameters["higherMinuteMargin"]))

                        while arrival > limits[1] and (arrival + timedelta(minutes=parameters["securityMargin"])) > limits[1]:
                            counter += 1
                            if counter > 10:
                                raise ValueError("Simulación fallida.")
                        
                            else:
                                changeSeed()
                                departure = referenceHour + timedelta(minutes=ran.randint(parameters["lowerMinuteMargin"], 
                                                                                          parameters["higherMinuteMargin"]))
                                arrival = departure + timedelta(hours=ran.randint(0, parameters["hourMargin"]), minutes=ran.randint(parameters["lowerMinuteMargin"], 
                                                                                                                                    parameters["higherMinuteMargin"]))

                        counter = 0
                        horas_salida.append(departure)
                        horas_llegada.append(arrival)

                    else:
                        departure = horas_llegada[len(horas_llegada)-1] + timedelta(minutes=ran.randint(parameters["lowerMinuteMargin"], 
                                                                                                        parameters["higherMinuteMargin"]))
                        arrival = departure + timedelta(hours=ran.randint(0, parameters["hourMargin"]), minutes=ran.randint(parameters["lowerMinuteMargin"], 
                                                                                                                            parameters["higherMinuteMargin"]))

                        while arrival > limits[1] and (arrival + timedelta(minutes=parameters["securityMargin"])) > limits[1]:
                            counter += 1
                            if counter > 10:
                                raise ValueError("Simulación fallida.")
                        
                            else:
                                changeSeed()
                                departure = horas_llegada[len(horas_llegada)-1] + timedelta(minutes=ran.randint(parameters["lowerMinuteMargin"], 
                                                                                                                parameters["higherMinuteMargin"]))
                                arrival = departure + timedelta(hours=ran.randint(0, parameters["hourMargin"]), minutes=ran.randint(parameters["lowerMinuteMargin"], 
                                                                                                                                    parameters["higherMinuteMargin"]))

                        counter = 0
                        horas_salida.append(departure)
                        horas_llegada.append(arrival)

                else:
                        
                    if len(horas_salida) == 0:
                        departure = limits[0] + timedelta(minutes=parameters["securityMargin"]) + timedelta(minutes=ran.randint(parameters["lowerMinuteMargin"], 
                                                                                                                                parameters["higherMinuteMargin"]))
                        arrival = departure + timedelta(hours=ran.randint(0, parameters["hourMargin"]), minutes=ran.randint(parameters["lowerMinuteMargin"], 
                                                                                                                            parameters["higherMinuteMargin"]))

                        while arrival > limits[1] and (arrival + timedelta(minutes=parameters["securityMargin"])) > limits[1]:
                            counter += 1
                            if counter > 10:
                                raise ValueError("Simulación fallida.")
                        
                            else:
                                changeSeed()
                                departure = limits[0] + timedelta(minutes=parameters["securityMargin"]) + timedelta(minutes=ran.randint(parameters["lowerMinuteMargin"], 
                                                                                                                                        parameters["higherMinuteMargin"]))
                                arrival = departure + timedelta(hours=ran.randint(0, parameters["hourMargin"]), minutes=ran.randint(parameters["lowerMinuteMargin"], 
                                                                                                                                    parameters["higherMinuteMargin"]))

                        counter = 0
                        horas_salida.append(departure)
                        horas_llegada.append(arrival)

                    else:
                        departure = horas_llegada[len(horas_llegada)-1] + timedelta(minutes=ran.randint(parameters["lowerMinuteMargin"], 
                                                                                                        parameters["higherMinuteMargin"]))
                        arrival = departure + timedelta(hours=ran.randint(0, parameters["hourMargin"]), minutes=ran.randint(parameters["lowerMinuteMargin"], 
                                                                                                                            parameters["higherMinuteMargin"]))

                        while arrival > limits[1] and (arrival + timedelta(minutes=parameters["securityMargin"])) > limits[1]:
                            counter += 1
                            if counter > 10:
                                raise ValueError("Simulación fallida.")
                        
                            else:
                                changeSeed()
                                departure = horas_llegada[len(horas_llegada)-1] + timedelta(minutes=ran.randint(parameters["lowerMinuteMargin"], 
                                                                                                                parameters["higherMinuteMargin"]))
                                arrival = departure + timedelta(hours=ran.randint(0, parameters["hourMargin"]), minutes=ran.randint(parameters["lowerMinuteMargin"], 
                                                                                                                                    parameters["higherMinuteMargin"]))

                        counter = 0             
                        horas_salida.append(departure)
                        horas_llegada.append(arrival)
                
        valid_lines.append(current_line)
        used_lines.remove(current_line)
        current_timeTable.append(horas_salida)
        current_timeTable.append(horas_llegada)
        valid_timeTables.append(current_timeTable)
        dbl.modifyEntry(dbl.selectCollection("trainLines", 'TFG'), {"Linea": current_line}, {"Timetable": current_timeTable})
        dbl.modifyEntry(dbl.selectCollection("trainLines", 'TFG'), {"Linea": current_line}, {"Timetable_Margins": [marginsTimetable(1, horas_salida, current_line),
                                                                                                            marginsTimetable(2, horas_llegada, current_line)]})

