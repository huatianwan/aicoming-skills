# Model Discovery — Query the Live Model List

> **The single most important rule of this skill:** never hard-code or guess a model ID. Always fetch the live list first. Models on AIComing change constantly, **and the usable set depends on the API key.**

## Two endpoints — pick the right one

| Endpoint | Auth | Returns |
|----------|------|---------|
| `GET /v1/models` | **API key** | Models THIS key can actually call. **Prefer this** when a key is available. |
| `GET /api/v1/models` | none | Full public catalog (browsing only; not all are callable by a given key). |

## Preferred: Models This Key Can Call (key required)

```bash
curl https://api.aicoming.top/v1/models \
  -H "Authorization: Bearer $AICOMING_API_KEY"
```

```python
import os, requests

def my_models() -> list:
    resp = requests.get(
        "https://api.aicoming.top/v1/models",
        headers={"Authorization": f"Bearer {os.environ['AICOMING_API_KEY']}"},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    return data.get("data", data)   # OpenAI-standard: {"object":"list","data":[{"id": "...", ...}]}

for m in my_models():
    print(m.get("id", m))
```

> In the OpenAI-standard response, the usable model identifier is the `id` field of each item — pass it as `"model"` in your requests.

## Public Catalog — All Platform Models (no auth)

Use this only for browsing/comparison when no key is set, or to show vendors/pricing.

```
GET https://api.aicoming.top/api/v1/models
```

```bash
curl https://api.aicoming.top/api/v1/models
```

```python
import requests

def list_models() -> list:
    resp = requests.get("https://api.aicoming.top/api/v1/models", timeout=30)
    resp.raise_for_status()
    data = resp.json()
    # Response is wrapped; the model array is usually under "data".
    return data.get("data", data)

models = list_models()
for m in models[:20]:
    print(m)
```

```typescript
const resp = await fetch('https://api.aicoming.top/api/v1/models');
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

Use the `name` field as the `"model"` value. Examples live at the time of writing:

| `name` (example) | Type | Call via |
|------------------|------|----------|
| `gpt-5.5`, `gpt-5.4`, `gpt-5.4-mini` | chat | `/v1/chat/completions` |
| `gpt-5.3-codex` | chat (code) | `/v1/chat/completions` |
| `claude-opus-4-8`, `claude-sonnet-4-6` | chat | `/v1/chat/completions` or `/v1/messages` |
| `deepseek-v4-pro`, `deepseek-v4-flash` | chat | `/v1/chat/completions` |
| `gemini-3.1-pro-preview` | chat | `/v1/chat/completions` or `/v1beta/models/...` |
| `glm-5.1`, `kimi-k2.6` | chat | `/v1/chat/completions` |
| `gpt-image-2-1k`, `gpt-image-2-2k`, `nano-banana-pro` | image | `/v1/images/generations` |
| `bytedance/seedance-2.0/text-to-video` | video | (provider-specific) |

## The Verification Workflow

Before sending any response or code that references a model ID:

1. Fetch `GET https://api.aicoming.top/api/v1/models`.
2. Confirm the exact ID the user wants is present.
3. Use that exact ID. If it's absent, tell the user and suggest the closest available one — do NOT invent an ID.
