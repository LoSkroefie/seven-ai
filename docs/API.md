# Local REST API

Seven's optional REST API exposes the fully capable agent. It is disabled by default and binds only to `127.0.0.1`.

## Start

```text
python -m seven --api-only
python -m seven --daemon --api
python -m seven --gui --api
```

On first start Seven atomically creates `~/.seven/api.token` (or `%USERPROFILE%\.seven\api.token`) containing a cryptographically random token. On POSIX systems the file is created mode `0600`; existing files are re-restricted where supported. Concurrent starts converge on the one file value. Set `SEVEN_API_TOKEN` before launch to supply a managed token instead. Environment/file tokens shorter than 32 characters are rejected.

## Authentication

`GET /health` is unauthenticated and contains no user or agent state. Every other endpoint requires either `Authorization: Bearer <token>` or `X-Seven-Token: <token>`.

The server does not enable browser CORS and rejects `OPTIONS` with JSON `405`. It cannot be configured to bind a non-loopback address. Responses use `no-store`, `nosniff`, and no-referrer headers.

Defaults are a 1 MiB body, 100,000-character message, eight concurrent requests, and 30-second accepted-socket timeout. Configure these with `SEVEN_API_MAX_BODY_BYTES`, `SEVEN_API_MAX_MESSAGE_CHARS`, `SEVEN_API_CONCURRENCY`, and `SEVEN_API_SOCKET_TIMEOUT`. Overload fails immediately with `503` instead of accumulating unbounded waiting threads. Agent operations remain serialized because Seven's conversation/tool state is shared; health requests can run concurrently when capacity exists.

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

## Request and lifecycle semantics

`POST /chat` requires `Content-Type: application/json`, a valid positive `Content-Length`, a complete UTF-8 JSON object, and a non-empty string `message` (or compatibility key `text`). Malformed/incomplete input is `400`, missing length is `411`, wrong media type is `415`, body/message overflow is `413`, and unsupported methods are `405`. Internal exceptions are logged locally and returned only as generic JSON `500`, without exposing exception details.

Each server owns its concurrency state and lazily created agent. When an existing GUI/daemon agent is injected, the caller retains ownership. Clean shutdown stops accepting sockets, waits up to ten seconds for active handlers, closes the port, and shuts down only an API-owned idle agent. GUI and daemon modes now call that lifecycle explicitly. A port conflict makes `--api-only` exit nonzero with a visible startup error; GUI/daemon log the failure and continue their primary mode.

To rotate a generated token: stop every Seven API process, remove `api.token`, start one API process, then update clients. Do not delete/replace the file while a server is running because that process correctly continues using the token it loaded at startup.

## Evidence boundaries

Automated integration tests use real loopback sockets and concurrent clients for public health, both authentication headers, chat/tools/status, malformed bodies, content type, limits, overload, method rejection, exception containment, port conflict/release, lazy-agent ownership, token creation races, and shutdown. The clean wheel lifecycle independently starts the installed API on an ephemeral port, reads `/health`, and closes it. This is a local API, not a supported LAN/Internet deployment or multi-user isolation boundary.
