from django.shortcuts import render, redirect
from django.http import JsonResponse

# Create your views here.
def simulator(request):
    if request.method == "POST":
        trip = request.POST.get("trip")
        startHour = request.POST.get("startHour")
        endHour = request.POST.get("endHour")
        lines = request.POST.get("lines")
        secuMargin = request.POST.get("secuMargin")

        request.session['trip'] = trip
        request.session['startHour'] = startHour
        request.session['endHour'] = endHour
        request.session['lines'] = lines
        request.session['secuMargin'] = secuMargin

        print(f"[DEBUG] T = {trip}")
        print(f"[DEBUG] SH = {startHour}")
        print(f"[DEBUG] EH = {endHour}")
        print(f"[DEBUG] L = {lines}")
        print(f"[DEBUG] SC = {secuMargin}")

        return redirect('simulator')
    
    trip = request.session.get('trip')
    startHour = request.session.get('startHour')
    endHour = request.session.get('endHour')
    lines = request.session.get('lines')
    secuMargin = request.session.get('secuMargin')

    return render(request, "railSimulator/simulation.html", 
    {
        "trip": trip, 
        "startHour": startHour,
        "endHour": endHour,
        "lines": lines,
        "secuMargin": secuMargin
    })

def home(request):
    return render(request, "railSimulator/home.html")




