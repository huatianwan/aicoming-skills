# 账户:key 的路由范围 / 余额 / 用量

## 一把 key 能调什么,由三层决定

1. **路由范围(route_scope)**——建 key 时定:
   - `favorites`:跟随账号的**收藏商家**动态路由(收藏夹变,key 的可用面跟着变)——"总路由 key"模式;
   - `explicit`:锁定指派的若干商家(快照式,不随收藏变);
   - 全部:不限商家,全市场最低价路由。
2. **模型白名单(allowed_models)**——可选;设了之后调白名单外的模型直接 403
   `model_not_allowed_for_key`。只限调用,与计费无关。
3. **余额**——`GET /v1/balance` 为 0 或负,任何调用 402。

**agent 排障顺序**:403 白名单错 → 换模型或让用户改 key 设置;某模型列表里有但调不到 →
key 的路由范围不含提供该模型的商家(引导用户收藏对应商家,或用控制台"简单模式"重建 key:
选模型→系统自动反推商家配好路由)。

## 用 key 直接查(无需登录)

```bash
# 余额(CNY)
curl -s https://api.aicoming.top/v1/balance -H "Authorization: Bearer $AICOMING_API_KEY"
# → {"data":{"balance":110.17,"currency":"CNY","object":"balance"}}

# 该 key 可路由的模型
curl -s https://api.aicoming.top/v1/models -H "Authorization: Bearer $AICOMING_API_KEY"
```

## 控制台 API(JWT 登录态;agent 一般引导用户去网页操作,以下仅供确需自动化时用)

```
POST /api/v1/auth/login                       {username, password} → JWT   # 字段是 username 不是 email
GET  /api/v1/keys                             列 key
POST /api/v1/keys/quick-create                简单模式建 key:{"model_names":[...]} 自动配路由
POST /api/v1/providers/{id}/subscribe         收藏商家(DELETE 取消)——喂 favorites 路由,免费,非付费订阅
GET  /api/v1/wallet/balance                   余额
GET  /api/v1/user/usage                       用量统计
GET  /api/v1/keys/{id}/route-policy           查/改 key 路由策略(PUT)
```

> 公开市场目录(免鉴权,含价格/商家/延迟,适合比价):`GET /api/v1/models`。
> 请求模型名用其 `name` 字段(该接口的 `id` 是数据库自增号,不是模型名)。

## 给客户端配余额显示(CC Switch 等)

`GET /v1/balance` 用 sk-key 鉴权,适合配进客户端的余额脚本;控制台 API Key 页有
一键导入 CC Switch 的深链(含 usage_script)。
