import requests

TOKEN = "8507010824:AAHWWDY5dlXSgF2rVUAbIbEO5GmfYQsuZ20"
CHAT_ID = "5862209981"

url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

data = {
    "chat_id": CHAT_ID,
    "text": "Bot test successful ✅"
}

response = requests.post(url, data=data)
print(response.json())