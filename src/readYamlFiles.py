import yaml as yml
import src.dbLibrary as dbl
import src.generateDiagram as gd
from robin.supply.entities import Supply
import src.cantonCalculator as cc
from datetime import timedelta, datetime

def getSimplifiedStation(station:str, stations:list, dictStationsWork:dict, stationsId:list):
    """
    Maps real station names to simplified IDs (A, B, C...).
    """
    for simplifiedStation in dictStationsWork:
        if dictStationsWork[simplifiedStation][0] == station:
            stationsId.append((simplifiedStation, station))
            stations.append(simplifiedStation)
    return stationsId

def importData(name:str) -> None:
    """
    Reads a YAML file and imports train services into the database.
    Uses 'Lines' as the primary key field.
    """
    supply = Supply.from_yaml(name)
    base = datetime(1900, 1, 1)
    collection = dbl.selectCollection("trainLines", "TFG")
    dbl.deleteCollection(collection)

    dictStations = supply.corridors[0].stations
    dictStationsWork = {chr(ord('A') + i): [clave] for i, clave in enumerate(dictStations)}

    for service in supply.services:
        departures, arrivals, stations, stationsId = [], [], [], []
        prevStation = None

        for i, station in enumerate(service.schedule):
            getSimplifiedStation(station, stations, dictStationsWork, stationsId)
            if i > 0:
                departures.append(base + service.schedule[prevStation][0])
                arrivals.append(base + service.schedule[station][1])
            prevStation = station
        
        # Insert using Lines instead of Linea
        dbl.dbInputsTL(service.id, stations, [], [departures, arrivals], "TFG", [], stationsId)

    distances_lines = cc.getDistances(name)
    canton_lines = cc.cantonDivider(distances_lines)
    gd.generateDiagram(2, canton_lines)