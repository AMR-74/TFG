from geopy.distance import geodesic
from robin.supply.entities import Supply
import src.dbLibrary as dbl

#=== GLOBAL VARIABLES ===#
name = "C:/Users/alber/Desktop/supply_data.yaml"

#=== FUNCTIONS ===#
def getStationData(name:str) -> dict:
    supply = Supply.from_yaml(name)
    stationData = supply.stations

    return stationData

def getDistanceData(data:tuple) -> float:
    processedStationData = []
    for element in data:
        processedStationData.append((element.id, element.coordinates))

    return processedStationData

def getUsedStationsID() -> list:
    collection = dbl.readCollection(dbl.selectCollection("trainLines", "TFG"))
    stationData = getDistanceData(getStationData(name))
    distances = []
    distanceLines = []
    for line in collection:
        stationsId = line["StationsID"]
        for i, identifier in enumerate(stationsId):
            if i == 0:
                prevStation = identifier

            else:
                for j in stationData:
                    if j[0] == identifier[1]:
                        destiny = j[1]

                    elif j[0] == prevStation[1]:
                        origin = j[1]
                    
                    else:
                        pass
                distance = geodesic(origin, destiny).kilometers
                distances.append(distance)
                prevStation = identifier
        
        distanceLines.append(distances)
        distances = []

    return distanceLines

print(getUsedStationsID())