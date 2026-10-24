# Google Gemini Format — Complete Code Templates

AIComing accepts native Google Gemini requests at `POST https://api.gptcoming.cn/v1beta/models/{model}:{action}`. Use this when your code targets the Gemini REST format.

Supports `generateContent` (non-streaming), `streamGenerateContent` (SSE), and `countTokens` (free local estimate, not billing usage). Text generation requires a Gemini-family model visible to the current key; other text model families are rejected. Supported image models have a separate adaptation path. Fetch `/v1/models` and check `/v1/models/{id}/access` first.

Use the site root as the google-genai SDK base URL (no `/v1` suffix). Keep the API key in headers rather than URLs.

---

## Authentication

Use your AIComing API key via the standard `Authorization: Bearer` header (instead of Google's `?key=` query param):

```
Authorization: Bearer $AICOMING_API_KEY
Content-Type: application/json
```

---

## cURL (streaming)

```bash
curl -N "https://api.gptcoming.cn/v1beta/models/<model-id>:streamGenerateContent" \
  -H "Authorization: Bearer $AICOMING_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "contents": [{"role": "user", "parts": [{"text": "Count to 5."}]}]
  }'
```

Each SSE line is `data: { ...Gemini chunk... }`:
```
data: {"candidates":[{"content":{"role":"model","parts":[{"text":"Hi"}]},"finishReason":null,"index":0}],"usageMetadata":{...}}
data: {"candidates":[{"content":{"role":"model","parts":[{"text":"!"}]},...}]}
```

---

## Python (raw requests, streaming)

```python
import os, json, requests

API_KEY = os.environ["AICOMING_API_KEY"]
BASE = "https://api.gptcoming.cn/v1beta/models"
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}


def generate_stream(model: str, prompt: str) -> str:
    url = f"{BASE}/{model}:streamGenerateContent"   # choose generateContent for non-streaming
    body = {"contents": [{"role": "user", "parts": [{"text": prompt}]}]}
    out = []
    with requests.post(url, json=body, headers=HEADERS, stream=True, timeout=300) as resp:
        resp.raise_for_status()
        for line in resp.iter_lines(decode_unicode=True):
            if not line or not line.startswith("data: "):
                continue
            chunk = json.loads(line[len("data: "):])
            for cand in chunk.get("candidates", []):
                for part in cand.get("content", {}).get("parts", []):
                    if part.get("text"):
                        out.append(part["text"])
    return "".join(out)


if __name__ == "__main__":
    # use an id from GET /v1/models
    print(generate_stream(os.environ["AICOMING_GEMINI_MODEL"], "Hello, Gemini format!"))
```

---

## Python (google-genai SDK)

Set AICOMING_GEMINI_MODEL to a Gemini model from the current key list. The official SDK uses streaming via `generate_content_stream`. Point it at AIComing's base URL:

```python
import os
from google import genai
from google.genai.types import HttpOptions

client = genai.Client(
    api_key=os.environ["AICOMING_API_KEY"],
    http_options=HttpOptions(base_url="https://api.gptcoming.cn"),
)
for chunk in client.models.generate_content_stream(
    model=os.environ["AICOMING_GEMINI_MODEL"],          # use an id from GET /v1/models
    contents="Hello!",
):
    print(chunk.text, end="", flush=True)
print()
```

---

## Streaming chunk shape (Gemini format)

```json
{
  "candidates": [{
    "content": {"role": "model", "parts": [{"text": "Hello!"}]},
    "finishReason": "STOP",
    "index": 0
  }],
  "usageMetadata": {"promptTokenCount": 5, "candidatesTokenCount": 8, "totalTokenCount": 13}
}
```

> Simplest cross-model path: call everything through the OpenAI-compatible `/v1/chat/completions` (see `chat.md`) — one code path, supports non-streaming, works for Gemini-family models too.

## Non-streaming and token estimates

Use the same contents body with `:generateContent` for a JSON response, or `:countTokens` for `{"totalTokens": ...}`. The latter is a local estimate and does not submit a paid generation.
