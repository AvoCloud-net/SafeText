import pytest
from quart import Quart, jsonify, request
from server import (
    check_chatfilter,
    check_user_db,
    save_data,
    load_data
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
        cid = 123
        sid = 123
        results = check_chatfilter(input_str=message, badwords=badwords, goodwords=goodwords, cid=cid, sid=sid)
        return jsonify(results)

    @app.route("/user", methods=["POST"])
    async def check_user():
        data = await request.get_json()
        user_id = data["id"]
        result = check_user_db(int(user_id), ids_list)
        return jsonify(result)

    @app.route("/flagg_user", methods=["POST"])
    async def add_flagged_user():
        data = await request.get_json()
        user_id = data["id"]
        user_name = data["name"]
        reason = data["reason"]

        if str(user_id) in ids_list:
            return jsonify({"success": False, "message": "User already in Database!"})
        else:
            ids_list[str(user_id)] = {
                "id": int(user_id),
                "name": str(user_name),
                "reason": str(reason),
                "flagged": True
            }
            return jsonify({"success": True, "message": "User was flagged"})

    @app.route("/deflag_user", methods=["POST"])
    async def remove_flagged_user():
        data = await request.get_json()
        user_id = data["id"]

        if str(user_id) in ids_list:
            del ids_list[str(user_id)]
            return jsonify({"success": True, "message": "User was deflagged"})
        else:
            return jsonify({"success": False, "message": "User not flagged!"})

    yield app


# Chatfilter Test
@pytest.mark.asyncio
async def test_check_chatfilter(app):
    client = app.test_client()

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
    client = app.test_client()

    response = await client.post("/user", json={"id": 123})
    data = await response.get_json()
    assert data["id"] == 123
    assert data["name"] == "Test User"
    assert data["flagged"] is True

    response = await client.post("/user", json={"id": 999})
    data = await response.get_json()
    assert data["flagged"] is False
    assert data["name"] is None


# Admin Endpoints Tests
@pytest.mark.asyncio
async def test_flag_user(app):
    client = app.test_client()

    # Benutzer flaggen, der nicht in der Datenbank ist
    response = await client.post("/flagg_user", json={"id": 789, "name": "New User", "reason": "test reason"})
    data = await response.get_json()
    assert data["success"] is True
    assert data["message"] == "User was flagged"

    # Versuchen, denselben Benutzer erneut zu flaggen
    response = await client.post("/flagg_user", json={"id": 789, "name": "New User", "reason": "test reason"})
    data = await response.get_json()
    assert data["success"] is False
    assert data["message"] == "User already in Database!"


@pytest.mark.asyncio
async def test_deflag_user(app):
    client = app.test_client()

    # Benutzer, der bereits in der Datenbank ist, deflaggen
    response = await client.post("/deflag_user", json={"id": 123})
    data = await response.get_json()
    assert data["success"] is True
    assert data["message"] == "User was deflagged"

    # Versuchen, einen Benutzer zu deflaggen, der nicht in der Datenbank ist
    response = await client.post("/deflag_user", json={"id": 999})
    data = await response.get_json()
    assert data["success"] is False
    assert data["message"] == "User not flagged!"
