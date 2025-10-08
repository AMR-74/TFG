import yaml as yml
import src.dbLibrary as dbl
import src.generateDiagram as gd
from robin.supply.entities import Supply
import src.cantonCalculator as cc
from datetime import timedelta, datetime


#=== GLOBAL VARIABLES ===#

#=== FUNCTIONS ===#
def getSimplifiedStation(station:str, stations:list, dictStationsWork:dict, stationsId:list):
    for simplifiedStation in dictStationsWork:
            if dictStationsWork[simplifiedStation][0] == station:
                stationsId.append((simplifiedStation, station))
                stations.append(simplifiedStation)
    return stationsId


def importData(name:str) -> None:
    """
    Function to transfer data to the database used.

    Parameters:
    file

    Returns:
    None
    """

    supply = Supply.from_yaml(name)
    stations = supply.stations
    base = datetime(1900, 1, 1)

    collection = dbl.selectCollection("trainLines", "TFG")
    dbl.deleteCollection(collection)

    stationsCorridor = supply.corridors
    dictStations = stationsCorridor[0].stations
    dictStationsWork = {}
    departures = []
    arrivals = []
    stations = []
    stationsId = []
    prevStation = None

    for i, clave in enumerate(dictStations):
        dictStationsWork[chr(ord('A') + i)] = [clave]

    for service in supply.services:
        for i, station in enumerate(service.schedule):
            if i == 0:
                origin = station
                prevStation =  station
                getSimplifiedStation(station, stations, dictStationsWork, stationsId)

            else:
                departures.append(base + service.schedule[prevStation][0])
                arrivals.append(base + service.schedule[station][1])
                prevStation = station
                getSimplifiedStation(station, stations, dictStationsWork, stationsId)
        
        dbl.dbInputsTL(service.id, stations, [], [departures, arrivals], "TFG", [], stationsId)
        stations = []
        stationsId = []
        departures = []
        arrivals = []

    distances_lines = cc.getDistances(name)                 # usa el YAML recién subido
    canton_lines = cc.cantonDivider(distances_lines)        # cantones por tramo
    gd.generateDiagram(2, canton_lines)                     # pásalo al diagrama

    

