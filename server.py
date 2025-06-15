import os
import quart
import json
import reds_simple_logger
import colorama
import sys
import time
import string
from quart import Quart, request
from colorama import Fore, Style
from Levenshtein import distance
from typing import Optional, List
import hashlib
import time
import uuid
import datetime


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


def check_chatfilter(
    input_str: str,
    badwords: List[str],
    goodwords: List[str],
    c_badwords: Optional[List[str]] = None,
    c_goodwords: Optional[List[str]] = None,
    cid: int = 0,
    gid: int = 0
):
    import string

    if c_badwords is None:
        c_badwords = []
    if c_goodwords is None:
        c_goodwords = []

    threshold = 1
    input_data = input_str.lower().replace("”", " ").replace("“", " ").split()

    badwords = [w.lower() for w in badwords]
    goodwords = [w.lower() for w in goodwords]
    c_badwords = [w.lower() for w in c_badwords]
    c_goodwords = [w.lower() for w in c_goodwords]

    for word in input_data:
        cleaned_word = word.strip(string.punctuation)

        if cleaned_word in goodwords or cleaned_word in c_goodwords:
            continue

        best_match = None
        best_distance = float("inf")

        for badword in badwords + c_badwords:
            current_distance = distance(cleaned_word, badword)

            if current_distance <= threshold and current_distance < best_distance:
                best_match = {
                    "input_word": cleaned_word,
                    "matched_badword": badword,
                    "distance": current_distance,
                    "cid": cid,
                    "gid": gid
                }
                best_match["code"] = "custom" if badword in c_badwords else "internal"
                best_distance = current_distance

        if best_match:
            return best_match

    return {}


def check_user_db(input_id: int, ids_list):
    rt_data = {}
    name: str = ""
    id: int = input_id
    reason: str = ""
    flagged: bool = False
    entry_date: str = ""

    if str(input_id) in ids_list:
        name: str = ids_list[str(input_id)]["name"]
        id: int = ids_list[str(input_id)]["id"]
        reason: str = ids_list[str(input_id)]["reason"]
        entry_date: str = ids_list[str(input_id)]["entry_date"]
        flagged: bool = True

    rt_data = {"name": name, "id": id, "reason": reason,
               "flagged": flagged, "entry_date": entry_date}

    return rt_data


def hash_string(string: str):
    hashed = hashlib.sha256(string.encode()).hexdigest()
    return hashed


@server.route("/", methods=["GET", "POST"])
async def home():
    return "SafeText API online!"


@server.route("/chatfilter", methods=["GET", "POST"])
async def check_message():
    start_time = time.time()
    id = os.urandom(15).hex()
    logger.info(f"Start processing order number chatfilter-{id}")

    data = await request.get_json(silent=True)

    if not data:
        return {"error": "No JSON payload received"}, 400

    badwords_data = load_data("json/badwords.json")
    goodwords_data = load_data("json/goodwords.json")

    badwords = badwords_data.get("badwords", []) if isinstance(
        badwords_data, dict) else badwords_data
    goodwords = goodwords_data.get("goodwords", []) if isinstance(
        goodwords_data, dict) else goodwords_data

    key_hash_list = load_data("json/key_hash.json")

    key = data.get("key")
    if not key or hash_string(key) not in key_hash_list:
        return {"error": "access denied"}, 403

    message = data.get("message", "")
    c_badwords = data.get("c_badwords", [])
    c_goodwords = data.get("c_goodwords", [])

    cid = data.get("cid", 0)
    gid = data.get("gid", 0)

    results = check_chatfilter(
        message, badwords, goodwords, c_badwords, c_goodwords, cid, gid)

    end_time = time.time()
    processing_time = end_time - start_time

    if results:
        logger.info(f"chatfilter-{id} marked as SPAM.")
    logger.success(
        f"Processing of order number chatfilter-{id} in {processing_time:.3f}s completed.")

    return results


@server.route("/user", methods=["GET", "POST"])
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
    if result["flagged"]:
        logger.info(f"user-{id}: user is FLAGGED.")
    logger.success(
        f"Processing of order number user-{id} in {processing_time}s completed."
    )

    return result


@server.route("/flagg_user", methods=["GET", "POST"])
async def add_flagged_user():
    data = await request.get_json()
    admin_key_hash_list = load_data("json/admin_key_hash.json")
    ids_list = load_data("json/ids.json")
    if hash_string(data["key"]) not in admin_key_hash_list:
        return {"error": "access denied"}, 401

    user_id = data["id"]
    user_name = data["name"]
    reason = data["reason"]

    if str(user_id) in ids_list:
        return {"success": False, "message": "User already in Database!"}
    else:
        ids_list[str(user_id)] = {
            "id": int(user_id),
            "name": str(user_name),
            "reason": str(reason),
            "entry_date": str(datetime.date.today()),
            "flagged": True,
        }

        save_data("json/ids.json", ids_list)
        return {"success": True, "message": "Used was flagged"}


@server.route("/deflag_user", methods=["GET", "POST"])
async def remove_flagged_user():
    data = await request.get_json()
    admin_key_hash_list = load_data("json/admin_key_hash.json")
    ids_list = load_data("json/ids.json")
    if hash_string(data["key"]) not in admin_key_hash_list:
        return {"error": "access denied"}

    user_id = data["id"]

    if str(user_id) in ids_list:
        del ids_list[str(user_id)]
        save_data("json/ids.json", ids_list)
        return {"success": True, "message": "Used was deflagged"}
    else:
        return {"success": False, "message": "User not flagged!"}


if __name__ == "__main__":

    server.run(host="0.0.0.0", port=1652)
