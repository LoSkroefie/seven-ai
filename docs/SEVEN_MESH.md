# Seven Mesh

Seven Mesh lets separate Seven installations identify one another, report
presence, and exchange durable messages. It is opt-in. A normal Seven install
continues to operate with the mesh disabled.

## What is implemented

- A stable random 128-bit node ID stored in `mesh_identity.json`.
- A separate `seven_mesh.db` containing peers, replay nonces, relay queues, and
  the local inbox/outbox.
- HMAC-SHA256 authentication on every presence, peer, inbox, and message
  request. Signed requests include method, route, body hash, timestamp, nonce,
  and node ID.
- Timestamp and nonce replay protection.
- Bounded request bodies, message sizes, relay lifetime, and peer metadata.
- A rendezvous/relay listener for machines behind NAT.
- Optional authenticated LAN multicast discovery.
- One compact `mesh` tool for small models, plus the detailed `mesh_status`,
  `mesh_peers`, `mesh_inbox`, and `mesh_send` tools for normal/full profiles.
- Durable `mesh_message_received` events in Seven's main memory.

Mesh messages are data, not commands. Receiving a message never invokes the
shell, opens an application, runs a tool, or grants another machine access.

## Trust and confidentiality

Every authorized node currently shares one owner-controlled mesh secret. This
is appropriate for one owner's machines but means a compromised member must be
removed by rotating the shared secret.

HMAC provides identity, integrity, and replay protection; it is not encryption.
Use HTTPS for the Peanut/WAN rendezvous route. Plain HTTP LAN endpoints expose
message content to the local network even though attackers cannot forge or
alter accepted messages. Leave LAN discovery off on untrusted networks.

## Configuration

Create one random secret containing at least 32 characters and store the same
value in a private file on every trusted machine. Never put it in Git.

```text
SEVEN_MESH_ENABLED=1
SEVEN_MESH_SECRET_FILE=/private/path/mesh.secret
SEVEN_MESH_NODE_NAME=Seven@UniqueMachineName
SEVEN_MESH_LISTEN=1
SEVEN_MESH_LISTEN_HOST=127.0.0.1
SEVEN_MESH_LISTEN_PORT=18766
SEVEN_MESH_HUB_URL=https://example.com/seven-mesh
SEVEN_MESH_ADVERTISE_URL=https://example.com/seven-mesh
SEVEN_MESH_SYNC_SECONDS=30
SEVEN_MESH_LAN_DISCOVERY=0
```

For a desktop-only LAN hub, bind the separate mesh listener to `0.0.0.0`, set
an address other LAN machines can reach in `SEVEN_MESH_ADVERTISE_URL`, permit
only TCP port 18766 on the private firewall profile, and enable LAN discovery.
Do not expose that plain HTTP listener to the Internet.

## Peanut rendezvous route

On Peanut, the mesh listener binds only to `127.0.0.1:18766`. Apache should
proxy `/seven-mesh/` to that loopback listener over the existing HTTPS virtual
host:

```apache
ProxyPass        /seven-mesh/ http://127.0.0.1:18766/ nocanon retry=0 timeout=30
ProxyPassReverse /seven-mesh/ http://127.0.0.1:18766/
```

The health route may be read without authentication and returns only the
service name and protocol version. All peer and message routes require signed
mesh requests.

## Operator checks

1. `mesh_status` must show `operational: true`, `started: true`, and
   `store_integrity: ok`.
2. `mesh_peers` must show the other node's exact node ID and `online: true`.
3. Send a harmless message with `mesh_send`.
4. On the target, `mesh_inbox` must return the same message ID, sender node ID,
   content, and timestamp.
5. A repeated signed request must return HTTP 401, proving replay rejection.

Do not call the mesh deployed or connected until the exact two-node exchange
has passed through the intended network route.
