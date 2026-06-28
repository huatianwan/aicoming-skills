# Account, API Keys, Wallet & Usage — Complete Code Templates

These are Console API endpoints under `https://api.aicoming.top/api/v1`. Most require a JWT obtained from login. The relay API (model calls) uses an API key instead — see the other reference files.

Two distinct credentials:
- **JWT** — short-lived login token, used for console/account operations below.
- **API Key** (`sk-...`) — created in the console, used to call models (`/v1/...`).

---

## Register & Login (no auth)

```bash
# Register
curl -X POST https://api.aicoming.top/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","email":"alice@example.com","password":"12345678"}'

# Login → returns a JWT
curl -X POST https://api.aicoming.top/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"12345678"}'
# → {"data":{"token":"eyJ...","user":{...}}}
```

```python
import requests

BASE = "https://api.aicoming.top/api/v1"

def login(username: str, password: str) -> str:
    resp = requests.post(f"{BASE}/auth/login",
                         json={"username": username, "password": password}, timeout=30)
    resp.raise_for_status()
    return resp.json()["data"]["token"]

jwt = login("alice", "12345678")
AUTH = {"Authorization": f"Bearer {jwt}"}
```

> For most integrations you do NOT need to script register/login — just create an API key once in the [console UI](https://aicoming.top/console) and use it. Script the JWT flow only for programmatic account management.

---

## API Key Management (JWT auth)

```python
# List keys
requests.get(f"{BASE}/keys", headers=AUTH, timeout=30).json()

# Create a key
new_key = requests.post(f"{BASE}/keys", headers=AUTH,
                        json={"name": "my-app"}, timeout=30).json()
# The full sk-... secret is shown ONLY at creation time — store it now.

# Delete a key
requests.delete(f"{BASE}/keys/123", headers=AUTH, timeout=30)
```

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/api/v1/keys` | List your API keys (secrets masked) |
| `POST` | `/api/v1/keys` | Create a key — returns the full secret once |
| `DELETE` | `/api/v1/keys/{id}` | Delete a key |
| `PATCH` | `/api/v1/keys/{id}/status` | Enable/disable a key |
| `POST` | `/api/v1/keys/{id}/regenerate` | Rotate a key's secret |
| `GET`  | `/api/v1/keys/{id}/route-policy` | Get per-key routing policy |
| `PUT`  | `/api/v1/keys/{id}/route-policy` | Set per-key routing policy |
| `GET`  | `/api/v1/keys/{id}/route-preview` | Preview which provider a request would route to |

---

## Wallet & Balance (JWT auth)

```python
# Balance
bal = requests.get(f"{BASE}/wallet/balance", headers=AUTH, timeout=30).json()
print(bal)

# Bills / transaction history
requests.get(f"{BASE}/wallet/bills", headers=AUTH, timeout=30).json()

# Top up (returns a payment URL/order to complete in browser)
requests.post(f"{BASE}/wallet/topup", headers=AUTH,
              json={"amount": "10.00", "method": "zpay"}, timeout=30).json()
```

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/api/v1/wallet/balance` | Current balance |
| `POST` | `/api/v1/wallet/topup` | Create a top-up order |
| `GET`  | `/api/v1/wallet/topup/{order_no}/status` | Poll top-up status |
| `GET`  | `/api/v1/wallet/bills` | Transaction history |
| `POST` | `/api/v1/wallet/redeem` | Redeem a code |
| `GET`  | `/api/v1/wallet/packages` | Available packages |

---

## Enabling a Model Your Key Can't Call Yet (Provider Subscriptions, JWT auth)

Models are provided by **providers (merchants)**. A key can only call models from subscribed providers. To unlock a model that's missing from `GET /v1/models`:

```python
# 1. Find the provider for the model (from the public catalog)
catalog = requests.get("https://api.aicoming.top/api/v1/models", timeout=30).json()["data"]
target = next(m for m in catalog if m["name"] == "claude-opus-4-8")
provider_id = target["provider_id"]   # also: target["available_providers"], target["provider_name"]

# 2. Subscribe to that provider (account-level; all your keys inherit it)
requests.post(f"{BASE}/providers/{provider_id}/subscribe", headers=AUTH, timeout=30)

# 3. (Optional) buy a package if the model is gated behind a subscription plan
requests.post(f"{BASE}/wallet/subscriptions/purchase", headers=AUTH,
              json={"package_id": 1}, timeout=30)

# 4. Now it shows up for the key:
requests.get("https://api.aicoming.top/v1/models",
             headers={"Authorization": f"Bearer {os.environ['AICOMING_API_KEY']}"}, timeout=30).json()
```

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/api/v1/providers` | Browse providers (public) |
| `GET`  | `/api/v1/providers/subscriptions` | Your current subscriptions |
| `POST` | `/api/v1/providers/{id}/subscribe` | Subscribe to a provider |
| `DELETE` | `/api/v1/providers/{id}/subscribe` | Unsubscribe |
| `POST` | `/api/v1/providers/subscriptions/bulk` | Bulk subscribe/favorite |
| `POST` | `/api/v1/wallet/subscriptions/purchase` | Buy a subscription package |
| `GET`  | `/api/v1/wallet/subscriptions` | Your packages |

> Subscriptions are account-level — every API key on the account inherits them. Per-key routing preferences are set separately via `PUT /api/v1/keys/{id}/route-policy`.

## Usage Statistics (JWT auth)

```python
requests.get(f"{BASE}/user/usage", headers=AUTH, timeout=30).json()
requests.get(f"{BASE}/user/stats", headers=AUTH, timeout=30).json()
requests.get(f"{BASE}/user/logs",  headers=AUTH, timeout=30).json()
```

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/user/profile` | Account profile |
| `GET` | `/api/v1/user/usage` | Token/cost usage over time |
| `GET` | `/api/v1/user/stats` | Aggregate stats |
| `GET` | `/api/v1/user/logs` | Per-request call logs |
| `GET` | `/api/v1/call-logs/{request_id}/route-trace` | Routing trace for one request (which provider, failovers) |
