# 分站站长管理

调用 Key 与管理凭据分开。`read` 只读模型、套餐、客户、收益、分析、日志与质量；`write` 在此基础上允许模型上下架/加价及套餐上下架。凭据绑定签发域名和站点，可由站长撤销。

```bash
python scripts/aic.py login --device --management read --base https://api.gptcoming.cn
python scripts/aic.py station models
python scripts/aic.py station earnings
```

写操作先预览：

```bash
python scripts/aic.py station preview-model 123 --enabled --markup-rate 0.2
python scripts/aic.py station preview-package 45 --status inactive
```

展示完整 `before/after` 并取得用户针对本次清单的明确同意后，才执行：

```bash
python scripts/aic.py station commit <确认码> --confirm
```

确认码只能使用一次、十分钟过期；数据变化会拒绝提交并要求重新预览。提现、结算、资金池、客户余额、密码、佣金和凭据设置永不开放。
