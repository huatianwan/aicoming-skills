# 三协议直连:OpenAI / Anthropic / Gemini

同一把 key、同一个网关,三种协议任选——用与现有代码/SDK 匹配的那种。
**跨协议随意组合**:比如用 Anthropic 格式调 GPT 系模型、OpenAI 格式调 Claude,网关自动做双向协议转换(含流式、工具调用、思考/推理参数、缓存计费)。

## OpenAI 协议(默认)

- 端点:`/v1/chat/completions` `/v1/responses` `/v1/embeddings` `/v1/images/*` 等
- SDK:`base_url="https://api.aicoming.top/v1"`,其余不动(见 chat.md)

## Anthropic 协议 `POST /v1/messages`

```python
import anthropic, os
client = anthropic.Anthropic(
    api_key=os.environ["AICOMING_API_KEY"],
    base_url="https://api.aicoming.top",   # 注意:不带 /v1,SDK 自己拼 /v1/messages
)
msg = client.messages.create(
    model="<从/v1/models取,claude系或任意chat模型>",
    max_tokens=1024,
    messages=[{"role": "user", "content": "你好"}],
)
print(msg.content[0].text)
```

curl:

```bash
curl -s https://api.aicoming.top/v1/messages \
  -H "Authorization: Bearer $AICOMING_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"<model>","max_tokens":1024,"messages":[{"role":"user","content":"你好"}]}'
```

(`x-api-key` 头也接受;流式 `"stream": true` 为 Anthropic SSE 事件格式。)

**Claude Code / 其它 Anthropic 兼容客户端**:把 `ANTHROPIC_BASE_URL=https://api.aicoming.top`、
`ANTHROPIC_AUTH_TOKEN=$AICOMING_API_KEY` 即可。

## Gemini 协议 `POST /v1beta/models/{model}:generateContent`

```bash
curl -s "https://api.aicoming.top/v1beta/models/<model>:generateContent" \
  -H "Authorization: Bearer $AICOMING_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"contents":[{"parts":[{"text":"你好"}]}]}'
```

流式用 `:streamGenerateContent`。`?key=` 查询参数鉴权也接受(Google SDK 习惯)。
Gemini 生图模型的 `generationConfig.imageConfig`(aspectRatio/imageSize)原样支持。

## 选择建议

| 场景 | 用 |
|---|---|
| 通用/新项目 | OpenAI 协议(生态最广) |
| 现有代码是 Anthropic SDK / Claude Code | Anthropic 协议,零改动 |
| 现有代码是 Google SDK | Gemini 协议 |
| Codex CLI | OpenAI Responses(`/v1/responses`) |
