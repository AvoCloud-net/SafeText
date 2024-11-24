import os
import quart, json, reds_simple_logger, colorama, sys, time, string
from quart import Quart, request
from colorama import Fore, Style
from Levenshtein import distance
import hashlib, time, uuid

print(Fore.MAGENTA, "Programm developed by Red_wolf2467")
print(Fore.MAGENTA, "Starting up chatfilter server...")
print(Fore.RESET, "")
server = Quart(__name__)
logger = reds_simple_logger.Logger()
logger.info("Server init complete! Continuing startup...")


def load_data(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        return {}


def save_data(file_path, data):
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


files_and_functions = [
    ("json/badwords.json", load_data, save_data),
    ("json/goodwords.json", load_data, save_data),
    ("json/ids.json", load_data, save_data),
    ("json/key_hash.json", load_data, save_data),
    ("json/admin_key_hash.json", load_data, save_data),
]


def check_chatfilter(input_str: str, badwords, goodwords, cid: int, gid: int):
    threshold: int = 1 if len(input_str) < 150 else 2
    input_data = input_str.lower().split()

    for word in input_data:
        cleaned_word = word.strip(string.punctuation)

        if cleaned_word in goodwords:
            continue

        best_match = None
        best_distance = float("inf")

        for badword in badwords:
            current_distance = distance(cleaned_word, badword)
            if current_distance <= threshold and current_distance < best_distance:
                best_match = {
                    "input_word": cleaned_word,
                    "matched_badword": badword,
                    "distance": current_distance,
                    "cid": cid,
                    "gid": gid
                }
                best_distance = current_distance

        if best_match:
            return best_match

    return {}


def check_user_db(input_id: int, ids_list):
    rt_data = {}
    name: str = None
    id: int = input_id
    reason: str = None
    flagged: bool = False

    if str(input_id) in ids_list:
        name: str = ids_list[str(input_id)]["name"]
        id: int = ids_list[str(input_id)]["id"]
        reason: str = ids_list[str(input_id)]["reason"]
        flagged: bool = True

    rt_data = {"name": name, "id": id, "reason": reason, "flagged": flagged}

    return rt_data


def hash_string(string: str):
    hashed = hashlib.sha256(string.encode()).hexdigest()
    return hashed


@server.route("/chatfilter")
async def check_message():
    print("")
    start_time = time.time()
    id = os.urandom(15).hex()
    logger.info(f"Start processing order number chatfilter-{id}")
    data = await request.get_json()
    badwords = load_data("json/badwords.json")
    goodwords = load_data("json/goodwords.json")
    key_hash_list = load_data("json/key_hash.json")
    if hash_string(data["key"]) not in key_hash_list:
        return {"error": "access denied"}

    message = data["message"]
    try:
        cid = data["cid"]
        gid = data["gid"]
    except:
        cid = None
        gid = None
    results = check_chatfilter(message, badwords, goodwords, cid, gid)

    end_time = time.time()
    processing_time = end_time - start_time
    logger.info(
        f"Processing of order number chatfilter-{id} in {processing_time}s completed."
    )

    return results


@server.route("/user")
async def check_user():
    print("")
    start_time = time.time()
    id = os.urandom(15).hex()
    logger.info(f"Start processing order number user-{id}")
    data = await request.get_json()
    key_hash_list = load_data("json/key_hash.json")
    ids_list = load_data("json/ids.json")
    if hash_string(data["key"]) not in key_hash_list:
        return {"error": "access denied"}

    user_id = data["id"]

    result = check_user_db(int(user_id), ids_list)

    end_time = time.time()
    processing_time = end_time - start_time
    logger.info(
        f"Processing of order number user-{id} in {processing_time}s completed."
    )

    return result


@server.route("/flagg_user")
async def add_flagged_user():
    data = await request.get_json()
    admin_key_hash_list = load_data("json/admin_key_hash.json")
    ids_list = load_data("json/ids.json")
    if hash_string(data["key"]) not in admin_key_hash_list:
        return {"error": "access denied"}

    user_id = data[str(user_id)]["id"]
    user_name = data[str(user_id)]["name"]
    reason = data[str(user_id)]["reason"]

    if str(user_id) in ids_list:
        return {"success": False, "message": "User already in Database!"}
    else:
        ids_list[str(user_id)] = {
            "id": int(user_id),
            "name": str(user_name),
            "reason": str(reason),
            "flagged": bool(True),
        }
        save_data("json/ids.json", ids_list)
        return {"success": True, "message": "Used was flagged"}


@server.route("/deflag_user")
async def remove_flagged_user():
    data = await request.get_json()
    admin_key_hash_list = load_data("json/admin_key_hash.json")
    ids_list = load_data("json/ids.json")
    if hash_string(data["key"]) not in admin_key_hash_list:
        return {"error": "access denied"}

    user_id = data[str(user_id)]["id"]

    if str(user_id) in ids_list:
        del ids_list[str(user_id)]
        save_data("json/ids.json", ids_list)
        return {"success": True, "message": "Used was deflagged"}
    else:
        return {"success": False, "message": "User not flagged!"}


if __name__ == "__main__":

    server.run(host="0.0.0.0", port=1652)
