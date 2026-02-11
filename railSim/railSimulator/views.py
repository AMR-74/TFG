from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.core.files.storage import FileSystemStorage
from src import simLibrary
from src import dbLibrary as dbl
from src import readYamlFiles as ryf
import time
from datetime import datetime
from src import capacity as cp

# Create your views here.

def generate_capacity(request):
    """
    Handles the POST request to calculate infrastructure capacity.
    Updates capacity parameters and redirects back to the simulator.
    """
    if request.method == "POST":
        stationOrg = request.POST.get("stationOrg").upper()
        stationEnd = request.POST.get("stationEnd").upper()
        startHour = request.POST.get("startHourCapacity")
        endHour = request.POST.get("endHourCapacity")

        # Update global capacity parameters
        cp.capacityParams["stationOrg"] = stationOrg
        cp.capacityParams["stationEnd"] = stationEnd
        cp.capacityParams["startHour"] = startHour
        cp.capacityParams["endHour"] = endHour

        # Calculate occupancy percentage
        ocupation = cp.generateSelectedtt()
        request.session["ocupation"] = ocupation

        return redirect('simulator')

def simulator(request):
    """
    Main view for the rail simulator. Handles file uploads, 
    random timetable generation, and data visualization.
    """
    if request.method == "POST":
        # Handle YAML file upload for real data import
        if request.FILES.get('uploaded_file'):
            uploaded_file = request.FILES['uploaded_file']
            fs = FileSystemStorage()
            file_name = fs.save(uploaded_file.name, uploaded_file)
            file_path = fs.path(file_name)

            ryf.importData(file_path)

            # Brief pause to ensure database insertion and image generation
            time.sleep(2)
            return redirect('simulator')

        # Handle random simulation parameters from the form
        trip_form = request.POST.get("trip")
        startHour = request.POST.get("startHour")
        endHour = request.POST.get("endHour")
        lines = request.POST.get("lines")
        secuMargin = request.POST.get("secuMargin")
        lMargin = request.POST.get("lMargin")
        hMargin = request.POST.get("hMargin")

        # Store parameters in session for persistence
        request.session['trip'] = trip_form
        request.session['startHour'] = startHour
        request.session['endHour'] = endHour
        request.session['lines'] = lines
        request.session['lMargin'] = lMargin
        request.session['hMargin'] = hMargin
        request.session['secuMargin'] = secuMargin

        # Update simulation library parameters
        simLibrary.parameters["trip"] = int(trip_form)
        simLibrary.parameters["upperTimeLimit"] = startHour
        simLibrary.parameters["lowerTimeLimit"] = endHour
        simLibrary.parameters["nLines"] = int(lines)
        simLibrary.parameters["lowerMinuteMargin"] = int(lMargin)
        simLibrary.parameters["higherMinuteMargin"] = int(hMargin)
        simLibrary.parameters["securityMargin"] = int(secuMargin)

        # Execute simulation pipeline
        limits = simLibrary.setTimeLimit(simLibrary.parameters["format"])
        trip_tuple = simLibrary.generateTrip(simLibrary.parameters["trip"])
        
        # Clear previous data and generate new lines and timetable
        dbl.deleteCollection(dbl.selectCollection("trainLines", 'TFG'))
        simLibrary.generateLines(trip_tuple, simLibrary.parameters["minStations"])
        simLibrary.generateTimetable(limits, trip_tuple)

        time.sleep(2)
        return redirect('simulator')
    
    # GET Request: Prepare data for the simulation template
    trip = request.session.get('trip')
    startHour = request.session.get('startHour')
    endHour = request.session.get('endHour')
    lines = request.session.get('lines')
    secuMargin = request.session.get('secuMargin')

    # Fetch all train line data from MongoDB
    train_lines_data_raw = list(dbl.selectCollection("trainLines", "TFG").find({}, {"_id": 0}))

    train_lines_data = []

    for line in train_lines_data_raw:
        formatted_departures = []
        formatted_arrivals = []
        
        # Format datetime objects into strings for the template table
        if "Timetable_Margins" in line and line["Timetable_Margins"]:
            departures = line["Timetable_Margins"][0]
            arrivals = line["Timetable_Margins"][1]
        
            for hora in departures:
                formatted_departures.append(simLibrary.visualHourFormat(hora))
        
            for hora in arrivals:
                formatted_arrivals.append(simLibrary.visualHourFormat(hora))

        # Build the final data list using the updated 'Lines' key
        train_lines_data.append({
            "Lines": line.get("Lines"),  # UPDATED: Changed from "Linea" to "Lines"
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
        "timestamp": datetime.now().timestamp(), # Forces browser to refresh the diagram image
        "ocupation": ocupation
    })

def home(request):
    """
    Renders the home page of the application.
    """
    return render(request, "railSimulator/home.html")