# ADR 0015: Cognito custom domain `auth.digitalhome.cloud`

Status: Accepted · 2026-05-09

## Context

The Cognito User Pool (`eu-central-1_QTq7NVm2M`) had no Hosted UI domain attached. Each app's embedded `<Authenticator>` component handles email/password sign-in via the SDK directly, so a domain hadn't been needed yet.

Two near-term needs change that:

1. **Re-enabling Google federation.** The notes in `amplify/auth/resource.ts` already document the missing pieces: `secret("GOOGLE_CLIENT_ID")` + `secret("GOOGLE_CLIENT_SECRET")` and a Hosted UI domain to host `/oauth2/idpresponse` (Google's mandatory `redirect_uri`).
2. **Other OAuth/OIDC integrations** — anything that bypasses the embedded `<Authenticator>` (M2M client credentials, Managed Login pages, future SAML IdPs) needs a stable, branded URL.

Provisioning the domain now is the prerequisite for both. We do it without touching the apps so the future Google PR is a pure-additive change.

## Decision

1. **Custom domain over Cognito prefix.** `auth.digitalhome.cloud` keeps the URL on a DHC-owned host, matching the existing `portal.` / `designer.` / `modeler.digitalhome.cloud` pattern. The Cognito-prefix alternative would have shipped faster but locked us into an `*.amazoncognito.com` URL we'd later have to migrate away from.

2. **Console-managed for v1, not IaC.** The custom domain was attached via the AWS Console (Cognito → User Pool → App Integration → Custom domain) using an ACM certificate in `us-east-1`. It is **not** declared in `amplify/backend.ts`. Rationale:
   - The Amplify Gen 2 L2 `defineAuth` doesn't yet expose a `customDomain` prop. The IaC alternative would be a `CfnUserPoolDomain` L1 escape hatch.
   - Adding the L1 construct after the console attachment would cause `DomainAlreadyExistsException` on the next `pipeline-deploy`, and rolling back to a clean IaC-only state would require a domain delete + recreate (interruption to Managed Login).
   - The custom domain is a **one-shot, long-lived resource**. ACM auto-renews the cert as long as the validation CNAME stays in DNS. There are no per-deploy operations on this resource. The IaC drift is real but inert.
   - When the Gen 2 L2 grows native `customDomain` support, we can adopt it then with a one-time CFN import or a coordinated delete/recreate.

3. **Managed Login enabled (Hosted UI v2).** The console attachment defaulted to Cognito's new Managed Login (`Branding version: Managed login` in the console). Branding (logo, colors, custom CSS) is configurable via Cognito Console → Branding → Managed login styles, applied per app client. No code change needed.

4. **DNS in Route 53.** Both records — the ACM validation CNAME and the delegation CNAME (`auth.digitalhome.cloud → d3f3u0naodepqd.cloudfront.net`) — live in the Route 53 hosted zone for `digitalhome.cloud`, alongside the existing `portal.` / `designer.` / `modeler.` subdomains.

5. **`amplify_outputs.json` intentionally untouched.** The user requirement was "domain provisioned now, no client-side changes." When Google federation lands, that PR will use `backend.addOutput({ auth: { oauth: {...} } })` and re-propagate the outputs file to each app.

## Alternatives considered

- **Cognito prefix domain (`*.auth.eu-central-1.amazoncognito.com`).** Rejected: works immediately with no DNS or cert work, but locks us into an unbranded URL. Switching to a custom domain later would mean re-coordinating every OAuth client and external IdP redirect URI, exactly the kind of churn the platform's `*.digitalhome.cloud` scheme was designed to avoid.

- **`CfnUserPoolDomain` L1 escape hatch in `backend.ts`.** Drafted, then reverted (commit history reflects this). The console attachment had already happened by the time the escape hatch would have deployed; the two would collide. Re-considering once the Gen 2 L2 supports `customDomain` natively, or if we ever need to recreate the domain across environments.

- **CDK-managed cert in a cross-region `us-east-1` stack.** Rejected: a single one-shot cert that auto-renews via ACM doesn't justify cross-region stack complexity, custom resource handlers, or the cross-stack reference plumbing.

- **Attach the domain on `stage` too with a parallel `auth-stage.digitalhome.cloud`.** Rejected for now: requires a second cert + second DNS record for a branch where the embedded `<Authenticator>` already covers all sign-in paths. Easy to add later if Hosted-UI cosmetics need stage-level testing.

## Consequences

- **CFN drift for the auth stack.** The `User Pool` resource in CFN is unaware of its custom domain. Anyone reading `amplify/backend.ts` cannot tell that `auth.digitalhome.cloud` is wired up — discoverable only via the Cognito Console or a CLI call. Mitigated by this ADR plus the inline reference comment to follow in `auth/resource.ts` once Google federation lands.
- **Auto-renewal works without intervention.** ACM rotates the cert as long as the validation CNAME stays in the Route 53 zone. Never delete `_6399ae8398d1652a1a2d09c3bfeb5713.auth.digitalhome.cloud`.
- **Apex prerequisite already satisfied.** `digitalhome.cloud` already has an apex A record (the existing subdomains resolve), so Cognito's apex-A requirement is a non-issue.
- **No client behaviour change today.** Portal, Designer, and Modeler keep using `<Authenticator>` exactly as before; the domain sits idle until the Google-federation PR (or any other OAuth-flow PR) activates it.
- **Branding can ship independently of any code change.** Marketing/design can iterate on the Managed Login style in the Cognito Console without involving engineering.

## Verification

```bash
# Confirm domain registration with Cognito
aws cognito-idp describe-user-pool-domain \
  --domain auth.digitalhome.cloud \
  --region eu-central-1
# Expect: Status=ACTIVE, CloudFrontDistribution=d3f3u0naodepqd.cloudfront.net,
#         CustomDomainConfig.CertificateArn pointing at us-east-1.

# Confirm DNS resolves to CloudFront
dig +short auth.digitalhome.cloud
# Expect: d3f3u0naodepqd.cloudfront.net. → AWS edge IPs.

# Confirm Cognito serves /oauth2/authorize on the custom domain
curl -sI "https://auth.digitalhome.cloud/oauth2/authorize?client_id=<app-client-id>&response_type=code&scope=openid&redirect_uri=https://localhost"
# Expect: HTTP/2 302 with set-cookie: XSRF-TOKEN=... and x-amz-cognito-request-id header.
# Note: /.well-known/openid-configuration returns 404 on the custom domain by design — Cognito only
# serves the discovery document on the cognito-idp.<region>.amazonaws.com host.
```

## Related

- AWS Console: Cognito → User Pools → `eu-central-1_QTq7NVm2M` → App Integration → Custom domain.
- Comments: `amplify/auth/resource.ts` lines 15–23 — already document the future Google-federation steps.
- Skill: `.claude/skills/dhc-amplify-gen2/SKILL.md` section 4 — CDK escape-hatch patterns (relevant if/when this domain gets moved into IaC).
- Prior ADRs: 0003 (Amplify Gen 2 backend), 0005 (Cognito auth with group-based access).
