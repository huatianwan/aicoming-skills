---
name: aicoming
description: "AIComing 统一模型网关接入、模型调用、图片/视频生成、任务恢复、余额与用量查询。涉及 AIComing、gptcoming.cn、统一 API 网关、OpenAI 兼容接口、模型选择或生成任务时使用。"
---

# AIComing

所有操作遵循下面的固定流程。事实类端点以 `references/endpoints.generated.md` 为准，判断规则只以 `policy/` 为准。

## Step 0：先对齐，再改动

1. 说明用户要完成的目标。
2. 列出准备读取和修改的**绝对路径**。
3. 读取现有配置；已有 provider、Key 或 SDK 配置时，先说明现状和拟议 diff，得到用户同意后再写。
4. 意图不清时采用最小侵入方式，只协助取得账号或完成本次会话，不改项目配置。

详细规则见 `policy/consent.md`。

## Step 1：安全取得 Key

优先使用设备码登录（服务端支持后）：

```bash
python scripts/aic.py login --device
```

否则使用隐藏输入，Key 只写入 `~/.aicoming/key`：

```bash
python scripts/aic.py login
```

禁止让用户把 Key 发进聊天、命令行参数、日志或项目文件。见 `policy/security.md`。

## Step 2：从当次列表选择模型

```bash
python scripts/aic.py models
python scripts/aic.py check-model <模型名>
```

模型名必须来自本次返回；不得靠记忆猜测。换模型前展示类型、价格和能力差异并征得同意。权限拒绝按 `policy/model-access.md` 处理。

## Step 3：只提交用户确认的一次调用

```bash
python scripts/aic.py chat --model <模型> --prompt <文本>
python scripts/aic.py image --model <模型> --prompt <文本>
python scripts/aic.py video --model <模型> --prompt <文本> --duration 5 --resolution 720p
```

生成类请求只提交一次。重试通常会再次扣费，必须先说明并征得同意。断线后使用：

```bash
python scripts/aic.py task <任务ID或幂等键>
python scripts/aic.py tasks --pending
```

完整计费规则见 `policy/billing.md`，禁止操作见 `policy/forbidden.md`。

## 站长管理（仅分站长明确授权时）

调用 Key 与站长管理凭据完全分开。只读授权：

```bash
python scripts/aic.py login --device --management read --base https://<分站域名>
python scripts/aic.py station models
python scripts/aic.py station customers
python scripts/aic.py station earnings
python scripts/aic.py station logs
```

需要改模型或套餐时，重新申请 `--management write`。写操作必须先执行
`station preview-model` 或 `station preview-package`，把响应里的完整 `before/after`
清单展示给用户；只有用户针对这份清单明确同意后，才可执行
`station commit <一次性确认码> --confirm`。详见 `references/station-management.md`。

## Step 4：用固定格式结束

汇报必须包含：

- 实际提交次数；
- 实际模型与规格；
- 已知费用或明确标注的估算费用；
- 任务 ID；
- 所有产出文件的绝对路径；
- 失败时是否计费，以及重新提交会再次计费的提示。

不得把原始上游响应、Key、内部请求头、商家内部编号写入结果。
