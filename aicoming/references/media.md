# 媒体:生图 / 图生图 / 视频 / 语音

Base: `https://api.aicoming.top`(**必须直连域**,长请求经 CDN 域名会被 ~100s 掐断)。

## 文生图 `POST /v1/images/generations`

```bash
curl -s https://api.aicoming.top/v1/images/generations \
  -H "Authorization: Bearer $AICOMING_API_KEY" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: my-task-$(date +%s)" \
  -d '{"model":"gpt-image-2","prompt":"草地上奔跑的柯基犬","size":"1024x1024","n":1}'
```

要点(重要程度排序):

1. **`Idempotency-Key` 头必带**:生成 60-300s,断连后**带同一个键+同样参数**重发直取结果,
   不再打上游、不重复扣费(响应带 `X-Aicoming-Idempotent-Replay: 1`)。键任意唯一字符串,
   ≤128 字符,10 分钟内有效。注意:同键不同参数会各自照常生成(键含参数指纹)。
2. **客户端超时设长**(≥600s)。等待超 60s 网关先回 200 头+空白字节保活
   (`X-Aicoming-Heartbeat: 1`);此时失败会以 200 + `{"error":{...,"http_status":N}}` 返回,
   **解析前先查顶层 `error` 字段**。
3. `size`:如 `1024x1024`/`1792x1024`/`2048x2048`/`3840x2160`,以模型支持为准;
   `gpt-image-2` 按 size 自动路由 1k/2k/4k 档(价格不同档不同)。
4. 响应 `data[0]` 是 `b64_json` 或 `url` 二选一,两种都要处理(b64 解码落盘;url 直接下载)。
5. 内容审核拦截会报 `moderation_blocked` 类错误——换措辞重试,别原样硬重试。

## 图生图 `POST /v1/images/edits`

multipart(适合本地文件):

```bash
curl -s https://api.aicoming.top/v1/images/edits \
  -H "Authorization: Bearer $AICOMING_API_KEY" \
  -H "Idempotency-Key: edit-$(date +%s)" \
  -F model="gpt-image-2" -F prompt="把背景换成星空" \
  -F image=@input.png -F size="1024x1024"
```

也支持 JSON 格式(`image` 字段放 URL 或 dataURL);多参考图用 `image[]` 多个 -F。
参考图单张过大可能被个别上游拒(400),网关会自动换家重试。

## 视频 `POST /v1/videos/generations`(异步)

```bash
# 1. 提交任务(秒回任务 id)
curl -s https://api.aicoming.top/v1/videos/generations \
  -H "Authorization: Bearer $AICOMING_API_KEY" -H "Content-Type: application/json" \
  -d '{"model":"<视频模型,从/v1/models取>","prompt":"海边日落延时"}'
# → {"data":{"id":"task_...","status":"pending",...}}

# 2. 轮询(3-5s 间隔)
curl -s https://api.aicoming.top/v1/videos/generations/<task_id> \
  -H "Authorization: Bearer $AICOMING_API_KEY"
# status: pending/processing → completed(结果含视频 url) / failed
```

图生视频:请求加参考图字段(字节系模型支持 `content` 数组带 image);时长/分辨率参数
(`duration`/`resolution`)按模型能力,计费按时长/次/或 token,详见模型市场页。

## 语音 `POST /v1/audio/transcriptions`

```bash
curl -s https://api.aicoming.top/v1/audio/transcriptions \
  -H "Authorization: Bearer $AICOMING_API_KEY" \
  -F model="<whisper系模型>" -F file=@speech.mp3
```

`/v1/audio/translations` 同格式(转写并译为英文)。

## Midjourney(异步)

```bash
curl -s https://api.aicoming.top/mj/submit/imagine \
  -H "Authorization: Bearer $AICOMING_API_KEY" -H "Content-Type: application/json" \
  -d '{"prompt":"a corgi running on grass --v 6"}'
# → {"result":"<taskId>"} ;轮询:
curl -s https://api.aicoming.top/mj/task/<taskId>/fetch \
  -H "Authorization: Bearer $AICOMING_API_KEY"
```
