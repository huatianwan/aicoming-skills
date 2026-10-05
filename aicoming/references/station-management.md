# 分站站长管理

## 权限边界

- `read`：模型上架与价格、套餐、客户列表、收益、经营分析、调用日志、质量统计。
- `write`：包含只读能力，并允许模型上下架/加价和套餐上下架。
- 永不开放：提现、结算确认、资金池、客户余额、密码、佣金、支付/邮件/OAuth/银行凭据。
- 凭据绑定签发时的域名和站点，不能拿到另一个分站或主站使用；站长可在控制台随时撤销。

## 只读示例

```bash
python scripts/aic.py login --device --management read --base https://<分站域名>
python scripts/aic.py station dashboard
python scripts/aic.py station models
python scripts/aic.py station packages
python scripts/aic.py station customers
python scripts/aic.py station earnings
python scripts/aic.py station analytics
python scripts/aic.py station logs
python scripts/aic.py station quality
```

## 写操作确认协议

1. 使用写权限登录：`login --device --management write`。
2. 只做预览：

```bash
python scripts/aic.py station preview-model 123 --enabled --markup-rate 0.2
python scripts/aic.py station preview-package 45 --status inactive
```

3. 将完整的 `before`、`after`、模型/套餐名称和最终加价率展示给用户。
4. 用户必须针对这份预览明确同意。之前的笼统授权不能替代本次确认。
5. 执行一次性确认：

```bash
python scripts/aic.py station commit <确认码> --confirm
```

确认码十分钟过期且只能使用一次。预览后的数据若被别人改动，提交会拒绝；重新预览并再次取得用户确认。批量变更逐项预览，向用户展示全量清单后再逐项提交。
