import config

import re
import requests
import json
import time
import os
from datetime import datetime
from collections import deque

def get_continuation(video_id):
    url = f"https://www.youtube.com/watch?v={video_id}"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    resp = requests.get(url, headers=headers)

    if resp.status_code != 200:
        raise Exception(f"Failed to fetch video page: {resp.status_code}")
    
    html = resp.text

    initial_data = None
    match = re.search(r"var ytInitialData = ({.*?});</script>", html)

    if match:
        initial_data = json.loads(match.group(1))
    else:
        raise Exception("Could not find ytInitialData in the page source.")
    
    continuations = (initial_data["contents"]["twoColumnWatchNextResults"]["conversationBar"]["liveChatRenderer"]["continuations"])
    continuation = continuations[0]["reloadContinuationData"]["continuation"]

    return continuation


def fetch_live_chat(continuation_token):
    url = "https://www.youtube.com/youtubei/v1/live_chat/get_live_chat"

    headers = {
        "Content-Type": "application/json"
    }

    payload = {
        "context": {
            "client": {
                "clientName": "WEB",
                "clientVersion": "2.20250724.00.00"
            }
        },
        "continuation": continuation_token
    }

    response = requests.post(url, json=payload, headers=headers)

    return response.json()
    

def parse_message(message_runs):
    parts = []
    for run in message_runs:
        if "text" in run:
            parts.append(run["text"])
        elif "emoji" in run:
            emoji = run["emoji"]
            if "shortcuts" in emoji and emoji["shortcuts"]:
                parts.append(emoji["shortcuts"][0])
            else:
                parts.append(emoji["emoji"])
        
    return "".join(parts)


def get_output_file(video_id, base_path="livechat"):
    folder = os.path.join(base_path, video_id)
    os.makedirs(folder, exist_ok=True)

    date_str = datetime.now().strftime("%m%d%y")

    filename = f"{date_str}.jsonl"
    return os.path.join(folder, filename)


def save_chat(author, message, path="test.jsonl"):
    data = {
        "author": author,
        "message": message
    }
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False) + "\n")


saved_ids = deque(maxlen=100)
saved_ids_set = set()

def is_duplicate(message_id):
    if message_id in saved_ids_set:
        return True
    
    if len(saved_ids) == saved_ids.maxlen:
        oldest = saved_ids.popleft()
        saved_ids_set.remove(oldest)

    saved_ids.append(message_id)
    saved_ids_set.add(message_id)

    return False


output_file = get_output_file(config.video_id)
def print_chat_messages(actions):
    for action in actions:
        try:
            item = action["addChatItemAction"]["item"]
            msg = item["liveChatTextMessageRenderer"]
            msg_id = msg.get("id")

            if is_duplicate(msg_id):
                continue

            author = msg["authorName"]["simpleText"]
            message_runs = msg["message"]["runs"]
            message = parse_message(message_runs)

            print(f"{author}: {message}")
            save_chat(author, message, path=output_file)
        except KeyError:
            continue


def stream_chat(continuation_token):
    while continuation_token:
        data = fetch_live_chat(continuation_token)

        actions = data["continuationContents"]["liveChatContinuation"]["actions"]
        print_chat_messages(actions)


if __name__ == "__main__":
    video_id = config.video_id
    continuation_token = get_continuation(config.video_id)
    stream_chat(continuation_token)