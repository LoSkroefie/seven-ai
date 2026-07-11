# Local REST API

Seven's optional REST API exposes the fully capable agent. It is disabled by default and binds only to `127.0.0.1`.

## Start

```text
python -m seven --api-only
python -m seven --daemon --api
python -m seven --gui --api
```

On first start Seven creates `~/.seven/api.token` (or `%USERPROFILE%\.seven\api.token`) containing a cryptographically random token. On POSIX systems the file is restricted to the current user. Set `SEVEN_API_TOKEN` before launch to supply a managed token instead.

## Authentication

`GET /health` is unauthenticated and contains no user or agent state. Every other endpoint requires either `Authorization: Bearer <token>` or `X-Seven-Token: <token>`.

The server does not enable browser CORS. Request bodies are limited to 1 MiB.

## Endpoints

- `GET /health` - service/version health
- `GET /status` - runtime status
- `GET /tools` - active tool schemas
- `POST /chat` - `{"message":"..."}`

```powershell
$token = (Get-Content "$HOME\.seven\api.token" -Raw).Trim()
$headers = @{ Authorization = "Bearer $token" }
Invoke-RestMethod http://127.0.0.1:7777/status -Headers $headers
Invoke-RestMethod http://127.0.0.1:7777/chat -Method Post -Headers $headers -ContentType application/json -Body '{"message":"Give me a status summary"}'
```

The token authenticates callers; it does not lower Seven's L4 autonomy. Treat it like a password because an authenticated caller can request tool execution.
