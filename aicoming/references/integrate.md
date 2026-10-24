# 接入现有项目

1. 读取现有 SDK、环境变量和 provider 配置。
2. 列出准备修改的绝对路径及 diff。
3. 已有配置时新建 `aicoming` profile，不覆盖默认 provider。
4. 用户逐项确认后才写入。
5. Key 默认保存在 `~/.aicoming/key`，项目只引用环境变量或凭据文件。
6. 完成后提供恢复原 provider 的具体步骤。
