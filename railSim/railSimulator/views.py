from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.core.files.storage import FileSystemStorage
from src import simLibrary
from src import dbLibrary as dbl
from src import readYamlFiles as ryf
import time
from django.contrib import messages 
from datetime import datetime
from src import capacity as cp

# --- VISTA PRINCIPAL DEL SIMULADOR ---
def simulator(request):
    """
    Main view for the rail simulator. Handles file uploads, 
    random timetable generation, and data visualization.
    """
    if request.method == "POST":
        # 1. Gestión de subida de archivos YAML
        if request.FILES.get('uploaded_file'):
            try:
                uploaded_file = request.FILES['uploaded_file']
                fs = FileSystemStorage()
                file_name = fs.save(uploaded_file.name, uploaded_file)
                file_path = fs.path(file_name)

                ryf.importData(file_path)
                time.sleep(2)
                messages.success(request, "Archivo YAML cargado correctamente.") 
                return redirect('simulator')
            except Exception as e:
                messages.error(request, f"Error al procesar el archivo: {e}")
                return redirect('simulator')

        # 2. Gestión del formulario de simulación (Random Simulation)
        # Solo entra aquí si NO es subida de archivo y NO es capacidad (que va a otra URL)
        # pero como el form de capacidad tiene su propia action, no hay conflicto.
        if request.POST.get("trip"): 
            try:
                # Recuperamos datos
                trip_form = request.POST.get("trip")
                startHour = request.POST.get("startHour")
                endHour = request.POST.get("endHour")
                lines = request.POST.get("lines")
                secuMargin = request.POST.get("secuMargin")
                lMargin = request.POST.get("lMargin")
                hMargin = request.POST.get("hMargin")

                # Validación básica de campos vacíos
                if not all([trip_form, startHour, endHour, lines, secuMargin, lMargin, hMargin]):
                    raise ValueError("Todos los campos del generador son obligatorios.")

                # Guardar en sesión
                request.session['trip'] = trip_form
                request.session['startHour'] = startHour
                request.session['endHour'] = endHour
                request.session['lines'] = lines
                request.session['lMargin'] = lMargin
                request.session['hMargin'] = hMargin
                request.session['secuMargin'] = secuMargin

                # Validar formato de hora
                import re
                time_regex = r"^(?:[01]\d|2[0-3]):[0-5]\d$"
                if not re.match(time_regex, startHour) or not re.match(time_regex, endHour):
                    raise ValueError("El formato de hora debe ser HH:MM (ej. 09:00)")

                # Actualizar parámetros
                simLibrary.parameters["trip"] = int(trip_form)
                simLibrary.parameters["nLines"] = int(lines)
                simLibrary.parameters["lowerMinuteMargin"] = int(lMargin)
                simLibrary.parameters["higherMinuteMargin"] = int(hMargin)
                simLibrary.parameters["securityMargin"] = int(secuMargin)
                simLibrary.parameters["upperTimeLimit"] = startHour
                simLibrary.parameters["lowerTimeLimit"] = endHour

                # Ejecutar lógica
                limits = simLibrary.setTimeLimit(simLibrary.parameters["format"])
                trip_tuple = simLibrary.generateTrip(simLibrary.parameters["trip"])
                
                dbl.deleteCollection(dbl.selectCollection("trainLines", 'TFG'))
                simLibrary.generateLines(trip_tuple, simLibrary.parameters["minStations"])
                simLibrary.generateTimetable(limits, trip_tuple)

                time.sleep(2)
                messages.success(request, "Simulación generada exitosamente.")
                return redirect('simulator')
                
            except ValueError as e:
                messages.error(request, f"Datos incorrectos: {e}")
                return redirect('simulator')
                
            except Exception as e:
                messages.error(request, f"Ocurrió un error inesperado: {e}")
                return redirect('simulator')

    # --- GET REQUEST (Cargar la página) ---
    trip = request.session.get('trip')
    startHour = request.session.get('startHour')
    endHour = request.session.get('endHour')
    lines = request.session.get('lines')
    secuMargin = request.session.get('secuMargin')

    # Obtener datos de MongoDB
    train_lines_data_raw = list(dbl.selectCollection("trainLines", "TFG").find({}, {"_id": 0}))
    train_lines_data = []

    for line in train_lines_data_raw:
        formatted_departures = []
        formatted_arrivals = []
        
        if "Timetable_Margins" in line and line["Timetable_Margins"]:
            departures = line["Timetable_Margins"][0]
            arrivals = line["Timetable_Margins"][1]
        
            for hora in departures:
                formatted_departures.append(simLibrary.visualHourFormat(hora))
        
            for hora in arrivals:
                formatted_arrivals.append(simLibrary.visualHourFormat(hora))

        train_lines_data.append({
            "Lines": line.get("Lines"),  
            "Stations": line.get("Stations"),
            "Timetable": line.get("Timetable"),
            "Departures": formatted_departures,
            "Arrivals": formatted_arrivals
        })

    ocupation = request.session.get("ocupation", None)

    return render(request, "railSimulator/simulation.html", 
    {
        "trip": trip, 
        "startHour": startHour,
        "endHour": endHour,
        "lines": lines,
        "secuMargin": secuMargin,
        "train_lines": train_lines_data,
        "timestamp": datetime.now().timestamp(), 
        "ocupation": ocupation
    })

# --- VISTA PARA LA CAPACIDAD ---
def generate_capacity(request):
    if request.method == "POST":
        try:
            # 1. Recuperar inputs del formulario
            st_org = request.POST.get("stationOrg")
            st_end = request.POST.get("stationEnd")
            start = request.POST.get("startHourCapacity")
            end = request.POST.get("endHourCapacity")

            if not all([st_org, st_end, start, end]):
                raise ValueError("Todos los campos son obligatorios.")

            # 2. LLAMADA REAL A LA LÓGICA DE CAPACIDAD
            result = cp.generateSelectedtt(st_org, st_end, start, end)
            
            # 3. Guardar resultado
            request.session['ocupation'] = result
            messages.success(request, f"Capacidad calculada: {result}%")

        except ValueError as e:
            messages.error(request, f"Datos inválidos: {e}")
            request.session['ocupation'] = None

        except Exception as e:
            messages.error(request, f"Error del sistema: {e}")
            request.session['ocupation'] = None

    return redirect('simulator')

# --- VISTA HOME (ESTA ES LA QUE FALTABA) ---
def home(request):
    """
    Renders the home page of the application.
    """
    return render(request, "railSimulator/home.html")