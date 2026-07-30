# Seven Mesh deployment evidence — 2026-07-30

## Outcome

Seven 4.6.0 now provides an opt-in, HMAC-authenticated mesh for node
discovery and relayed messages. The Windows installation and Peanut share one
private mesh secret, retain separate stable node identities, and exchanged
signed messages in both directions.

This is authenticated discovery and messaging, not unrestricted remote
administration. No mesh route exposes Seven's shell, file, browser, model, or
desktop tools.

## Preserved before-state

- Repository branch: `codex/seven-completion`
- Peanut release before deployment: `/opt/seven-4.5.2-2ff5b90`
- Peanut core environment SHA-256:
  `0341cebacfc662b287fb1c2ca438c65c12ba551c8e165074ecaabb2bf6fa43fa`
- Peanut Apache configuration SHA-256:
  `3385d81a4b4d8e14fa064fbdea432fcd48a493a17dbc10535552d916cd5bffd9`
- Peanut services before deployment: `seven-core`, `seven-web`,
  `seven-ollama`, and `httpd` all active.
- Peanut ports before deployment: core on loopback `18765`; no listener on
  `18766`.
- Windows package before deployment: Seven 4.5.2.
- Windows rollback archive:
  `D:\SevenLocal\backups\pre-mesh-4.5.2-20260730T165318.zip`
  with SHA-256
  `D68A263B94BBA4A3B12E68C328EE185A7C165C33EBFC815B1F6C97E678E7B4FD`.
- Existing uncommitted user edits were identified and preserved:
  `deploy/peanut/README.md` SHA-256
  `1F627C5CAEA675469BBA31BBC7549C583415FC3BF3E5EE1B8C4CE5CF233A4929`
  and `docs/COMPLETION_LEDGER.md` SHA-256
  `85D87D51456FF1DE921C7EEB8457DB68AA979C546B926CFDF8F4FF0A25137643`.

## Implemented

- Stable private 128-bit node identity with atomic, concurrent-safe creation.
- HMAC-SHA256 authentication over method, route, body, timestamp, nonce, and
  node ID.
- Timestamp and replay protection.
- Separate mesh SQLite state for peers, nonces, relays, and local inbox/outbox.
- Separate mesh HTTP listener with only health, presence, peer, inbox, and
  message routes.
- Hub sync, message relay, optional LAN multicast discovery, lifecycle
  integration, and mesh tools.
- Opt-in configuration and startup persistence.
- Lean-mode compact dispatcher plus detailed tools for larger tool tiers.
- Apache route `/seven-mesh/` to loopback `127.0.0.1:18766`.
- Recovery after transient sync errors; fatal configuration failures remain
  non-operational.
- Windows identity creation was hardened against transient sharing violations.

## Source and package evidence

- Feature commit: `73ef31129c2b6c97bd114e559f6ae13a1e33bac4`
- Recovery commit: `8392d7ef4243e7ef4b6f9938a04830761a1590d2`
- Both commits pushed to `origin/codex/seven-completion`.
- Final wheel:
  `dist/seven_ai-4.6.0-py3-none-any.whl`
  SHA-256
  `C4942A19556F10374A3F500521128DCA1BB1A105D1CA6E30B41365FF66484600`.
- Final source distribution:
  `dist/seven_ai-4.6.0.tar.gz`
  SHA-256
  `2C1FAF1AA3F3FE9BE2954EF76B6E9070C5510452ED88CC04DCA2BFD3612DA277`.
- Final committed-source archive:
  `dist/seven-4.6.0-8392d7e-source.tar.gz`
  SHA-256
  `8A813E877E9EC199EB9D165D7197A67D81014CA162455B27E9E90BA19F3D389D`.
- Full suite: 226 tests passed. The identity concurrency test also passed ten
  consecutive runs. Only the existing Python `aifc` and `audioop`
  deprecation warnings remained.

## Installed state

### Windows

- Installed package: Seven 4.6.0 at
  `D:\SevenLocal\venv\Lib\site-packages\seven`.
- Active API: `127.0.0.1:18765`, health reports Seven 4.6.0.
- Active process command:
  `D:\SevenLocal\venv\Scripts\python.exe -m seven --api-only`.
- Mesh node: `Seven@USER-PC`,
  ID `cdf5a733dce73c307238a282198c0b07`.
- Mesh config is loaded by the normal, API, quiet, and Windows-startup
  launchers.
- Secret file ACL is restricted to the current Windows user and SYSTEM. The
  secret value is intentionally absent from this document.

### Peanut

- Active immutable release: `/opt/seven-4.6.0-8392d7e`.
- Active API and mesh health: Seven 4.6.0 on loopback ports `18765` and
  `18766`.
- Public mesh health:
  `https://jvrsoftware.co.za/seven-mesh/health` returned HTTP 200 and
  protocol 1.
- Unauthenticated access to `/seven-mesh/v1/peers` returned HTTP 401.
- Mesh node: `Seven@Peanut`,
  ID `4749afa78901a3e0c26ee295cf511296`.
- The server uses its loopback mesh listener as its hub; remote nodes use the
  public HTTPS route. This avoids a local virtual-host hairpin failure.
- Secret file owner/mode: `seven:seven`, `0600`. The value is intentionally
  absent from this document.
- Services after deployment: `seven-core`, `seven-web`, `seven-ollama`, and
  `httpd` active.
- `seven-web` PID `2790154` and `seven-ollama` PID `2533361` did not change;
  only `seven-core` restarted.
- SQLite integrity checks: `seven.db`, `memory.db`, and `seven_mesh.db` all
  returned `ok`.
- Apache configuration test returned `Syntax OK`.
- No sync warnings occurred after the recovery release started. One later
  authentication warning corresponds to the deliberate unsigned HTTP 401
  test.

## Exact two-way runtime proof

- Windows to Peanut:
  message `f22da8b318ad45cfbc27d6f4de42cadf` was stored in Peanut's local inbox
  with the expected sender, target, content, kind, and recovery commit.
- Peanut to Windows:
  message `b6779eb743394706bf8ec4ea7c1f1782` was stored in Windows' local inbox
  with the expected sender, target, content, kind, and recovery commit.

These records prove live discovery, authentication, relay, and receipt across
the public HTTPS route after the final code was installed.

## Rollback evidence

- First Peanut deployment backup:
  `/root/seven-pre-mesh-20260730T150224Z`
- Verified Seven data backup created during it:
  `/root/.seven/backups/seven-backup-20260730T150224850647Z.zip`
- Recovery deployment backup:
  `/root/seven-pre-mesh-recovery-20260730T152026Z`
- The previous immutable releases remain available for a symlink rollback.

## Remaining intentional boundaries

- LAN discovery is disabled on these two nodes because they are not on one
  trusted LAN; hub discovery is active.
- New installations do not join automatically without the shared secret.
  This is intentional authentication, not a missing feature.
- The mesh exchanges presence and messages. It does not grant either node
  root access or silently execute another node's tools.
