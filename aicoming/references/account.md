# 账号、Key、余额与用量

Agent 不收集用户名或密码，也不调用密码登录接口。

- 注册、充值、套餐升级、Key 管理：在当前站点控制台由用户完成。
- CLI 保存已有 Key：`python scripts/aic.py login`，从隐藏输入或标准输入读取。
- 设备码登录：`python scripts/aic.py login --device`（站点支持时）。
- 查看当前身份：`python scripts/aic.py whoami`。
- 查看余额：`python scripts/aic.py balance`。
- 查看用量：`python scripts/aic.py usage`。

Key 只保存在用户目录的凭据文件，禁止作为命令行参数传入。
