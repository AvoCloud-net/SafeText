import quart, json, reds_simple_logger, colorama, sys, time, string
from quart import Quart, request
from colorama import Fore, Style
from Levenshtein import distance

print(Fore.MAGENTA, "Programm developed by Red_wolf2467")
print(Fore.MAGENTA, "Starting up chatfilter server...")
print(Fore.RESET, "")
server = Quart(__name__)
logger = reds_simple_logger.Logger()  #
logger.info("Server init complete! Continuing startup...")


def load_badwords():
    with open("badwords.json", "r", encoding="utf-8") as badwords_file:
        return json.load(badwords_file)


def load_goodwords():
    with open("goodwords.json", "r", encoding="utf-8") as goodwords_file:
        return json.load(goodwords_file)


def load_ids():
    with open("ids.json", "r", encoding="utf-8") as ids_list:
        return json.load(ids_list)


logger.working("Loading badwords.json...")
try:
    badwords = load_badwords()
    logger.success("Loaded badwords.json")
except Exception as e:
    logger.error("Failed to load badwords.json\n" + str(e))
    sys.exit(0)

logger.working("Loading goodwords.json...")
try:
    goodwords = load_goodwords()
    logger.success("Loaded goodwords.json")
except Exception as e:
    logger.error("Failed to load goodwords.json\n" + str(e))
    sys.exit(0)

logger.working("Loading ids.json...")
try:
    ids_list = load_ids()
    logger.success("Loaded ids.json")
except Exception as e:
    logger.error("Failed to load ids.json\n" + str(e))
    sys.exit(0)


def check_chatfilter(input_str: str, badwords, goodwords):
    threshold: int = 1 if len(input_str) < 50 else 2
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


@server.route("/chatfilter")
async def check_message():
    data = await request.get_json()

    message = data["message"]
    results = check_chatfilter(message, badwords, goodwords)

    return results


@server.route("/user")
async def check_user():
    data = await request.get_json()

    user_id = data["id"]

    result = check_user_db(int(user_id), ids_list)

    return result


if __name__ == "__main__":

    server.run(host="0.0.0.0", port=1652)
