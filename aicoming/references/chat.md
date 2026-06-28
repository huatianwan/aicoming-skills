# Chat Completions — Complete Code Templates

OpenAI-compatible chat completions via `POST https://aicoming.top/v1/chat/completions`. Supports streaming (SSE) and non-streaming.

## Table of Contents
- [Python (OpenAI SDK)](#python-openai-sdk)
- [Python (raw requests + streaming)](#python-raw-requests--streaming)
- [Node.js / TypeScript (OpenAI SDK)](#nodejs--typescript-openai-sdk)
- [cURL](#curl)

> Before writing code, fetch `GET https://aicoming.top/api/v1/models` and use a real model ID. The IDs below are illustrative.

---

## Python (OpenAI SDK)

The simplest path — the official OpenAI SDK works unchanged except for `base_url`.

```python
import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ["AICOMING_API_KEY"],
    base_url="https://aicoming.top/v1",
)

# Non-streaming
resp = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Explain quantum computing in one sentence."},
    ],
    temperature=0.7,
    max_tokens=1024,
)
print(resp.choices[0].message.content)

# Streaming
stream = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Write a haiku about the sea."}],
    stream=True,
)
for chunk in stream:
    delta = chunk.choices[0].delta.content
    if delta:
        print(delta, end="", flush=True)
print()
```

---

## Python (raw requests + streaming)

Use this when you don't want the OpenAI SDK dependency, or need full control over the SSE stream.

```python
import os
import json
import requests

API_KEY = os.environ["AICOMING_API_KEY"]
BASE_URL = "https://aicoming.top/v1"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}


def chat(model: str, messages: list, **kwargs) -> str:
    """Non-streaming chat completion."""
    body = {"model": model, "messages": messages, **kwargs}
    resp = requests.post(f"{BASE_URL}/chat/completions", json=body, headers=HEADERS, timeout=120)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def chat_stream(model: str, messages: list, **kwargs):
    """Streaming chat completion — yields text deltas as they arrive."""
    body = {"model": model, "messages": messages, "stream": True, **kwargs}
    with requests.post(f"{BASE_URL}/chat/completions", json=body, headers=HEADERS,
                       stream=True, timeout=300) as resp:
        resp.raise_for_status()
        for line in resp.iter_lines(decode_unicode=True):
            if not line or not line.startswith("data: "):
                continue
            data = line[len("data: "):]
            if data == "[DONE]":
                break
            try:
                chunk = json.loads(data)
            except json.JSONDecodeError:
                continue
            delta = chunk["choices"][0]["delta"].get("content")
            if delta:
                yield delta


if __name__ == "__main__":
    print(chat("gpt-4o-mini", [{"role": "user", "content": "Hello!"}]))

    for piece in chat_stream("gpt-4o-mini", [{"role": "user", "content": "Count to 5."}]):
        print(piece, end="", flush=True)
    print()
```

---

## Node.js / TypeScript (OpenAI SDK)

```typescript
import OpenAI from 'openai';

const client = new OpenAI({
  apiKey: process.env.AICOMING_API_KEY,
  baseURL: 'https://aicoming.top/v1',
});

// Non-streaming
const resp = await client.chat.completions.create({
  model: 'gpt-4o-mini',
  messages: [{ role: 'user', content: 'Hello!' }],
  max_tokens: 1024,
});
console.log(resp.choices[0].message.content);

// Streaming
const stream = await client.chat.completions.create({
  model: 'gpt-4o-mini',
  messages: [{ role: 'user', content: 'Write a short poem.' }],
  stream: true,
});
for await (const chunk of stream) {
  const delta = chunk.choices[0]?.delta?.content;
  if (delta) process.stdout.write(delta);
}
process.stdout.write('\n');
```

---

## cURL

```bash
# Non-streaming
curl https://aicoming.top/v1/chat/completions \
  -H "Authorization: Bearer $AICOMING_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'

# Streaming (SSE)
curl -N https://aicoming.top/v1/chat/completions \
  -H "Authorization: Bearer $AICOMING_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [{"role": "user", "content": "Hello!"}],
    "stream": true
  }'
```

Response (non-streaming, standard OpenAI format):
```json
{
  "id": "chatcmpl-xxx",
  "object": "chat.completion",
  "model": "gpt-4o-mini",
  "choices": [{
    "index": 0,
    "message": {"role": "assistant", "content": "Hello! How can I help?"},
    "finish_reason": "stop"
  }],
  "usage": {"prompt_tokens": 10, "completion_tokens": 8, "total_tokens": 18}
}
```
