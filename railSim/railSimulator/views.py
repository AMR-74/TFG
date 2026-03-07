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
import re


# --- MAIN VIEW OF THE SIMULATOR ---
def simulator(request):
    """
    Main view for the rail simulator. Handles file uploads,
    random timetable generation, and data visualization.
    """
    if request.method == "POST":
        # 1. YAML file upload management
        if request.FILES.get("uploaded_file"):
            try:
                uploadedFile = request.FILES["uploaded_file"]
                fs = FileSystemStorage()
                fileName = fs.save(uploadedFile.name, uploadedFile)
                filePath = fs.path(fileName)

                ryf.import_data(filePath)
                time.sleep(2)
                messages.success(request, "YAML file uploaded successfully.")
                return redirect("simulator")
            except Exception as e:
                messages.error(request, f"Error processing file: {e}")
                return redirect("simulator")

        # 2. Simulation form management (Random Simulation)
        # This section is only accessed if it's not a file upload.
        if request.POST.get("trip"):
            try:
                # Retrieve data from post request
                tripForm = request.POST.get("trip")
                startHour = request.POST.get("startHour")
                endHour = request.POST.get("endHour")
                lines = request.POST.get("lines")
                secuMargin = request.POST.get("secuMargin")
                lMargin = request.POST.get("lMargin")
                hMargin = request.POST.get("hMargin")

                # Basic validation for empty fields
                if not all(
                    [tripForm, startHour, endHour, lines, secuMargin, lMargin, hMargin]
                ):
                    raise ValueError("All generator fields are mandatory.")

                # Save to session
                request.session["trip"] = tripForm
                request.session["startHour"] = startHour
                request.session["endHour"] = endHour
                request.session["lines"] = lines
                request.session["lMargin"] = lMargin
                request.session["hMargin"] = hMargin
                request.session["secuMargin"] = secuMargin

                # Validate time format using Regex
                TIME_REGEX = r"^(?:[01]\d|2[0-3]):[0-5]\d$"
                if not re.match(TIME_REGEX, startHour) or not re.match(
                    TIME_REGEX, endHour
                ):
                    raise ValueError("Time format must be HH:MM (e.g., 09:00)")

                # Update simulation parameters
                simLibrary.PARAMETERS["trip"] = int(tripForm)
                simLibrary.PARAMETERS["nLines"] = int(lines)
                simLibrary.PARAMETERS["lowerMinuteMargin"] = int(lMargin)
                simLibrary.PARAMETERS["higherMinuteMargin"] = int(hMargin)
                simLibrary.PARAMETERS["securityMargin"] = int(secuMargin)
                simLibrary.PARAMETERS["upperTimeLimit"] = startHour
                simLibrary.PARAMETERS["lowerTimeLimit"] = endHour

                # Execute simulation logic
                limits = simLibrary.set_time_limit(simLibrary.PARAMETERS["format"])
                tripTuple = simLibrary.generate_trip(simLibrary.PARAMETERS["trip"])

                dbl.delete_collection(dbl.select_collection("trainLines", "TFG"))
                simLibrary.generate_lines(
                    tripTuple, simLibrary.PARAMETERS["minStations"]
                )
                simLibrary.generate_timetable(limits, tripTuple)

                time.sleep(2)
                messages.success(request, "Simulation generated successfully.")
                return redirect("simulator")

            except ValueError as e:
                messages.error(request, f"Incorrect data: {e}")
                return redirect("simulator")

            except Exception as e:
                messages.error(request, f"An unexpected error occurred: {e}")
                return redirect("simulator")

    # --- GET REQUEST (Page Load) ---
    trip = request.session.get("trip")
    startHour = request.session.get("startHour")
    endHour = request.session.get("endHour")
    lines = request.session.get("lines")
    secuMargin = request.session.get("secuMargin")

    # Fetch raw data from MongoDB
    trainLinesDataRaw = list(
        dbl.select_collection("trainLines", "TFG").find({}, {"_id": 0})
    )
    trainLinesData = []

    for line in trainLinesDataRaw:
        formattedDepartures = []
        formattedArrivals = []

        if "Timetable_Margins" in line and line["Timetable_Margins"]:
            departures = line["Timetable_Margins"][0]
            arrivals = line["Timetable_Margins"][1]

            for hour in departures:
                formattedDepartures.append(simLibrary.visual_hour_format(hour))

            for hour in arrivals:
                formattedArrivals.append(simLibrary.visual_hour_format(hour))

        trainLinesData.append(
            {
                "Lines": line.get("Lines"),
                "Stations": line.get("Stations"),
                "Timetable": line.get("Timetable"),
                "Departures": formattedDepartures,
                "Arrivals": formattedArrivals,
            }
        )

    occupation = request.session.get("ocupation", None)

    return render(
        request,
        "railSimulator/simulation.html",
        {
            "trip": trip,
            "startHour": startHour,
            "endHour": endHour,
            "lines": lines,
            "secuMargin": secuMargin,
            "train_lines": trainLinesData,
            "timestamp": datetime.now().timestamp(),
            "ocupation": occupation,
        },
    )


def generate_capacity(request):
    """
    Handles the calculation of network capacity between two stations
    within a specific time range.
    """
    if request.method == "POST":
        try:
            # 1. Retrieve form inputs
            stOrg = request.POST.get("stationOrg")
            stEnd = request.POST.get("stationEnd")
            start = request.POST.get("startHourCapacity")
            end = request.POST.get("endHourCapacity")

            if not all([stOrg, stEnd, start, end]):
                raise ValueError("All fields are mandatory.")

            # 2. Call to capacity core logic
            result = cp.generate_selected_tt(stOrg, stEnd, start, end)

            # 3. Save result in session
            request.session["ocupation"] = result
            messages.success(request, f"Capacity calculated: {result}%")

        except ValueError as e:
            messages.error(request, f"Invalid data: {e}")
            request.session["ocupation"] = None

        except Exception as e:
            messages.error(request, f"System error: {e}")
            request.session["ocupation"] = None

    return redirect("simulator")


def home(request):
    """
    Renders the home page of the application.
    """
    return render(request, "railSimulator/home.html")
