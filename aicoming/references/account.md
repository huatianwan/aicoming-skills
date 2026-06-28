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
