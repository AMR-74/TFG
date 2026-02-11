from pymongo import MongoClient

# MongoDB connection client
client = MongoClient("mongodb+srv://albertoml2000:ik3x1booKcfJ64De@clustertfgamr.5sbnm.mongodb.net/")

def getDatabase(db:str):  
    """
    Returns the database object for the specified name.
    """
    return client[db]

def dbInputsTL(line:int, stations:list, timetable:list, timetableMargins:list, db:str, compressedTt: list, stationsId:list):
    """
    Inserts train line data into the 'trainLines' collection.
    Replaced 'Linea' with 'Lines' for consistency.
    """
    db = getDatabase(db)
    collection = db["trainLines"]
    collection.insert_one({
        "Lines": line, 
        "Stations": stations, 
        "Timetable": timetable, 
        "Timetable_Margins": timetableMargins, 
        "Compressed_Timetable": compressedTt, 
        "StationsID": stationsId
    })

def dbInputsSL(station:str, times:list, db:str):
    """
    Inserts simulation line data for a specific station.
    """
    db = getDatabase(db)
    collection = db["simulationLines"]
    collection.insert_one({"Station": station, "Hours": times})

def selectCollection(collection:str, db:str):
    """
    Retrieves a specific collection from a database.
    """
    db = getDatabase(db)
    return db[collection]

def readCollection(collection):
    """
    Returns a cursor with all documents in the collection.
    """
    return collection.find()

def selectData(collection, property:str) -> list:
    """
    Returns a list of values for a specific property from the collection.
    """
    return [data[property] for data in collection.find({}, {property:1, "_id":0})]

def modifyEntry(collection, id:dict, data:dict):
    """
    Updates a single document based on the filter provided.
    """
    collection.update_one(id, {"$set": data})

def deleteCollection(collection):
    """
    Deletes all documents in a collection.
    """
    collection.delete_many({})