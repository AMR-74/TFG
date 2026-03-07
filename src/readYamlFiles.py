import yaml as yml
import src.dbLibrary as dbl
import src.generateDiagram as gd
from robin.supply.entities import Supply
import src.cantonCalculator as cc
from datetime import timedelta, datetime


def get_simplified_station(stationName, stationsList, dictStationsWork, stationsId):
    """
    Maps real station names to simplified IDs (A, B, C...).
    """
    for simplifiedStation in dictStationsWork:
        if dictStationsWork[simplifiedStation][0] == stationName:
            stationsId.append((simplifiedStation, stationName))
            stationsList.append(simplifiedStation)
    return stationsId


def import_data(fileName):
    """
    Reads a YAML file and imports train services into the database.
    Uses 'Lines' as the primary key field.
    """
    supply = Supply.from_yaml(fileName)
    baseDate = datetime(1900, 1, 1)
    collection = dbl.select_collection("trainLines", "TFG")
    dbl.delete_collection(collection)

    dictStations = supply.corridors[0].stations
    dictStationsWork = {
        chr(ord("A") + i): [clave] for i, clave in enumerate(dictStations)
    }

    for service in supply.services:
        departures, arrivals, stations, stationsId = [], [], [], []
        prevStation = None

        for i, station in enumerate(service.schedule):
            get_simplified_station(station, stations, dictStationsWork, stationsId)
            if i > 0:
                departures.append(baseDate + service.schedule[prevStation][0])
                arrivals.append(baseDate + service.schedule[station][1])
            prevStation = station

        # Insert using 'Lines' instead of 'Linea'
        dbl.db_inputs_tl(
            service.id, stations, [], [departures, arrivals], "TFG", [], stationsId
        )

    distancesLines = cc.get_distances(fileName)
    cantonLines = cc.canton_divider(distancesLines)
    gd.generate_diagram(2, cantonLines)
