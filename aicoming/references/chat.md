# 对话:chat completions / 流式 / 多轮 / Responses

Base: `https://api.aicoming.top`,鉴权 `Authorization: Bearer $AICOMING_API_KEY`。
模型名先 `GET /v1/models` 取当次可用的 `id`,以下示例中的模型名仅为占位。

## 一次性对话(curl)

```bash
curl -s https://api.aicoming.top/v1/chat/completions \
  -H "Authorization: Bearer $AICOMING_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"<从/v1/models取>","messages":[{"role":"user","content":"你好"}]}'
```

## Python(OpenAI SDK,推荐)

```python
from openai import OpenAI
import os

client = OpenAI(api_key=os.environ["AICOMING_API_KEY"],
                base_url="https://api.aicoming.top/v1")

resp = client.chat.completions.create(
    model="<从/v1/models取>",
    messages=[{"role": "user", "content": "你好"}],
)
print(resp.choices[0].message.content)
```

## 流式(SSE)

```python
stream = client.chat.completions.create(
    model="<model>", stream=True,
    messages=[{"role": "user", "content": "写一首短诗"}],
)
for chunk in stream:
    delta = chunk.choices[0].delta.content or ""
    print(delta, end="", flush=True)
```

curl 流式:加 `"stream": true`,响应为 `data: {...}` 行,以 `data: [DONE]` 结束。
慢首字期间网关会发 SSE 注释行保活,标准解析器自动忽略。

## 多轮对话

自己维护 messages 数组(system/user/assistant 轮替),每轮把历史带上。多轮想貼住同一家上游
(利用上游 prompt cache),带自定义头 `X-Session-ID: <会话id>` ——同会话同价商家粘性路由。

## 零依赖 Python(无 SDK,标准库)

```python
import json, os, urllib.request

req = urllib.request.Request(
    "https://api.aicoming.top/v1/chat/completions",
    data=json.dumps({
        "model": "<model>",
        "messages": [{"role": "user", "content": "你好"}],
    }).encode(),
    headers={"Authorization": "Bearer " + os.environ["AICOMING_API_KEY"],
             "Content-Type": "application/json"})
print(json.load(urllib.request.urlopen(req))["choices"][0]["message"]["content"])
```

## Node.js

```js
import OpenAI from "openai";
const client = new OpenAI({
  apiKey: process.env.AICOMING_API_KEY,
  baseURL: "https://api.aicoming.top/v1",
});
const r = await client.chat.completions.create({
  model: "<model>",
  messages: [{ role: "user", content: "你好" }],
});
console.log(r.choices[0].message.content);
```

## Responses API(Codex 等客户端)

`POST /v1/responses`,OpenAI Responses 格式原样透传;支持流式。适合把 Codex CLI 的
base url 指到 AIComing(`https://api.aicoming.top/v1`)。

## 常用参数

`temperature` `max_tokens` `top_p` `stop` `tools`/`tool_choice`(函数调用) `response_format`
(JSON 模式) 均按 OpenAI 语义透传;推理系模型的 `reasoning`/thinking 参数按上游能力转换。
