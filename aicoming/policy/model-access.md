# 模型权限处理

## 调用前

模型必须来自本次 `GET /v1/models`。若不在列表，再查公开目录：公开目录也没有时列出 3–5 个同类型近似候选，绝不猜模型名；公开目录有而 Key 列表没有时，按白名单限制处理。

对话可用 `max_tokens: 1` 做低成本探测。图片、视频和素材不得用真实生成做探测，应调用 `GET /v1/models/{id}/access`；接口不可用时说明风险并由用户决定。

## 权限错误

| 类型 | 处理 | 禁止 |
|---|---|---|
| `model_not_allowed_for_key` | 列允许模型；让用户选择允许模型、去控制台放开或用设备码新建 Key | 自动改白名单、重试 |
| `model_not_in_package` | 说明套餐范围并列同类型模型，升级在浏览器完成 | 代购、重试 |
| `package_quota_exhausted` / `key_quota_exceeded` | 说明额度已用尽 | 重试 |
| `no_favorited_providers` / `key_has_no_route_providers` / `providers_not_favorited` | 主站提示调整路由；分站只说当前站点或 Key 路由不含模型 | 分站输出商家名、自动改路由 |
| `model_not_supported_by_selected_providers` / `pinned_provider_not_available` | 提示调整所选范围 | 重试 |
| `all_selected_providers_unavailable` | 说明暂时故障，按计费规则决定稍后重试 | 当作权限问题 |
| 404 | 回到候选模型流程 | 猜名字 |
| 402 | 引导浏览器充值 | 处理支付 |

权限类拒绝发生在生成和计费前，只请求一次。用户明确只用目标模型时，不推荐替代模型，只给取得权限的步骤。
