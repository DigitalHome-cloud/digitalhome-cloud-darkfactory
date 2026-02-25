# ADR 0005: Cognito Authentication with Group-Based Access Control

## Status

Accepted

## Date

2024-12 (documented retroactively 2025-02)

## Context

The platform needs authentication that:
- Works across multiple frontend apps sharing one backend
- Supports social login (Google) alongside email/password
- Controls per-app feature access (not everyone can use the Designer or Operator)
- Provides a graceful demo mode for unauthenticated visitors

## Decision

We use **Amazon Cognito User Pool** with **Cognito groups** for access control:

- **User Pool** handles registration, login, Google OAuth, and token issuance
- **Groups** (embedded in the ID token as `cognito:groups`) gate feature access:
  - `dhc-users` — SmartHome Designer access
  - `dhc-operators` — SmartHome Operator access (future)
  - `dhc-admins` — Modeler editing access (future)
- **AuthContext** in each app reads the session and exposes `authState`, `groups`, `hasGroup()`
- **Demo mode** (`authState === "demo"`) is the default for unauthenticated users — the app is usable with limited features, no login required
- **Identity Pool** is optional — only needed for direct AWS service access (S3), not for User Pool auth

### Resilience pattern

`AuthContext` calls `getCurrentUser()` before `fetchAuthSession()`. If the Identity Pool is misconfigured, auth still works — the user stays authenticated with groups potentially missing.

## Consequences

### Positive

- One login works across portal, designer, modeler (shared User Pool)
- Group-based gating is simple and managed in AWS Console — no app code changes to grant/revoke
- Demo mode means the platform is always accessible, lowering the barrier to exploration
- Google OAuth reduces friction for new users

### Negative

- Cognito groups are coarse-grained — no per-SmartHome permissions yet
- Group membership requires AWS Console or API access to manage (no self-service UI yet)
- AuthContext is duplicated across repos rather than shared as a package
