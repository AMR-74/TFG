import yaml as yml
import src.dbLibrary as dbl


#=== GLOBAL VARIABLES ===#

fileName = "./src/supply_data.yaml"

#=== FUNCTIONS ===#
def openYaml(name:str) -> dict:
    """
    Function to read .yaml files to study their capacity.

    Parameters:
    name(str): Name/route of the yaml file to read.

    Returns:
    dict: Data of the yaml file.
    """

    with open(name, 'r') as file:
        data = yml.safe_load(file)

    return data

def importData(file:dict) -> None:
    """
    Function to transfer data to the database used.

    Parameters:
    file(dict): Dictionary with the data contained in the yaml file.

    Returns:
    None
    """

    collection = dbl.selectCollection("trainLines", "TFG")
    dbl.deleteCollection(collection)
    stations = {}


    for i, station in enumerate(file["stations"]):
        stations[chr(ord("A") + i)] = [station["short_name"],station["id"]]

    
    simplifiedStation = list(stations.keys())

    for line in file["line"]:
        lineStations = []
        route = [stop["station"] for stop in line["stops"]]

        for i, stopStations in enumerate(stations):
            if stations[stopStations][1] == route[0]:
                lineStations.append(simplifiedStation[i])

            elif (stations[stopStations][1] == route[-1]) and len(lineStations) != 0:
                lineStations.append(simplifiedStation[i])

        dbl.dbInputsTL(line["id"],lineStations,[],[],"TFG",[])

importData(openYaml(fileName))