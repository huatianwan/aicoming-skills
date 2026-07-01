---
name: aicoming
description: "用用户自己的 AIComing API key 直接调用 127+ 大模型干活:对话/生图/视频/嵌入/重排/语音转写,以及查余额、列可用模型;也支持把现有项目接入 AIComing(OpenAI/Anthropic/Gemini SDK 只换 base_url)。触发场景:(1)用户提到 aicoming / aicoming.top / AIComing key;(2)用户要求用自己的 AIComing 账号生成图片、调用某个大模型、查询余额或可用模型;(3)用户要把项目的模型调用切换/接入到 AIComing。Use when the user mentions AIComing or wants to call models / generate images / check balance with their AIComing API key."
---

# AIComing — 用用户的 key 直接干活

AIComing(aicoming.top)是聚合 127+ 大模型的 OpenAI 兼容网关。用户配好 `AICOMING_API_KEY` 后,你(agent)可以直接替用户调模型:生图、跑对话、查余额、提视频任务——不只是写接入代码。

## Codex 用户必读:先放行沙箱网络

Codex CLI 的沙箱**默认禁止命令访问外网**——症状是调用 api.aicoming.top 时报
"访问套接字被拒 / connection refused",看起来像被拦截。修复:`~/.codex/config.toml`
顶层加 `sandbox_mode = "workspace-write"`,并加表:

```toml
[sandbox_workspace_write]
network_access = true
```

(或单次运行:`codex exec -s workspace-write -c sandbox_workspace_write.network_access=true ...`)
Claude Code 无此问题。

## Key 与 Base URL

- **Key 来源**:环境变量 `AICOMING_API_KEY`,或文件 `~/.aicoming/key`。没有时引导用户去 [控制台](https://aicoming.top/console) 创建(推荐"简单模式"向导:选模型→自动配路由),然后 `export AICOMING_API_KEY=sk-...`。**绝不替用户编造或猜测 key。**
- **Base URL 必须用直连域** `https://api.aicoming.top`——生图/视频等长请求(60-300s)经 CDN 代理的域名会被 ~100 秒网关超时掐断,直连域无此限制。
- 鉴权统一 `Authorization: Bearer $AICOMING_API_KEY`。

## 首选工具:scripts/aic.py

零依赖(Python 3.8+ 标准库),封好了鉴权、心跳容错、生图幂等重试、b64 落盘、视频轮询。
脚本在本 skill 目录下(Claude Code 通常是 `~/.claude/skills/aicoming/scripts/aic.py`;
Windows 上用 `python`,类 Unix 用 `python3` 均可):

```bash
python scripts/aic.py models [关键词]        # 该 key 可路由的模型列表
python scripts/aic.py chat <model> <提示词>   # 一次性对话
python scripts/aic.py image <model> <提示词> [--size 1024x1024] [-o out.png]
python scripts/aic.py balance                # 余额(CNY)
python scripts/aic.py video <model> <提示词>  # 提交视频任务并轮询到完成
```

脚本没覆盖的(流式、多轮、embeddings、rerank、audio、Anthropic/Gemini 协议),按 references 里的示例直接发 HTTP。

## 铁律:模型名永远来自实时列表

模型上下架频繁,**且每把 key 能调什么受它的路由范围和白名单限制**。任何写进请求/代码/回复的模型名,必须来自当次 `GET /v1/models`(带 key)响应的 `id` 字段——不凭记忆、不凭示例、不凭模式推断。

- `GET https://api.aicoming.top/v1/models`(带 key)→ OpenAI 标准格式,`data[].id` 就是请求里的 `"model"` 值。
- `GET https://api.aicoming.top/api/v1/models`(免鉴权)→ 公开市场目录(价格/商家/延迟),用于浏览比价;请求用它的 `name` 字段。
- 列表里有 ≠ 一定能调:key 可能设了 `allowed_models` 白名单(403 `model_not_allowed_for_key`)或路由范围不含该模型的商家——见 `references/account.md`。

## 生图要点(必读再动手)

1. **模型名**:通用生图直接用 `gpt-image-2`(网关按 size 自动分 1k/2k/4k 档),或列表里的其它 image 模型。
2. **必带 `Idempotency-Key` 头**(aic.py 已自动带):生成要 60-300 秒,连接被客户端超时/网络切换掐断后,带同一个键原样重发即可**直取已生成的图、不重复扣费**。没带键的断连=白花钱重来。
3. **心跳容错**:等待超 60s 网关会先回 200 头 + 周期性空白字节保活(响应带 `X-Aicoming-Heartbeat: 1`)。JSON 解析器天然容忍前导空白;但此时若生成失败,错误在 body 里:`{"error":{"message":...,"http_status":N}}` ——**解析成功响应前先检查顶层 error 字段**(aic.py 已处理)。
4. 图生图:`POST /v1/images/edits`(multipart 或 JSON 带参考图),细节见 `references/media.md`。

## 端点总览(全部实测存在)

| 用途 | 端点 | 说明 |
|---|---|---|
| 对话 | `POST /v1/chat/completions` | OpenAI 格式,支持 `stream:true` |
| Responses | `POST /v1/responses` | OpenAI Responses API(Codex 等) |
| Claude 原生 | `POST /v1/messages` | Anthropic 格式,SDK 换 base_url 即用 |
| Gemini 原生 | `POST /v1beta/models/{model}:generateContent` | Google 格式(含 :streamGenerateContent) |
| 生图 | `POST /v1/images/generations` | 见上"生图要点" |
| 图生图 | `POST /v1/images/edits` | multipart / JSON |
| 视频 | `POST /v1/videos/generations` → `GET /v1/videos/generations/{id}` | 异步任务+轮询 |
| 嵌入 | `POST /v1/embeddings` | OpenAI 格式 |
| 重排 | `POST /v1/rerank` | RAG 重排 |
| 语音转写 | `POST /v1/audio/transcriptions` / `translations` | Whisper 格式 |
| 模型列表 | `GET /v1/models` | 带 key;`data[].id` 即模型名 |
| 余额 | `GET /v1/balance` | 返回 `{balance, currency:"CNY"}` |
| Midjourney | `POST /mj/submit/imagine` → `GET /mj/task/{id}/fetch` | 异步任务 |

> `/v1/*` 同时镜像在 `/v1/v1/*`(容错客户端多拼一层 /v1)。

## 错误处理

| 状态 | 含义 | 动作 |
|---|---|---|
| 401 | key 无效/过期 | 让用户检查 `AICOMING_API_KEY` |
| 402 | 余额不足 | `GET /v1/balance` 确认,引导去控制台充值 |
| 403 `model_not_allowed_for_key` | key 设了模型白名单 | 换白名单内模型,或让用户在控制台改 key 设置 |
| 429 | 限速 | 指数退避重试(1s→2s→4s) |
| 5xx / `all N endpoints failed` | 上游故障(网关已自动 failover 过) | 稍后重试;生图带同一个 Idempotency-Key 重试 |

**别盲目重试 POST 生成请求**(会重复扣费)——唯一例外:生图带同一个 `Idempotency-Key` 的重试是安全的。

## 深入参考(按需读取)

- `references/chat.md` — 对话/流式/多轮/Responses(Python·Node·curl)
- `references/media.md` — 生图/图生图/视频/语音 完整示例与参数
- `references/protocols.md` — Anthropic SDK / Gemini SDK / OpenAI SDK 直连三协议
- `references/account.md` — key 路由范围(收藏商家/指派/白名单)、余额、用量、route-policy
- `references/integrate.md` — 把现有项目接入 AIComing(各 SDK 只换 base_url 的速查表)
