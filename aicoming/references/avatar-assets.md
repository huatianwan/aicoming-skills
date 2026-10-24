# 参考图片与素材库

生成请求必须实际携带参考图片字段。仅在 prompt 写“图片1”、@标签、文件名或素材 ID 不会自动上传或绑定图片。prompt 在转换时保持原样；编号语法以所选模型为准，媒体顺序按数组。

## 第三方画布：继续传原图 URL

1. 用 JSON `POST /v1/assets` 上传 `{"url":"https://example.com/face.jpg","name":"角色","type":"image"}`。
2. HTTP 201 响应为 `{"code":0,"message":"ok","data":{"id":"aic_...","asset_url":"asset://aic_...","status":"processing"}}`。从 `response.data.id` 取 ID，查询 `GET /v1/assets/{id}`，从 `response.data.status` 读取状态。设置请求超时和轮询期限；failed 时检查 fail_reason，超时后继续查询已有素材。
3. 等 active 后，在视频请求中传相同的原图 URL：

```json
{"model":"doubao-seedance-2.0","prompt":"图片1的人物缓缓转身","references":[{"media_type":"image","url":"https://example.com/face.jpg"}],"resolution":"720p","seconds":5}
```

模型名、时长和档位仅为示例；先从当前 Key 的模型列表和实时价格目录确认支持情况。

平台仅对当前用户、当前站点、唯一 active image 的完整 source_url 精确匹配（包括大小写、路径、查询参数），按所选线路使用可用绑定；无绑定但具备公网回退条件时使用公网图。无匹配或歧义保持原 URL，不猜测最近上传素材。此转换无需改写提示词，不保证模型视觉效果完全一致。

## 显式素材引用

`image_urls: ["asset://aic_..."]` 使用平台返回的素材引用。标准 `references[].url` 入口只接受公网 HTTP(S)，不能直接填 asset://；它与 image/image_tail 首尾帧模式互斥。media_type 每项只能选 image、video、audio 之一。视频和音频暂不通过图片素材库上传。

支持情况取决于线路与素材绑定，不按模型后缀永久保证。上传免费但有配额；生成和参考媒体附加费以所选线路报价为准。
