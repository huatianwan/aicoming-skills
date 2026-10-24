# AIComing Skill

统一模型网关接入文档与 CLI。此仓库的 aicoming/ 来自当前服务端模板和接口事实清单，修订版本 **2026-10-24.1**；文件来源及内容哈希见 aicoming/SOURCE.json。

## 文档入口

- [主站 API 文档](https://aicoming.top/docs)
- [视频教程](https://aicoming.top/docs-video.html)
- [在线 Skill](https://aicoming.top/agent/SKILL.md)
- [完整安装包](https://api.aicoming.top/agent/files.json)
- [机器可读事实清单](https://api.aicoming.top/api/v1/skill-manifest)
- [参考素材与第三方画布](aicoming/references/avatar-assets.md)
- [模型发现与权限](aicoming/references/models.md)
- [图片、视频与响应格式](aicoming/references/images-embeddings.md)
- [Gemini](aicoming/references/gemini.md)
- [计费与重试](aicoming/policy/billing.md)

## 安装和使用

复制 aicoming/ 到所用工具的 Skill 目录，或使用在线安装包提供的安装器。现有仓库安装入口仍保留。CLI 需要 Python 3；Key 通过隐藏输入保存，不要粘贴到聊天或项目文件。

```bash
git clone https://github.com/huatianwan/aicoming-skills.git
# 在安装后的 Skill 目录运行：
python scripts/aic.py login
python scripts/aic.py models
python scripts/aic.py check-model <本次列表中的模型名>
```

生成请求只按用户授权提交一次。断线后先查已有任务和用量；同步生图只有成功结果缓存命中才可免费重放，同一幂等键不保证并发、尚未完成、跨节点或缓存未命中的请求免重复计费。完整规则见计费文档。

## 维护

事实源为 huatianwan/aicoming 的 internal/agentfiles/templates 与 internal/apimanifest/manifest.go。通过 `go run ./cmd/export-agent-skill` 导出主站安装包，校验 SHA-256 后同步，并记录 SOURCE.json；不单独修改生成的端点清单。分站使用自己的在线安装包，避免混用主站地址。

本次文档验证不包含付费模型效果测试或所有第三方客户端兼容性承诺。实时模型、价格与权限以请求时查询结果为准。

## License

MIT
