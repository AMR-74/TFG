from pymongo import MongoClient

client = MongoClient("mongodb+srv://albertoml2000:ik3x1booKcfJ64De@clustertfgamr.5sbnm.mongodb.net/")

def getDatabase(db:str):  
    return client[db]

def dbInputsTL(line:int, stations:list, timetable:list, timetableMargins:list, db:str):
    db = getDatabase(db)
    collection = db["trainLines"]
    collection.insert_one({"Linea":line, "Stations":stations, "Timetable":timetable, "Timetable_Margins": timetableMargins})

def dbInputsSL(station:str, times:list, db:str):
    db = getDatabase(db)
    collection = db["simulationLines"]
    collection.insert_one({"Station":station, "Hours":times})

def selectCollection(collection:str, db:str):
    db = getDatabase(db)
    return db[collection]

def readCollection(collection):
    return collection.find()

def selectData(collection, property:str) -> list:
    return [data[property] for data in collection.find({}, {property:1, "_id":0})]

def modifyEntry(collection, id:dict, data:dict):
    collection.update_one(id, {"$set": data})

def deleteCollection(collection):
    collection.delete_many({})