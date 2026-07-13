# Seven 4.4.0 release evidence

Candidate code commit: `a452f9f62189edd4b3575f172181f2bc94028b4c`  
Evidence date: 2026-07-13 (Africa/Johannesburg)  
Source branch: `codex/complete-seven`

## Automated release result

| Gate | Result | Evidence |
|---|---|---|
| Current suite | Pass | 125 tests on local Windows Python 3.13; hosted Ubuntu Python 3.11, 3.12 and 3.13 all pass |
| Compile | Pass | `python -m compileall -q seven scripts` |
| Inventory | Pass | 533 non-generated paths; 216/216 legacy Python files parse; zero unresolved dispositions |
| Repository contract | Pass | zero production legacy imports; all local documentation links resolve; README 98-tool claim matches default registry |
| Universal lock | Pass | 281 packages; `uv lock --check`; provenance snapshot generated; seven publisher declarations remain explicitly unresolved |
| Wheel | Pass | `seven_ai-4.4.0-py3-none-any.whl`; SHA-256 `1118934b9f8b09eb6004132a421aa11f6dbd67a929d87660d432b76a979f713b`; version/assets/content verifier passes |
| Clean install/uninstall | Pass | hosted Windows core and Ubuntu selected-optionals lifecycles; CLI, schema, API health, `pip check`, console removal and import absence |
| Upgrade | Pass | freshly built baseline commit `08d8b4f`: metadata 4.3.0/runtime `4.3.0-complete`/schema 0/no packaged identity; actual pip uninstall then 4.4.0 install; schema 4/four identity files/healthy API; clean uninstall |
| Live host truth probe | Partial pass | shell, file, web search/fetch, HTTP browser, screenshot, window listing, belief, semantic memory, planning, skill and freewill probes pass; Ollama is not installed/running on this verification host |
| Secret/artifact scan | Pass within declared patterns | no tracked private-key, common GitHub/OpenAI/AWS token pattern, credential filename, runtime database, build cache or package output found |
| Hosted CI | Pass | [PR run 29276701830](https://github.com/LoSkroefie/seven-ai/actions/runs/29276701830) and [push run 29276697624](https://github.com/LoSkroefie/seven-ai/actions/runs/29276697624) |

The wheel hash is for the locally built candidate from the code commit. The evidence document itself is a subsequent documentation-only change, so rebuilding after its commit can change source-archive/inventory-derived bytes; GitHub CI independently rebuilds and validates its exact checkout.

## Manual/unavailable evidence

Not executed or not available on this host: a real Ollama text/vision conversation, audible microphone/speaker loop, physical webcam contention matrix, multi-monitor/Wayland/HiDPI behavior, physical robot motor driver/emergency stop, real MCP client interoperability, authenticated SSH target, installed login greeting, macOS lifecycle, and 24-hour soak. No claim for those scenarios is made. They remain listed in `KNOWN_LIMITATIONS.md` and the manual matrix in `RELEASE_CHECKLIST.md`.

## Release decision

The independent Seven core package is eligible for a truthful 4.4.0 beta release: its software/package/migration gates pass and unavailable hardware/provider scenarios are explicitly excluded from the proof. It is not evidence that every optional device or external service works.
