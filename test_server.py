import pytest
from quart import Quart, jsonify, request
from server import (
    check_chatfilter,
    check_user_db
)


badwords = ["badword1", "badword2", "badword3"]
goodwords = ["goodword1", "goodword2"]
ids_list = {
    "123": {"name": "Test User", "id": 123, "reason": "spamming"},
    "456": {"name": "Another User", "id": 456, "reason": "offensive language"},
}


# Quart Test App
@pytest.fixture
def app():

    app = Quart(__name__)

    @app.route("/chatfilter", methods=["POST"])
    async def check_message():
        data = await request.get_json()
        message = data["message"]
        results = check_chatfilter(message, badwords, goodwords)
        return jsonify(results)

    @app.route("/user", methods=["POST"])
    async def check_user():
        data = await request.get_json()
        user_id = data["id"]
        result = check_user_db(int(user_id), ids_list)
        return jsonify(result)

    yield app


# Chatfilter Test
@pytest.mark.asyncio
async def test_check_chatfilter(app):
    client = await app.test_client()

    response = await client.post("/chatfilter", json={"message": "This is a badword1"})
    data = await response.get_json()
    assert "input_word" in data
    assert data["input_word"] == "badword1"

    response = await client.post("/chatfilter", json={"message": "This is a goodword1"})
    data = await response.get_json()
    assert not data


# User Test
@pytest.mark.asyncio
async def test_check_user(app):
    client = await app.test_client()

    response = await client.post("/user", json={"id": 123})
    data = await response.get_json()
    assert data["id"] == 123
    assert data["name"] == "Test User"
    assert data["flagged"] is True

    response = await client.post("/user", json={"id": 999})
    data = await response.get_json()
    assert data["flagged"] is False
    assert data["name"] is None


