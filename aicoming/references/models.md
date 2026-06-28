# Model Discovery — Query the Live Model List

> **The single most important rule of this skill:** never hard-code or guess a model ID. Always fetch the live list first. Models on AIComing change constantly.

## List All Models (no auth)

```
GET https://aicoming.top/api/v1/models
```

```bash
curl https://aicoming.top/api/v1/models
```

```python
import requests

def list_models() -> list:
    resp = requests.get("https://aicoming.top/api/v1/models", timeout=30)
    resp.raise_for_status()
    data = resp.json()
    # Response is wrapped; the model array is usually under "data".
    return data.get("data", data)

models = list_models()
for m in models[:20]:
    print(m)
```

```typescript
const resp = await fetch('https://aicoming.top/api/v1/models');
const json = await resp.json();
const models = json.data ?? json;
console.log(models.slice(0, 20));
```

## Search by Keyword (client-side)

The endpoint returns the full list; filter locally.

```python
def search_models(keyword: str) -> list:
    kw = keyword.lower().replace("-", "").replace("_", "").replace(" ", "")
    out = []
    for m in list_models():
        blob = " ".join(str(v) for v in m.values() if isinstance(v, (str, int))).lower()
        if kw in blob.replace("-", "").replace("_", "").replace(" ", ""):
            out.append(m)
    return out

print(search_models("claude"))
print(search_models("embedding"))
```

## Related Discovery Endpoints (no auth)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/models` | All available models |
| `GET` | `/api/v1/model-vendors` | Model vendors (OpenAI, Anthropic, Google, ...) |
| `GET` | `/api/v1/providers` | Upstream providers behind the gateway |

## Popular Model IDs (illustrative only — MUST verify via API)

These are hints about what *kind* of models exist. The real, current IDs come from `/api/v1/models`.

| Model ID (example) | Type | Call via |
|--------------------|------|----------|
| `gpt-4o`, `gpt-4o-mini` | chat | `/v1/chat/completions` |
| `claude-3-5-sonnet` | chat | `/v1/chat/completions` or `/v1/messages` |
| `gemini-1.5-pro` | chat | `/v1/chat/completions` or `/v1beta/models/...` |
| `deepseek-chat` | chat | `/v1/chat/completions` |
| `text-embedding-3-small` | embedding | `/v1/embeddings` |
| `dall-e-3` | image | `/v1/images/generations` |
| `whisper-1` | audio | `/v1/audio/transcriptions` |

## The Verification Workflow

Before sending any response or code that references a model ID:

1. Fetch `GET https://aicoming.top/api/v1/models`.
2. Confirm the exact ID the user wants is present.
3. Use that exact ID. If it's absent, tell the user and suggest the closest available one — do NOT invent an ID.
