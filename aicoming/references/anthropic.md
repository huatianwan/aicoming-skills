# Anthropic Messages Format — Complete Code Templates

AIComing accepts native Anthropic Messages requests at `POST https://aicoming.top/v1/messages`. Use this when your code already targets the Anthropic SDK/format — just change the base URL.

> Authentication uses the AIComing API key. AIComing accepts it via the standard `Authorization: Bearer` header. Fetch `GET https://aicoming.top/api/v1/models` for valid Claude model IDs.

---

## Python (Anthropic SDK)

```python
import os
from anthropic import Anthropic

client = Anthropic(
    api_key=os.environ["AICOMING_API_KEY"],
    base_url="https://aicoming.top",   # SDK appends /v1/messages
)

resp = client.messages.create(
    model="claude-3-5-sonnet",          # verify via /api/v1/models
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello, Claude!"}],
)
print(resp.content[0].text)
```

---

## Python (raw requests)

```python
import os
import requests

API_KEY = os.environ["AICOMING_API_KEY"]
URL = "https://aicoming.top/v1/messages"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "anthropic-version": "2023-06-01",
}

body = {
    "model": "claude-3-5-sonnet",
    "max_tokens": 1024,
    "messages": [{"role": "user", "content": "Explain SSE in one line."}],
}
resp = requests.post(URL, json=body, headers=HEADERS, timeout=120)
resp.raise_for_status()
print(resp.json()["content"][0]["text"])
```

### Streaming

```python
import json

body["stream"] = True
with requests.post(URL, json=body, headers=HEADERS, stream=True, timeout=300) as resp:
    resp.raise_for_status()
    for line in resp.iter_lines(decode_unicode=True):
        if not line or not line.startswith("data: "):
            continue
        event = json.loads(line[len("data: "):])
        if event.get("type") == "content_block_delta":
            print(event["delta"].get("text", ""), end="", flush=True)
print()
```

---

## Node.js / TypeScript (Anthropic SDK)

```typescript
import Anthropic from '@anthropic-ai/sdk';

const client = new Anthropic({
  apiKey: process.env.AICOMING_API_KEY,
  baseURL: 'https://aicoming.top',
});

const resp = await client.messages.create({
  model: 'claude-3-5-sonnet',
  max_tokens: 1024,
  messages: [{ role: 'user', content: 'Hello!' }],
});
console.log(resp.content[0].type === 'text' ? resp.content[0].text : '');
```

---

## cURL

```bash
curl https://aicoming.top/v1/messages \
  -H "Authorization: Bearer $AICOMING_API_KEY" \
  -H "Content-Type: application/json" \
  -H "anthropic-version: 2023-06-01" \
  -d '{
    "model": "claude-3-5-sonnet",
    "max_tokens": 1024,
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

Response (Anthropic format):
```json
{
  "id": "msg_xxx",
  "type": "message",
  "role": "assistant",
  "content": [{"type": "text", "text": "Hello! How can I help?"}],
  "model": "claude-3-5-sonnet",
  "stop_reason": "end_turn",
  "usage": {"input_tokens": 10, "output_tokens": 8}
}
```

> Tip: if you don't need the native Anthropic shape, you can also call Claude models through the OpenAI-compatible `/v1/chat/completions` endpoint (see `chat.md`) — AIComing routes both to the same upstream.
