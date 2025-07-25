import config

import re
import requests
import json
import time

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
    

def print_chat_messages(actions):
    for action in actions:
        try:
            msg = action["addChatItemAction"]["item"]["liveChatTextMessageRenderer"]
            author = msg["authorName"]["simpleText"]
            message_text = msg["message"]["runs"]
            message = "".join(run.get("text", "") for run in message_text)

            print(f"{author}: {message}")
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