import quart, json, reds_simple_logger, colorama, sys, time
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


def check_chatfilter(input_str: str, badwords, goodwords, threshold=2):
    input_data = input_str.lower().split()
    flagged_words = []

    for word in input_data:
        if word in goodwords:
            continue
        
        best_match = None
        best_distance = float('inf')

        for badword in badwords:
            current_distance = distance(word, badword)
            if current_distance <= threshold and current_distance < best_distance:
                best_match = (word, badword, current_distance)
                best_distance = current_distance

        if best_match:
            flagged_words.append(best_match)

    return flagged_words


@server.route("/chatfilter")
async def check_message():
    data = await request.get_json()

    message = data["message"]
    results = check_chatfilter(message, badwords, goodwords)
    
    return results


if __name__ == "__main__":

    server.run(host="0.0.0.0", port=1234)