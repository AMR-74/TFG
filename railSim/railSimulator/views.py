from django.shortcuts import render

# Create your views here.
def simulator(request):
    return render(request, "railSimulator/simulation.html")

def home(request):
    return render(request, "railSimulator/home.html")