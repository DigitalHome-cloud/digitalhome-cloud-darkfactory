# DH-SPEC-100 — Edge ↔ Cloud Registration (OAuth Device Flow)

| Field | Value |
|---|---|
| Spec ID | `DH-SPEC-100` |
| Title | Edge ↔ Cloud Registration (OAuth Device Flow) |
| Status | **Implemented (stage)** — cloud endpoints + Portal `/link` live on stage as of 2026-07-03; full edge e2e pending the edge `:ro` secrets-mount fix (see §8) |
| Version | 0.1.0 |
| Author | DigitalHome.Edge team |
| Date | 2026-07-03 |
| Scope | Cross-cutting. Defines the cloud-side APIs, DynamoDB tables, and Portal UI needed for a `digitalhome-edge` box to register itself with the cloud, get a device token, and stream telemetry. |
| Referenced by | Portal (new `/link` page), `digitalhome-edge` (`node-red-contrib-dhc-sync`) |
| Related | [DH-SPEC-000] (access tiers) |

---

## 1. Purpose

Ship the cloud half of the edge-registration wire so a fresh `digitalhome-edge` box can:

1. Announce itself to the cloud without any pre-shared credential.
2. Prompt its homeowner to approve the pairing via Cognito login on the Portal.
3. Receive a durable `device_token` bound to a `home_id` + `edge_id`.
4. Post telemetry / heartbeat authenticated by that token, and fetch its C-BOX.

The **edge side is already implemented** in `node-red-contrib-dhc-sync` and blocked only on cloud endpoints being live.

## 2. Source of truth

The wire-level spec is owned by the edge repo and is authoritative for request / response schemas, error semantics, DDB shapes, and lifecycle:

> **`digitalhome-edge/docs/specs/edge-cloud-api.md` v0.2**
> https://github.com/DigitalHome-cloud/digitalhome-edge/blob/main/docs/specs/edge-cloud-api.md

This DH-SPEC exists to track the **dark-factory-team implementation slice**: Amplify Gen2 resources, IAM scoping, Portal page, open questions, and the sign-off checklist. It does **not** duplicate the wire spec — read that first.

## 3. Deliverables (dark factory team)

### 3.1 Amplify Gen2 backend

Four API Gateway HTTP endpoints backed by Lambda + DynamoDB:

| Endpoint | Auth | Purpose |
|---|---|---|
| `POST /edge/v1/device_authorization` | none | Mint a `device_code` + `user_code`, return verification URI. |
| `POST /edge/v1/token` | none (proves `device_code`) | Poll for approval; on approval return `device_token` + `edge_id`. |
| `POST /edge/v1/telemetry` | Bearer `device_token` | Full + delta heartbeat, returns C-BOX freshness flag. |
| `POST /edge/v1/token/rotate` | Bearer `device_token` | Rolling refresh; 60 s dual-valid window. |

Two DynamoDB tables:

| Table | Kind | TTL | Notes |
|---|---|---|---|
| `DeviceCodes` | short-lived pairing state | 10 min | Deleted on approval, denial, or expiry. |
| `EdgeRegistry` | durable per-edge record | none | Sharded by `home_id` for admin-list queries. |

Exact schemas in the wire spec §5.

### 3.2 Portal `/link` page

New authenticated page in the Portal repo. Reads `user_code` from `?user_code=...`, prompts Cognito login if needed, shows:

- The `device_info` metadata the edge sent (hostname, LAN IP, `dhe_version`) so the user can sanity-check "yes that's my box."
- A dropdown of the user's SmartHomes + "create new."
- Approve / Deny buttons.

Approve triggers `PATCH /device_codes/{device_code}` (AppSync, Cognito-authed) which sets `approved=true`, stores `home_id` + `cognito_sub` against the code, and marks the code claimable.

Wire spec §2 (Actors and flow) has the sequence diagram.

### 3.3 Push channel (later phase)

`cloud_endpoints.deploy_channel` returns a WebSocket URL for server-initiated pushes (cbox update notifications, flow deployment). Not required for v1.0 — polling works.

Options in play: API Gateway v2 WebSocket vs. AWS IoT Core MQTT. Decision needed (see §5).

## 4. Dependencies and risks

- **Blocks edge pairing UX end-to-end.** `node-red-contrib-dhc-sync` currently sits in `state=error` on every workstation because these endpoints return DNS failure. Not a hard blocker for the edge (Node-RED runs; MCP wire works) but blocks the pairing dashboard from doing anything useful.
- **Portal repo touch.** `/link` is a new authenticated page — coordinate with the Portal owner. May need to bump the Portal image / Amplify env vars.
- **IAM scoping.** Wire spec §8.1 has the sketch: `edge.telemetry` scope must not grant access to other homes' data. Enforce via DDB conditional expressions keyed on the `edge_id → home_id` binding in `EdgeRegistry`.
- **Rate limits at API Gateway.** Anonymous `device_authorization` needs an IP-based throttle to prevent code exhaustion. Wire spec §7.2 has proposed numbers.

## 5. Open questions (need dark factory decision)

Resolved (2026-07-03) unless noted:

- [x] Base URL: `api.digitalhome.cloud/edge/v1` (matches the edge client's hardcoded default). Stage runs on the API Gateway `execute-api` URL; custom domain deferred to prod cutover.
- [x] Portal `/link`: new page in the **Portal** repo (`src/pages/link.js`).
- [ ] Push-channel transport (WebSocket vs. IoT Core MQTT) — **deferred**, not needed for v1 (polling works).
- [x] `device_token` lifetime: 12 months, rotation 30 d before expiry; 60 s dual-valid grace on rotate.
- [x] `user_code`: 8 chars `XXXX-XXXX`, unambiguous alphabet (no O/0/I/1/L), uppercase, GSI collision-retry. `device_code`: 128-bit `dc_v1_`; `device_token`: 256-bit `dt_v1_` with `edge_id` embedded.
- [x] Rate limits: `/token` 12/min per `device_code` in-handler + API Gateway stage throttle (10 rps, burst 20). IP-based WAF caps are a later hardening step.
- [x] Region: eu-central-1. Multi-region DR (eu-west-1 replica) **deferred**.
- [ ] `cbox_pull` caching — **deferred** to a separate spec.
- [x] Approval UX: dropdown of the user's existing homes **plus** inline create-new (reuses `initiateDigitalHome`).

Remaining deferred items (push channel, DR, `cbox_pull`) are out of the v1 core-pairing slice.

## 6. Acceptance criteria

- [x] `POST /edge/v1/device_authorization` returns a valid RFC 8628 response (200 + `device_code/user_code/verification_uri[_complete]/expires_in/interval`, interval ≥ 5). *Verified live.*
- [ ] Approve flow round-trips end-to-end with a workstation edge: dashboard shows QR → phone → Portal login → Approve → dashboard flips to `linked` state. *Backend + Portal `/link` live; blocked on the edge `:ro` secrets-mount fix (§8) before the box can persist its token.*
- [x] Denied flow: `denyDeviceCode` → `/token` returns `400 access_denied`. *Verified live (handler); dashboard state is the edge side.*
- [x] Tenant isolation: telemetry resolves `home_id`/`edge_id` from the token binding (edge never sends `home_id`), so a token cannot act for another home. *By construction; token embeds `edge_id`.*
- [x] `expired_token` and `access_denied` on `/token` do not leak whether a given `device_code` ever existed (unknown code → `expired_token`). *Verified live.*
- [x] Rate limits: `/token` 12/min per `device_code` (`slow_down`) enforced in-handler; API Gateway stage throttle 10 rps / burst 20. *`slow_down` verified live.*

> **Implementation notes (2026-07-03):** Backed by `repos/core/amplify` — HTTP API v2 under `/edge/v1/*` (4 per-endpoint Lambdas), `DeviceCodes`/`EdgeRegistry` DynamoDB tables, and AppSync `approveDeviceCode`/`denyDeviceCode`/`describeDeviceCode` for the Portal `/link` page. The full RFC 8628 happy path (approve → token → telemetry → rotate, incl. the 60 s rotation grace and code consumption) plus all error codes were verified live. Stage uses the API Gateway `execute-api` URL; the `api.digitalhome.cloud` custom domain is deferred to prod cutover — point the edge box's Node-RED `cloudApiUrl` at the stage URL + `/edge/v1` to test.

## 7. Handoff sign-off

- [ ] Dark factory team acknowledges spec + owns the 4 endpoints + `/link` page.
- [ ] Open questions triaged, defaults confirmed / overridden.
- [ ] Timeline agreed with edge team (edge is unblocked once endpoints go live in stage).
- [ ] Wire spec bumped to v1.0 on freeze.

[DH-SPEC-000]: ./DH-SPEC-000_access-tiers.md
