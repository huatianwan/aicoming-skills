# API Key Security — Handling `AICOMING_API_KEY`

The AIComing key (`sk-...`) is a bearer credential: anyone holding it can spend the account's balance. Treat it like a password. These rules are mandatory for this skill.

## Rules

1. **Never print, echo, or write a full `sk-` key** into chat, code, files, logs, commit messages, screenshots, or command-line arguments. A key pasted into any of these is compromised — tell the user to rotate it.
2. **Read the key only from the environment variable** `AICOMING_API_KEY`. Do not hardcode it in source, config committed to git, or example snippets.
   ```python
   api_key = os.environ["AICOMING_API_KEY"]   # ✅
   api_key = "sk-07305a..."                    # ❌ never
   ```
3. **When you must show a key, mask it**: `sk-0730**********24bb3`. Use `scripts/sanitize.js` (`maskKey`).
4. **Don't ask the user to paste their key into the chat.** Have them export it instead:
   ```bash
   export AICOMING_API_KEY="sk-..."          # add to ~/.bashrc / ~/.zshrc to persist
   ```
   If a key has already been pasted into a chat/issue/PR, treat it as leaked and tell the user to regenerate it in the console.
5. **Prefer the provided scripts over ad-hoc `curl`** for calling AIComing — `scripts/api.js` adds the auth header from the env var and masks any secret in the response, so keys never land in tool output.
6. **`.gitignore` the real key.** `.env` must never be committed; only `.env.example` (with a placeholder) belongs in git.

## Using the key without exposing it

- **In code**: reference `os.environ["AICOMING_API_KEY"]` / `process.env.AICOMING_API_KEY`. The literal never appears in your source.
- **In the shell / one-off calls**: the env var expands without you typing the value:
  ```bash
  curl https://api.gptcoming.cn/v1/balance -H "Authorization: Bearer $AICOMING_API_KEY"
  ```
- **Via the skill's caller** (auto-auth + auto-mask):
  ```bash
  node scripts/api.js GET /v1/balance
  node scripts/api.js GET /v1/models
  ```

## Setting the key — the user must do this in their own shell

A skill (or the agent) **cannot persist an environment variable for you**: a child process can't write back into the parent shell, and persisting requires touching the secret. So the user runs one of these themselves, in their own terminal:

**Windows — persist (PowerShell), writes to the user environment:**
```powershell
setx AICOMING_API_KEY "sk-..."
```
> `setx` persists for **new** terminals — the current window won't see it; open a fresh one. Don't use `setx` for values >1024 chars.

**Windows — current window only (not persisted):**
```powershell
$env:AICOMING_API_KEY = "sk-..."
```

**macOS / Linux — persist (add to shell profile):**
```bash
echo 'export AICOMING_API_KEY="sk-..."' >> ~/.zshrc   # or ~/.bashrc
source ~/.zshrc
```

**macOS / Linux — current shell only:**
```bash
export AICOMING_API_KEY="sk-..."
```

**Per-project — a `.env` file loaded by your app** (and git-ignored):
```
AICOMING_API_KEY=sk-...
```
Load it with python-dotenv / `dotenv` / your framework's env loader. Never commit `.env`; commit only `.env.example` with a placeholder.

> Do NOT have the agent run these with the real key inline — that puts the secret into AI-visible tool calls and history. The user types the value themselves; the agent only shows the command template with a `sk-...` placeholder.

## Rotation

If a key is leaked (or you're unsure), rotate it: AIComing Console → API keys → regenerate, then re-export the new value. Old key stops working immediately.
