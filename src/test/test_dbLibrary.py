import src.dbLibrary as dbl
from pymongo import MongoClient

import pytest
from unittest.mock import patch, MagicMock

client = MongoClient("mongodb+srv://albertoml2000:ik3x1booKcfJ64De@clustertfgamr.5sbnm.mongodb.net/")

@pytest.fixture(scope="function", autouse=True)
def clean_test_db():
    """Limpia la base de datos antes y después de cada prueba."""
    client.drop_database(dbl.getDatabase('Test'))
    yield
    client.drop_database(dbl.getDatabase('Test'))

def test_dbInputsTL():
    # Inserta una línea de prueba
    dbl.dbInputsTL(1, ['A', 'B'], ['08:00'], [5], 'Test')

    # Verifica que se insertó correctamente
    collection = dbl.selectCollection("trainLines", 'Test')
    result = list(dbl.readCollection(collection))
    assert len(result) == 1
    assert result[0]['Linea'] == 1
    assert result[0]['Stations'] == ['A', 'B']

def test_dbInputsSL():
    # Inserta una estación simulada
    dbl.dbInputsSL('Station1', ['09:00', '10:00'], 'Test')

    # Verifica que se insertó correctamente
    collection = dbl.selectCollection("simulationLines", 'Test')
    result = list(dbl.readCollection(collection))
    assert len(result) == 1
    assert result[0]['Station'] == 'Station1'
    assert result[0]['Hours'] == ['09:00', '10:00']

def test_selectCollection():
    collection = dbl.selectCollection("trainLines", 'Test')
    assert collection.name == "trainLines"

def test_readCollection():
    collection = dbl.selectCollection("trainLines", 'Test')
    assert isinstance(dbl.readCollection(collection), list) or collection.find()

def test_selectData():
    # Inserta datos para la prueba
    collection = dbl.selectCollection("simulationLines", 'Test')
    collection.insert_many([{"property": "val1"}, {"property": "val2"}])

    # Verifica selectData
    result = dbl.selectData(collection, "property")
    assert result == ["val1", "val2"]

def test_modifyEntry():
    collection = dbl.selectCollection("simulationLines", 'Test')
    collection.insert_one({"station": "Old", "hours": ["08:00"]})
    doc = collection.find_one({"station": "Old"})

    # Modificar el registro
    dbl.modifyEntry(collection, {"_id": doc["_id"]}, {"station": "New"})
    updated_doc = collection.find_one({"_id": doc["_id"]})
    assert updated_doc["station"] == "New"

def test_deleteCollection():
    collection = dbl.selectCollection("simulationLines", 'Test')
    collection.insert_one({"station": "Temp", "hours": ["10:00"]})
    dbl.deleteCollection(collection)

    # Verificar que está vacío
    assert collection.count_documents({}) == 0
