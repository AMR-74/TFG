from django.shortcuts import render, redirect
from django.http import JsonResponse
from src import simLibrary
from src import dbLibrary as dbl
import time
from datetime import datetime

# Create your views here.
def simulator(request):
    if request.method == "POST":
        trip_form = request.POST.get("trip")
        startHour = request.POST.get("startHour")
        endHour = request.POST.get("endHour")
        lines = request.POST.get("lines")
        secuMargin = request.POST.get("secuMargin")
        lMargin = request.POST.get("lMargin")
        hMargin = request.POST.get("hMargin")

        request.session['trip'] = trip_form
        request.session['startHour'] = startHour
        request.session['endHour'] = endHour
        request.session['lines'] = lines
        request.session['lMargin'] = lMargin
        request.session['hMargin'] = hMargin
        request.session['secuMargin'] = secuMargin

        simLibrary.parameters["trip"] = int(trip_form)
        simLibrary.parameters["upperTimeLimit"] = startHour
        simLibrary.parameters["lowerTimeLimit"] = endHour
        simLibrary.parameters["nLines"] = int(lines)
        simLibrary.parameters["lowerMinuteMargin"] = int(lMargin)
        simLibrary.parameters["higherMinuteMargin"] = int(hMargin)
        simLibrary.parameters["securityMargin"] = int(secuMargin)

        print(simLibrary.parameters)

        limits = simLibrary.setTimeLimit(simLibrary.parameters["format"])
        trip_tuple = simLibrary.generateTrip(simLibrary.parameters["trip"])
        dbl.deleteCollection(dbl.selectCollection("trainLines",'TFG'))
        simLibrary.generateLines(trip_tuple, simLibrary.parameters["minStations"])
        simLibrary.generateTimetable(limits, trip_tuple)

        time.sleep(2)

        return redirect('simulator')
    
    trip = request.session.get('trip')
    startHour = request.session.get('startHour')
    endHour = request.session.get('endHour')
    lines = request.session.get('lines')
    secuMargin = request.session.get('secuMargin')

    train_lines_data_raw = list(dbl.selectCollection("trainLines", "TFG").find({}, {"_id": 0}))  # recogemos todos los datos de trainLines

    train_lines_data = []

    for line in train_lines_data_raw:
    # Prepara la estructura
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
            "Linea": line.get("Linea"),
            "Stations": line.get("Stations"),
            "Timetable": line.get("Timetable"),
            "Departures": formatted_departures,
            "Arrivals": formatted_arrivals
        })

    return render(request, "railSimulator/simulation.html", 
    {
        "trip": trip, 
        "startHour": startHour,
        "endHour": endHour,
        "lines": lines,
        "secuMargin": secuMargin,
        "train_lines": train_lines_data,
        "timestamp": datetime.now().timestamp()
    })

def home(request):
    return render(request, "railSimulator/home.html")




