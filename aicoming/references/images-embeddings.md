# Images, Embeddings & Rerank — Complete Code Templates

All OpenAI-compatible, under `https://api.gptcoming.cn/v1`. Use the OpenAI SDK with `base_url="https://api.gptcoming.cn/v1"`, or raw HTTP.

> Fetch `GET https://api.gptcoming.cn/api/v1/models` for valid model IDs and use the `name` field. Image models seen live include `gpt-image-2-1k`, `gpt-image-2-2k`, `nano-banana-pro`.
>
> **Note:** the `/v1/embeddings`, `/v1/rerank`, and `/v1/audio/*` endpoints exist, but at the time of writing the model list contains only chat/image/video models. The embedding/rerank/audio model IDs below are placeholders — confirm a matching model is present in `/api/v1/models` before relying on them.

---

## Text-to-Image — `/v1/images/generations`

> **Response format (verified):** `gpt-image-*` models return the image as **base64** in `data[0].b64_json`, NOT a URL. Decode and save it yourself. (Some other image models may return `data[0].url` instead — handle both.)
>
> **Timeout:** image generation is synchronous and some models/sizes are slow. Set an explicit long timeout — **600s (10 min)**. Never leave a raw `requests` call with no timeout, and don't set it too short or slow renders get truncated.

### Python (OpenAI SDK)

```python
import os, base64
from openai import OpenAI

# Raise the SDK timeout for slow image renders — 600s (10 min)
client = OpenAI(api_key=os.environ["AICOMING_API_KEY"],
                base_url="https://api.gptcoming.cn/v1",
                timeout=600)

resp = client.images.generate(
    model="gpt-image-2-1k",                   # use an id from GET /v1/models
    prompt="A serene Japanese garden with cherry blossoms, soft light",
    size="1024x1024",
    n=1,
)
item = resp.data[0]
if getattr(item, "b64_json", None):
    with open("out.png", "wb") as f:
        f.write(base64.b64decode(item.b64_json))
    print("saved out.png")
else:
    print(item.url)
```

### cURL

```bash
curl --max-time 600 https://api.gptcoming.cn/v1/images/generations \
  -H "Authorization: Bearer $AICOMING_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-image-2-1k",
    "prompt": "A futuristic city skyline at sunset",
    "size": "1024x1024",
    "n": 1
  }'
```

Response (verified for `gpt-image-*` — base64, not URL):
```json
{ "created": 1782704322, "data": [{ "b64_json": "iVBORw0KGgoAAAANSUhEUg..." }] }
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
curl https://api.gptcoming.cn/v1/embeddings \
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
resp = requests.post("https://api.gptcoming.cn/v1/rerank", json=body, headers=HEADERS, timeout=60)
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
curl https://api.gptcoming.cn/v1/audio/transcriptions \
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

## Image Editing — `/v1/images/edits`

OpenAI-compatible image edit (verified). Multipart form with fields `model`, `image` (the source file), and `prompt`. Returns `data[0].b64_json` like generation. Set a long timeout (600s).

```bash
curl --max-time 600 https://api.gptcoming.cn/v1/images/edits \
  -H "Authorization: Bearer $AICOMING_API_KEY" \
  -F "model=gpt-image-2-1k" \
  -F "image=@photo.png" \
  -F "prompt=make the sky a dramatic sunset"
```

```python
import base64

with open("photo.png", "rb") as img:
    edited = client.images.edit(
        model="gpt-image-2-1k",          # use an id from GET /v1/models
        image=img,
        prompt="make the sky a dramatic sunset",
    )
item = edited.data[0]
# Like generation, gpt-image-* returns base64 (b64_json); other models may return url
data = base64.b64decode(item.b64_json) if getattr(item, "b64_json", None) else None
print("got b64 image" if data else item.url)
```

---

## Video Generation (async) — `/v1/videos/generations` + `/v1/videos/generations/{id}`

Two-step: submit a task → poll by id. **Use the model `id` exactly as `GET /v1/models` returns it** — e.g. `bytedance-seedance-2.0-text-to-video` (hyphenated), NOT the slash form `bytedance/seedance-2.0/text-to-video` from the public catalog.

Never hold one long-lived request open for the whole render. Submit fast, then poll with a **bounded** loop (cap total wait) so a stuck task can't loop forever.

```python
import os, time, requests

API_KEY = os.environ["AICOMING_API_KEY"]
H = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

# 1. Submit (fast — short timeout is fine; the render happens async)
sub = requests.post("https://api.gptcoming.cn/v1/videos/generations",
                    json={"model": "bytedance-seedance-2.0-text-to-video",
                          "prompt": "a rocket launching, cinematic"},
                    headers=H, timeout=60)
sub.raise_for_status()
task_id = sub.json().get("id") or sub.json().get("data", {}).get("id")

# 2. Poll with a hard cap (e.g. 120 tries * 5s = 10 min)
for _ in range(120):
    time.sleep(5)
    r = requests.get(f"https://api.gptcoming.cn/v1/videos/generations/{task_id}",
                     headers=H, timeout=30).json()
    status = r.get("status") or r.get("data", {}).get("status")
    if status in ("completed", "succeeded", "failed"):
        print(r)
        break
else:
    raise TimeoutError(f"video task {task_id} did not finish within 10 minutes")
```

> **Access note (verified):** model access is **group-based**. If your key's group doesn't include the model's category you'll get `403 {"error":{"message":"无权访问 图像视频 分组","type":"new_api_error"}}` — the request body was fine; the key just lacks permission for that group. See "Using a Model Your Key Doesn't Have Yet" in `SKILL.md`.

> Submit/response field names follow the gateway's video schema — inspect the first live response to confirm before hard-coding.

---

## Responses API — `/v1/responses`

OpenAI's newer Responses API is also relayed. Use the OpenAI SDK's `client.responses.create(...)` with `base_url="https://api.gptcoming.cn/v1"`.

---

## Wallet Balance via API key — `/v1/balance`

Unlike the JWT console endpoints, balance is also exposed under the relay with just the API key:

```bash
curl https://api.gptcoming.cn/v1/balance -H "Authorization: Bearer $AICOMING_API_KEY"
```

---

## Midjourney (async) — `/mj/submit/imagine` + `/mj/task/{taskId}/fetch`

Midjourney is a two-step async flow: submit a task → poll for the result.

```python
import os, time, requests

API_KEY = os.environ["AICOMING_API_KEY"]
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

# 1. Submit
sub = requests.post("https://api.gptcoming.cn/mj/submit/imagine",
                    json={"prompt": "a cute corgi astronaut, digital art"},
                    headers=HEADERS, timeout=60)
sub.raise_for_status()
task_id = sub.json()["result"]   # task id (field name may vary — inspect the response)

# 2. Poll
while True:
    time.sleep(5)
    r = requests.get(f"https://api.gptcoming.cn/mj/task/{task_id}/fetch", headers=HEADERS, timeout=30)
    data = r.json()
    if data.get("status") in ("SUCCESS", "FAILURE"):
        print(data.get("imageUrl") or data)
        break
```

> Midjourney response field names follow the common midjourney-proxy convention. Inspect the first live response to confirm field names before hard-coding them.
