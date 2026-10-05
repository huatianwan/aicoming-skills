# Google Gemini Format — Complete Code Templates

AIComing accepts native Google Gemini requests at `POST https://api.gptcoming.cn/v1beta/models/{model}:{action}`. Use this when your code targets the Gemini REST format.

> ⚠️ **Verified gotcha:** the upstream node only accepts **streaming** for this format. Use **`:streamGenerateContent`**. A non-streaming `:generateContent` call is rejected with:
> ```json
> {"error":{"message":"this NewAPI node only accepts streaming requests; set stream=true","type":"invalid_request"}}
> ```
> If you want a simple non-streaming call, use the OpenAI-compatible `/v1/chat/completions` endpoint instead (see `chat.md`) — it works with any model on the gateway, including Gemini-family ones.

> There may be no `gemini-*` model in the list at a given time, but the Gemini *format adapter* works against whatever models the gateway serves. Fetch `GET https://api.gptcoming.cn/v1/models` for valid model ids (use the `id` field).

---

## Authentication

Use your AIComing API key via the standard `Authorization: Bearer` header (instead of Google's `?key=` query param):

```
Authorization: Bearer $AICOMING_API_KEY
Content-Type: application/json
```

---

## cURL (streaming — the supported path)

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
    url = f"{BASE}/{model}:streamGenerateContent"   # must be the streaming action
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
    print(generate_stream("gpt-5.4-mini", "Hello, Gemini format!"))
```

---

## Python (google-genai SDK)

The official SDK uses streaming via `generate_content_stream`. Point it at AIComing's base URL:

```python
import os
from google import genai
from google.genai.types import HttpOptions

client = genai.Client(
    api_key=os.environ["AICOMING_API_KEY"],
    http_options=HttpOptions(base_url="https://api.gptcoming.cn"),
)
for chunk in client.models.generate_content_stream(
    model="gpt-5.4-mini",          # use an id from GET /v1/models
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
