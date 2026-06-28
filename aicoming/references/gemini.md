# Google Gemini Format — Complete Code Templates

AIComing accepts native Google Gemini requests at `POST https://aicoming.top/v1beta/models/{model}:{action}`. Use this when your code targets the Gemini REST format.

Actions:
- `:generateContent` — single response
- `:streamGenerateContent` — streaming response

> Fetch `GET https://aicoming.top/api/v1/models` for valid Gemini model IDs. The IDs below are illustrative.

---

## Authentication

AIComing uses your API key via the standard `Authorization: Bearer` header (instead of Google's `?key=` query param):

```
Authorization: Bearer $AICOMING_API_KEY
Content-Type: application/json
```

---

## cURL

```bash
# Non-streaming
curl "https://aicoming.top/v1beta/models/gemini-1.5-pro:generateContent" \
  -H "Authorization: Bearer $AICOMING_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "contents": [
      {"role": "user", "parts": [{"text": "Explain black holes simply."}]}
    ]
  }'

# Streaming
curl -N "https://aicoming.top/v1beta/models/gemini-1.5-pro:streamGenerateContent" \
  -H "Authorization: Bearer $AICOMING_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "contents": [{"role": "user", "parts": [{"text": "Count to 5."}]}]
  }'
```

---

## Python (raw requests)

```python
import os
import requests

API_KEY = os.environ["AICOMING_API_KEY"]
BASE = "https://aicoming.top/v1beta/models"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}


def generate(model: str, prompt: str) -> str:
    url = f"{BASE}/{model}:generateContent"
    body = {"contents": [{"role": "user", "parts": [{"text": prompt}]}]}
    resp = requests.post(url, json=body, headers=HEADERS, timeout=120)
    resp.raise_for_status()
    data = resp.json()
    return data["candidates"][0]["content"]["parts"][0]["text"]


if __name__ == "__main__":
    print(generate("gemini-1.5-pro", "Hello, Gemini!"))
```

---

## Python (google-genai SDK)

If you use Google's official SDK, point it at AIComing's base URL via the client options:

```python
import os
from google import genai
from google.genai.types import HttpOptions

client = genai.Client(
    api_key=os.environ["AICOMING_API_KEY"],
    http_options=HttpOptions(base_url="https://aicoming.top"),
)
resp = client.models.generate_content(
    model="gemini-1.5-pro",
    contents="Hello, Gemini!",
)
print(resp.text)
```

---

## Response Shape (Gemini format)

```json
{
  "candidates": [{
    "content": {
      "role": "model",
      "parts": [{"text": "Hello! How can I help?"}]
    },
    "finishReason": "STOP"
  }],
  "usageMetadata": {
    "promptTokenCount": 5,
    "candidatesTokenCount": 8,
    "totalTokenCount": 13
  }
}
```

> Tip: you can also call Gemini models through the OpenAI-compatible `/v1/chat/completions` endpoint (see `chat.md`) if you prefer one code path for all models.
