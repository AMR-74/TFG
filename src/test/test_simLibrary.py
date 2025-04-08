import src.simLibrary as siml
import src.dbLibrary as dbl
from pymongo import MongoClient
import re
import random
from datetime import timedelta, datetime
import pytest

client = MongoClient("mongodb+srv://albertoml2000:ik3x1booKcfJ64De@clustertfgamr.5sbnm.mongodb.net/")

@pytest.fixture(scope="function", autouse=True)
def clean_test_db():
    """Limpia la base de datos antes de cada prueba."""
    client.drop_database(dbl.getDatabase('Test'))
    yield
    client.drop_database(dbl.getDatabase('Test'))

### PRUEBAS UNITARIAS DE FUNCIONES BÁSICAS ###

def test_changeSeed():
    random.seed(1)
    value1 = random.randint(1, 100)
    
    siml.changeSeed()
    value2 = random.randint(1, 100)

    assert value1 != value2  # La semilla cambia y los valores deben diferir

def test_checkFormat():
    valid_format = r"^(?:[01]\d|2[0-3]):[0-5]\d$"
    assert siml.checkFormat(valid_format, "12:30") is True
    assert siml.checkFormat(valid_format, "25:30") is False  # Hora inválida
    assert siml.checkFormat(valid_format, "abc") is False  # Texto inválido

def test_generateTrip():
    assert siml.generateTrip(5) == ('A', 'E')
    assert siml.generateTrip(1) == ('A', 'A')
    with pytest.raises(ValueError):
        siml.generateTrip(30)  # Excede el límite de 26 estaciones

def test_stationsDefault():
    assert siml.stationsDefault(('A', 'C')) == {'A': [], 'B': [], 'C': []}

def test_hourFormat():
    assert siml.hourFormat("14:30") == datetime.strptime("14:30", "%H:%M")

### PRUEBAS UNITARIAS DE FUNCIONES ESPECÍFICAS ###

def test_generateLines(mocker):
    mock_dbInputsTL = mocker.patch("src.dbLibrary.dbInputsTL")
    mock_changeSeed = mocker.patch("src.simLibrary.changeSeed")

    siml.parameters["nLines"] = 3
    siml.generateLines(("A", "E"))

    assert mock_dbInputsTL.call_count == 3
    for call in mock_dbInputsTL.call_args_list:
        args = call[0]
        assert len(args[1]) == 2  # Debe ser una tupla de dos elementos
        assert "A" <= args[1][0] < args[1][1] <= "E"

    try:
        siml.generateLines(("A", "A"))

    except ValueError as e:
        assert "Error de simulación, línea sin movimiento" in str(e)
        return

    assert False, "Error no detectado"

def test_setTimeLimit(mocker):
    mock_checkFormat = mocker.patch("src.simLibrary.checkFormat", return_value=True)
    mock_hourFormat = mocker.patch("src.simLibrary.hourFormat", side_effect=lambda x: datetime.strptime(x, "%H:%M"))

    siml.parameters["upperTimeLimit"] = "14:00"
    siml.parameters["lowerTimeLimit"] = "06:00"
    start, end = siml.setTimeLimit("%H:%M")

    assert start == datetime.strptime("14:00", "%H:%M")
    assert end == datetime.strptime("06:00", "%H:%M")

    mock_checkFormat.side_effect = [False, True]
    with pytest.raises(ValueError, match="Error en el formato de hora introducido."):
        siml.setTimeLimit("%H:%M")

    mock_checkFormat.side_effect = [True, False]
    with pytest.raises(ValueError, match="Error en el formato de hora introducido."):
        siml.setTimeLimit("%H:%M")

def test_marginsTimetable():
    siml.parameters["securityMargin"] = 5
    times = [datetime(2024, 2, 24, 10, 0), datetime(2024, 2, 24, 10, 30), datetime(2024, 2, 24, 11, 0)]

    expected_opt1 = [times[0], times[1] - timedelta(minutes=5), times[2] - timedelta(minutes=5)]
    assert siml.marginsTimetable(1, times, 1) == expected_opt1

    expected_opt2 = [times[0] + timedelta(minutes=5), times[1] + timedelta(minutes=5), times[2] + timedelta(minutes=5)]
    assert siml.marginsTimetable(2, times, 1) == expected_opt2

def test_generateTimetable(mocker):
    mock_selectData = mocker.patch("src.dbLibrary.selectData", side_effect=[
        ["L1", "L2"],  # Líneas de tren
        [["A", "B"], ["C", "D"]],  # Estaciones
        [[], []]  # Horarios vacíos (para simplificar)
    ])
    mock_modifyEntry = mocker.patch("src.dbLibrary.modifyEntry")
    mock_changeSeed = mocker.patch("src.simLibrary.changeSeed")

    limits = (datetime(2024, 2, 24, 6, 0), datetime(2024, 2, 24, 22, 0))
    trip = ("A", "D")

    siml.generateTimetable(limits, trip)

    assert mock_selectData.call_count == 3
    assert mock_modifyEntry.call_count > 0
