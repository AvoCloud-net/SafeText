import pytest
from quart import Quart, jsonify, request
from server import check_chatfilter, check_user_db, load_badwords, load_goodwords, load_ids
import json


# Dummy Daten für Tests
badwords = ["badword1", "badword2", "badword3"]
goodwords = ["goodword1", "goodword2"]
ids_list = {
    "123": {"name": "Test User", "id": 123, "reason": "spamming"},
    "456": {"name": "Another User", "id": 456, "reason": "offensive language"}
}


@pytest.fixture
def app():
    # Erstelle eine Quart-App für Testzwecke
    app = Quart(__name__)

    # Die Test-Routen einbinden
    @app.route('/chatfilter', methods=['POST'])
    async def check_message():
        data = await request.get_json()
        message = data['message']
        results = check_chatfilter(message, badwords, goodwords)
        return jsonify(results)

    @app.route('/user', methods=['POST'])
    async def check_user():
        data = await request.get_json()
        user_id = data['id']
        result = check_user_db(int(user_id), ids_list)
        return jsonify(result)

    yield app


@pytest.mark.asyncio
async def test_check_chatfilter(app):
    # Teste die Chatfilter-Logik
    client = await app.test_client()

    # Test mit einem ungültigen Wort
    response = await client.post('/chatfilter', json={"message": "This is a badword1"})
    data = await response.get_json()
    assert "input_word" in data
    assert data["input_word"] == "badword1"

    # Test ohne schlechte Wörter
    response = await client.post('/chatfilter', json={"message": "This is a goodword1"})
    data = await response.get_json()
    assert not data


@pytest.mark.asyncio
async def test_check_user(app):
    # Teste die Nutzerabfrage
    client = await app.test_client()

    # Test für einen bekannten Nutzer
    response = await client.post('/user', json={"id": 123})
    data = await response.get_json()
    assert data["name"] == "Test User"
    assert data["flagged"] is True

    # Test für einen unbekannten Nutzer
    response = await client.post('/user', json={"id": 999})
    data = await response.get_json()
    assert data["flagged"] is False
    assert data["name"] is None


def test_load_badwords():
    # Teste das Laden der badwords.json-Datei
    with open("badwords.json", "w", encoding="utf-8") as file:
        json.dump(badwords, file)
    loaded_badwords = load_badwords()
    assert loaded_badwords == badwords


def test_load_goodwords():
    # Teste das Laden der goodwords.json-Datei
    with open("goodwords.json", "w", encoding="utf-8") as file:
        json.dump(goodwords, file)
    loaded_goodwords = load_goodwords()
    assert loaded_goodwords == goodwords


def test_load_ids():
    # Teste das Laden der ids.json-Datei
    with open("ids.json", "w", encoding="utf-8") as file:
        json.dump(ids_list, file)
    loaded_ids = load_ids()
    assert loaded_ids == ids_list
