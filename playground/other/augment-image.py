import json

import requests

url = "https://image.novelai.net/ai/augment-image"

payload = json.dumps({
    "req_type": "bg-removal",
    "width": 1024,
    "height": 1024,
    "image": "iVBORw0"
})
payload = json.dumps({
    "req_type": "colorize",
    "prompt": "",
    "defry": 0,
    "width": 2252,
    "height": 465,
    "image": "iVBORw0KGgoAAA"
})
payload = json.dumps({
    "req_type": "lineart",
    "width": 2252,
    "height": 465,
    "image": "iVBO"
})
payload = json.dumps({
    "req_type": "sketch",
    "width": 2252,
    "height": 465,
    "image": "iVBOR"
})

payload = json.dumps({
    "req_type": "emotion",
    "prompt": "neutral;;123132",
    "defry": 0,
    "width": 2252,
    "height": 465,
    "image": "iVBORw0KG"
})
payload = json.dumps({
    "req_type": "declutter",
    "width": 2252,
    "height": 465,
    "image": "iVBORw0"
})
APIKEY = "YOUR_API"

headers = {
    'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    'Accept-Encoding': "gzip, deflate, br, zstd",
    'Content-Type': "application/json",
    'authorization': f"Bearer {APIKEY}",
    'origin': "https://novelai.net",
    'priority': "u=1, i"
}

response = requests.post(url, data=payload, headers=headers)

print(response.text)
