from geopy.distance import geodesic
from robin.supply.entities import Supply
import src.dbLibrary as dbl

# === CONSTANTS ===
BLOCK_LONGITUDE_THRESHOLD = 50

# === FUNCTIONS ===


def get_station_data(fileName):
    """
    Retrieves station data from a YAML supply file.
    """
    supply = Supply.from_yaml(fileName)
    return supply.stations


def get_distance_data(inputData):
    """
    Extracts IDs and coordinates from station data objects.
    """
    return [(element.id, element.coordinates) for element in inputData]


def get_distances(fileName):
    """
    Calculates geodesic distances between stations for all train lines.
    """
    collection = dbl.read_collection(dbl.select_collection("trainLines", "TFG"))
    stationDataList = get_distance_data(get_station_data(fileName))
    distanceLinesList = []

    for line in collection:
        distances = []
        stationsIdList = line["StationsID"]
        for i, identifier in enumerate(stationsIdList):
            if i == 0:
                prevStation = identifier
            else:
                originCoord, destinyCoord = None, None
                for station in stationDataList:
                    if station[0] == identifier[1]:
                        destinyCoord = station[1]
                    elif station[0] == prevStation[1]:
                        originCoord = station[1]

                if originCoord and destinyCoord:
                    distances.append(geodesic(originCoord, destinyCoord).kilometers)
                prevStation = identifier
        distanceLinesList.append(distances)

    return distanceLinesList


def canton_divider(distancesList):
    """
    Divides track sections into blocks (cantons) based on segment length.
    """
    distancesLinesResult = []
    for line in distancesList:
        cantonsCount = [int((dist // BLOCK_LONGITUDE_THRESHOLD) + 5) for dist in line]
        distancesLinesResult.append(cantonsCount)
    return distancesLinesResult
