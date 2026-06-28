# Images, Embeddings & Rerank — Complete Code Templates

All OpenAI-compatible, under `https://aicoming.top/v1`. Use the OpenAI SDK with `base_url="https://aicoming.top/v1"`, or raw HTTP.

> Fetch `GET https://aicoming.top/api/v1/models` for valid model IDs. The IDs below are illustrative.

---

## Text-to-Image — `/v1/images/generations`

### Python (OpenAI SDK)

```python
import os
from openai import OpenAI

client = OpenAI(api_key=os.environ["AICOMING_API_KEY"], base_url="https://aicoming.top/v1")

resp = client.images.generate(
    model="dall-e-3",                   # verify via /api/v1/models
    prompt="A serene Japanese garden with cherry blossoms, soft light",
    size="1024x1024",
    n=1,
)
print(resp.data[0].url)
```

### cURL

```bash
curl https://aicoming.top/v1/images/generations \
  -H "Authorization: Bearer $AICOMING_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "dall-e-3",
    "prompt": "A futuristic city skyline at sunset",
    "size": "1024x1024",
    "n": 1
  }'
```

Response:
```json
{ "created": 1700000000, "data": [{ "url": "https://.../image.png" }] }
```

---

## Embeddings — `/v1/embeddings`

### Python (OpenAI SDK)

```python
resp = client.embeddings.create(
    model="text-embedding-3-small",     # verify via /api/v1/models
    input=["The quick brown fox", "jumps over the lazy dog"],
)
vectors = [d.embedding for d in resp.data]
print(len(vectors), "vectors,", len(vectors[0]), "dims")
```

### cURL

```bash
curl https://aicoming.top/v1/embeddings \
  -H "Authorization: Bearer $AICOMING_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "text-embedding-3-small",
    "input": ["hello world"]
  }'
```

Response:
```json
{
  "object": "list",
  "data": [{"object": "embedding", "index": 0, "embedding": [0.0023, -0.009, ...]}],
  "model": "text-embedding-3-small",
  "usage": {"prompt_tokens": 2, "total_tokens": 2}
}
```

---

## Rerank — `/v1/rerank`

Reorder candidate documents by relevance to a query (useful for RAG). Cohere/Jina-style format.

### Python (raw requests)

```python
import os
import requests

API_KEY = os.environ["AICOMING_API_KEY"]
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

body = {
    "model": "rerank-multilingual",     # verify via /api/v1/models
    "query": "What is the capital of France?",
    "documents": [
        "Paris is the capital of France.",
        "Berlin is the capital of Germany.",
        "The Eiffel Tower is in Paris.",
    ],
    "top_n": 2,
}
resp = requests.post("https://aicoming.top/v1/rerank", json=body, headers=HEADERS, timeout=60)
resp.raise_for_status()
for r in resp.json()["results"]:
    print(r["index"], r["relevance_score"])
```

Response:
```json
{
  "results": [
    {"index": 0, "relevance_score": 0.98},
    {"index": 2, "relevance_score": 0.74}
  ]
}
```

---

## Audio — `/v1/audio/transcriptions`

Speech-to-text (OpenAI Whisper format, multipart upload).

```bash
curl https://aicoming.top/v1/audio/transcriptions \
  -H "Authorization: Bearer $AICOMING_API_KEY" \
  -F file="@audio.mp3" \
  -F model="whisper-1"
```

```python
with open("audio.mp3", "rb") as f:
    transcript = client.audio.transcriptions.create(model="whisper-1", file=f)
print(transcript.text)
```

---

## Midjourney (async) — `/mj/submit/imagine` + `/mj/task/{taskId}/fetch`

Midjourney is a two-step async flow: submit a task → poll for the result.

```python
import os, time, requests

API_KEY = os.environ["AICOMING_API_KEY"]
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

# 1. Submit
sub = requests.post("https://aicoming.top/mj/submit/imagine",
                    json={"prompt": "a cute corgi astronaut, digital art"},
                    headers=HEADERS, timeout=60)
sub.raise_for_status()
task_id = sub.json()["result"]   # task id (field name may vary — inspect the response)

# 2. Poll
while True:
    time.sleep(5)
    r = requests.get(f"https://aicoming.top/mj/task/{task_id}/fetch", headers=HEADERS, timeout=30)
    data = r.json()
    if data.get("status") in ("SUCCESS", "FAILURE"):
        print(data.get("imageUrl") or data)
        break
```

> Midjourney response field names follow the common midjourney-proxy convention. Inspect the first live response to confirm field names before hard-coding them.
