# Ollama Runtime and Model Management

Seven uses the loopback Ollama endpoint configured by `OLLAMA_URL` (default `http://127.0.0.1:11434`). The modern tool registry exposes real operations:

- `ollama_status`
- `ollama_list`
- `ollama_show`
- `ollama_pull`
- `ollama_copy`
- `ollama_delete`
- `ollama_load`
- `ollama_unload`

Pull operations stream the local server response and may consume substantial bandwidth, disk and time. Their timeout is controlled by `SEVEN_OLLAMA_OPERATION_TIMEOUT` (default 1800 seconds).

Load uses an empty generation request with a configurable `keep_alive`. Unload uses Ollama's supported `keep_alive: 0` request. Model removal calls the local delete endpoint and is audited like every other Seven tool.

## Live baseline (2026-07-11)

- Ollama version: 0.31.2
- Installed models observed: seven
- Required Seven defaults observed: `qwen2.5:7b`, `llama3.2-vision:latest`
- Running models during audit: none

This replaces `_legacy/v3/integrations/ollama_manager.py`. The modern manager has no GUI coupling and does not keep a second model-state database; Ollama remains authoritative.
