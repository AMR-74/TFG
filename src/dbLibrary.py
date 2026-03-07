from pymongo import MongoClient

# === GLOBAL CONSTANTS ===
# MongoDB connection client
MONGO_CLIENT = MongoClient(
    "mongodb+srv://albertoml2000:ik3x1booKcfJ64De@clustertfgamr.5sbnm.mongodb.net/"
)


def get_database(dbName):
    """
    Returns the database object for the specified name.
    """
    return MONGO_CLIENT[dbName]


def db_inputs_tl(
    lineId,
    stationsList,
    timetableList,
    timetableMargins,
    dbName,
    compressedTt,
    stationsId,
):
    """
    Inserts train line data into the 'trainLines' collection.
    Replaced 'Linea' with 'Lines' for consistency.
    """
    database = get_database(dbName)
    collection = database["trainLines"]
    collection.insert_one(
        {
            "Lines": lineId,
            "Stations": stationsList,
            "Timetable": timetableList,
            "Timetable_Margins": timetableMargins,
            "Compressed_Timetable": compressedTt,
            "StationsID": stationsId,
        }
    )


def db_inputs_sl(stationName, timesList, dbName):
    """
    Inserts simulation line data for a specific station.
    """
    database = get_database(dbName)
    collection = database["simulationLines"]
    collection.insert_one({"Station": stationName, "Hours": timesList})


def select_collection(collectionName, dbName):
    """
    Retrieves a specific collection from a database.
    """
    database = get_database(dbName)
    return database[collectionName]


def read_collection(collectionObject):
    """
    Returns a cursor with all documents in the collection.
    """
    return collectionObject.find()


def select_data(collectionObject, propertyName):
    """
    Returns a list of values for a specific property from the collection.
    """
    return [
        data[propertyName]
        for data in collectionObject.find({}, {propertyName: 1, "_id": 0})
    ]


def modify_entry(collectionObject, filterId, updateData):
    """
    Updates a single document based on the filter provided.
    """
    collectionObject.update_one(filterId, {"$set": updateData})


def delete_collection(collectionObject):
    """
    Deletes all documents in a collection.
    """
    collectionObject.delete_many({})
