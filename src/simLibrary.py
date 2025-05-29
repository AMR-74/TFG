import random as ran
import src.dbLibrary as dbl
import src.generateDiagram as gd
import re
from datetime import timedelta, datetime


# GLOBAL VARIABLES
parameters = {
    "format": r"^(?:[01]\d|2[0-3]):[0-5]\d$",
    "formatHour": "%H:%M",
    "trip": None,
    "upperTimeLimit": None ,
    "lowerTimeLimit": None,
    "nLines": None,
    "hourMargin": 0,
    "lowerMinuteMargin": 10,
    "higherMinuteMargin": 40,
    "securityMargin": None
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

def hourFormat(hour):
    return datetime.strptime(hour, parameters["formatHour"])

def generateLines(route):
    estaciones = [chr(i) for i in range(ord(route[0]), ord(route[1]) + 1)]
    posibles_lineas = []

    # Generar todas las combinaciones posibles A → B, B → C, etc. sin repeticiones ni simetrías
    for i in range(len(estaciones)):
        for j in range(i + 1, len(estaciones)):
            posibles_lineas.append((estaciones[i], estaciones[j]))

    # Barajar las posibles líneas
    ran.shuffle(posibles_lineas)

    total_a_generar = min(parameters["nLines"], len(posibles_lineas))
    generadas = posibles_lineas[:total_a_generar]

    print(f"[DEBUG] Líneas generadas: {generadas}", flush=True)

    for idx, line in enumerate(generadas):
        dbl.dbInputsTL(idx + 1, line, [], [], 'TFG')
    
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
    print("[DEBUG] Entrando en generateTimetable 🚂")
    lines = dbl.selectData(dbl.selectCollection("trainLines",'TFG'), "Linea")
    stations = dbl.selectData(dbl.selectCollection("trainLines", 'TFG'), "Stations")
    timeTable = dbl.selectData(dbl.selectCollection("trainLines", 'TFG'), "Timetable")
    used_lines = lines.copy()
    valid_timeTables = []
    valid_lines = []
    valid_stations = []
    tt = stationsDefault(trip)
    counter = 0
    
    print(f"[DEBUG] Líneas disponibles: {used_lines}", flush=True)
    
    while len(used_lines) > 0:
        print(f"[DEBUG] Iterando línea. Quedan: {len(used_lines)}", flush=True)

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
                        if counter > 200:
                            raise ValueError("Simulación fallida.")
                        
                        else:
                            changeSeed()
                            departure = limits[0] + timedelta(minutes=parameters["securityMargin"]) + timedelta(minutes=ran.randint(parameters["lowerMinuteMargin"], 
                                                                                  parameters["higherMinuteMargin"]))
                            arrival = departure + timedelta(minutes=parameters["securityMargin"]) + timedelta(hours=ran.randint(0, parameters["hourMargin"]), minutes=ran.randint(parameters["lowerMinuteMargin"], 
                                                                                                                                parameters["higherMinuteMargin"]))
                    
                    counter = 0
                    horas_salida.append(departure)
                    horas_llegada.append(arrival)

                else:
                    departure = horas_llegada[len(horas_llegada)-1] + timedelta(minutes=parameters["securityMargin"]) + timedelta(minutes=ran.randint(parameters["lowerMinuteMargin"], 
                                                                                                    parameters["higherMinuteMargin"]))
                    arrival = departure + timedelta(minutes=parameters["securityMargin"]) + timedelta(hours=ran.randint(0, parameters["hourMargin"]), minutes=ran.randint(parameters["lowerMinuteMargin"], 
                                                                                                                        parameters["higherMinuteMargin"]))

                    while arrival > limits[1] and (arrival + timedelta(minutes=parameters["securityMargin"])) > limits[1]:
                        counter += 1
                        if counter > 200:
                            raise ValueError("Simulación fallida.")
                        
                        else:
                            changeSeed()
                            departure = horas_llegada[len(horas_llegada)-1] + timedelta(minutes=parameters["securityMargin"]) + timedelta(minutes=ran.randint(parameters["lowerMinuteMargin"], 
                                                                                                            parameters["higherMinuteMargin"]))
                            arrival = departure + timedelta(minutes=parameters["securityMargin"]) + timedelta(hours=ran.randint(0, parameters["hourMargin"]), minutes=ran.randint(parameters["lowerMinuteMargin"], 
                                                                                                                                parameters["higherMinuteMargin"]))

                    counter = 0
                    horas_salida.append(departure)
                    horas_llegada.append(arrival)

        else:
            current_line = ran.choice(used_lines)
            current_timeTable:list = timeTable[lines.index(current_line)]
            current_stations:list = stations[lines.index(current_line)]
            
            for station in range(ord(valid_stations[0]), ord(valid_stations[1])):
                tt[chr(station)].append(valid_timeTables[-1][1][station - ord(valid_stations[0])])
            
            for station in range(ord(current_stations[0]), ord(current_stations[1])):
                                    
                if len(tt[chr(station)]) != 0:
                    referenceHour = max(tt[chr(station)])
                        
                    if len(horas_llegada) == 0 or referenceHour > horas_llegada[len(horas_llegada) - 1]:
                        departure = referenceHour + timedelta(minutes=parameters["securityMargin"]) + timedelta(minutes=ran.randint(parameters["lowerMinuteMargin"], 
                                                                                  parameters["higherMinuteMargin"]))
                        arrival = departure + timedelta(minutes=parameters["securityMargin"]) + timedelta(hours=ran.randint(0, parameters["hourMargin"]), minutes=ran.randint(parameters["lowerMinuteMargin"], 
                                                                                                                            parameters["higherMinuteMargin"]))

                        while arrival > limits[1] and (arrival + timedelta(minutes=parameters["securityMargin"])) > limits[1]:
                            counter += 1
                            if counter > 200:
                                raise ValueError("Simulación fallida.")
                        
                            else:
                                changeSeed()
                                departure = referenceHour + timedelta(minutes=parameters["securityMargin"]) + timedelta(minutes=ran.randint(parameters["lowerMinuteMargin"], 
                                                                                          parameters["higherMinuteMargin"]))
                                arrival = departure + timedelta(minutes=parameters["securityMargin"]) + timedelta(hours=ran.randint(0, parameters["hourMargin"]), minutes=ran.randint(parameters["lowerMinuteMargin"], 
                                                                                                                                    parameters["higherMinuteMargin"]))

                        counter = 0
                        horas_salida.append(departure)
                        horas_llegada.append(arrival)

                    else:
                        departure = horas_llegada[len(horas_llegada)-1] + timedelta(minutes=parameters["securityMargin"]) + timedelta(minutes=ran.randint(parameters["lowerMinuteMargin"], 
                                                                                                        parameters["higherMinuteMargin"]))
                        arrival = departure + timedelta(minutes=parameters["securityMargin"]) + timedelta(hours=ran.randint(0, parameters["hourMargin"]), minutes=ran.randint(parameters["lowerMinuteMargin"], 
                                                                                                                            parameters["higherMinuteMargin"]))

                        while arrival > limits[1] and (arrival + timedelta(minutes=parameters["securityMargin"])) > limits[1]:
                            counter += 1
                            if counter > 200:
                                raise ValueError("Simulación fallida.")
                        
                            else:
                                changeSeed()
                                departure = horas_llegada[len(horas_llegada)-1] + timedelta(minutes=parameters["securityMargin"]) + timedelta(minutes=ran.randint(parameters["lowerMinuteMargin"], 
                                                                                                                parameters["higherMinuteMargin"]))
                                arrival = departure + timedelta(minutes=parameters["securityMargin"]) + timedelta(hours=ran.randint(0, parameters["hourMargin"]), minutes=ran.randint(parameters["lowerMinuteMargin"], 
                                                                                                                                    parameters["higherMinuteMargin"]))

                        counter = 0
                        horas_salida.append(departure)
                        horas_llegada.append(arrival)

                else:
                        
                    if len(horas_salida) == 0:
                        departure = limits[0] + timedelta(minutes=parameters["securityMargin"]) + timedelta(minutes=ran.randint(parameters["lowerMinuteMargin"], 
                                                                                                                                parameters["higherMinuteMargin"]))
                        arrival = departure + timedelta(minutes=parameters["securityMargin"]) +  timedelta(hours=ran.randint(0, parameters["hourMargin"]), minutes=ran.randint(parameters["lowerMinuteMargin"], 
                                                                                                                            parameters["higherMinuteMargin"]))

                        while arrival > limits[1] and (arrival + timedelta(minutes=parameters["securityMargin"])) > limits[1]:
                            counter += 1
                            if counter > 200:
                                raise ValueError("Simulación fallida.")
                        
                            else:
                                changeSeed()
                                departure = limits[0] + timedelta(minutes=parameters["securityMargin"]) + timedelta(minutes=ran.randint(parameters["lowerMinuteMargin"], 
                                                                                                                                        parameters["higherMinuteMargin"]))
                                arrival = departure + timedelta(minutes=parameters["securityMargin"]) + timedelta(hours=ran.randint(0, parameters["hourMargin"]), minutes=ran.randint(parameters["lowerMinuteMargin"], 
                                                                                                                                    parameters["higherMinuteMargin"]))

                        counter = 0
                        horas_salida.append(departure)
                        horas_llegada.append(arrival)

                    else:
                        departure = horas_llegada[len(horas_llegada)-1] + timedelta(minutes=parameters["securityMargin"]) + timedelta(minutes=ran.randint(parameters["lowerMinuteMargin"], 
                                                                                                        parameters["higherMinuteMargin"]))
                        arrival = departure + timedelta(minutes=parameters["securityMargin"]) + timedelta(hours=ran.randint(0, parameters["hourMargin"]), minutes=ran.randint(parameters["lowerMinuteMargin"], 
                                                                                                                            parameters["higherMinuteMargin"]))

                        while arrival > limits[1] and (arrival + timedelta(minutes=parameters["securityMargin"])) > limits[1]:
                            counter += 1
                            if counter > 200:
                                raise ValueError("Simulación fallida.")
                        
                            else:
                                changeSeed()
                                departure = horas_llegada[len(horas_llegada)-1] + timedelta(minutes=parameters["securityMargin"]) + timedelta(minutes=ran.randint(parameters["lowerMinuteMargin"], 
                                                                                                                parameters["higherMinuteMargin"]))
                                arrival = departure + timedelta(minutes=parameters["securityMargin"]) + timedelta(hours=ran.randint(0, parameters["hourMargin"]), minutes=ran.randint(parameters["lowerMinuteMargin"], 
                                                                                                                                    parameters["higherMinuteMargin"]))

                        counter = 0             
                        horas_salida.append(departure)
                        horas_llegada.append(arrival)
                
        valid_lines.append(current_line)
        used_lines.remove(current_line)
        current_timeTable.append(horas_salida)
        current_timeTable.append(horas_llegada)
        valid_timeTables.append(current_timeTable)
        valid_stations = [current_stations[0], current_stations[1]]

        print(f"[DEBUG] Modificando linea: {current_line}", flush=True)
        print(f"[DEBUG] Nuevo Timetable: {current_timeTable}", flush=True)

        try:
            result1 = dbl.modifyEntry(
            dbl.selectCollection("trainLines", 'TFG'),
                    {"Linea": current_line},
                    {"Timetable": current_timeTable}
            )
    
            print(f"[DEBUG] Resultado modificación Timetable: {result1}", flush=True)

            result2 = dbl.modifyEntry(
                dbl.selectCollection("trainLines", 'TFG'),
                    {"Linea": current_line},
                    {
                        "Timetable_Margins": [
                        marginsTimetable(1, horas_salida, current_line),
                        marginsTimetable(2, horas_llegada, current_line)
                        ]
                    }
                )
            print(f"[DEBUG] Resultado modificación Margins: {result2}", flush=True)

        except Exception as e:
            print(f"[ERROR] Fallo modificando MongoDB para {current_line}: {e}", flush=True)

    gd.generateDiagram()


