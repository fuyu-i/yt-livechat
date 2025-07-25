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


video_id = "szxssf"
continuation = get_continuation(video_id)
print(f"Continuation token: {continuation}")