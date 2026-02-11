from geopy.distance import geodesic
from robin.supply.entities import Supply
import src.dbLibrary as dbl

def getStationData(name:str) -> dict:
    """
    Retrieves station data from a YAML supply file.
    """
    supply = Supply.from_yaml(name)
    return supply.stations

def getDistanceData(data:tuple) -> list:
    """
    Extracts IDs and coordinates from station data objects.
    """
    return [(element.id, element.coordinates) for element in data]

def getDistances(name:str) -> list:
    """
    Calculates geodesic distances between stations for all train lines.
    """
    collection = dbl.readCollection(dbl.selectCollection("trainLines", "TFG"))
    stationData = getDistanceData(getStationData(name))
    distanceLines = []

    for line in collection:
        distances = []
        stationsId = line["StationsID"]
        for i, identifier in enumerate(stationsId):
            if i == 0:
                prevStation = identifier
            else:
                origin, destiny = None, None
                for j in stationData:
                    if j[0] == identifier[1]: destiny = j[1]
                    elif j[0] == prevStation[1]: origin = j[1]
                
                if origin and destiny:
                    distances.append(geodesic(origin, destiny).kilometers)
                prevStation = identifier
        distanceLines.append(distances)

    return distanceLines

def cantonDivider(distances:list):
    """
    Divides track sections into blocks (cantons) based on segment length.
    """
    longitude = 50
    distancesLines = []
    for line in distances:
        cantons = [int((dist // longitude) + 5) for dist in line]
        distancesLines.append(cantons)
    return distancesLines