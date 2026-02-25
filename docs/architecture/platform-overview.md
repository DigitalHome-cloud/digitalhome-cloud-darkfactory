# DigitalHome Cloud – Architecture & Environment Overview

This document provides a short initial version of the DigitalHome.Cloud environment
strategy and platform architecture.

---

## 1. Environment Strategy

DigitalHome.Cloud uses four environment tiers:

- **alpha** – experimental, internal only  
- **beta** – early testing with selected users  
- **stage** – release candidate, production‑like  
- **prod** – live production

### URL Pattern
Each application follows:

- **Production:** `<app>.digitalhome.cloud`
- **Stage:** `stage-<app>.digitalhome.cloud`
- **Beta:** `beta-<app>.digitalhome.cloud`
- **Alpha:** `alpha-<app>.digitalhome.cloud`

### Branch → Environment Mapping

| Branch | Environment | URL Pattern |
|--------|-------------|-------------|
| main   | prod        | `<app>.digitalhome.cloud` |
| stage  | stage       | `stage-<app>.digitalhome.cloud` |
| beta   | beta        | `beta-<app>.digitalhome.cloud` |
| alpha  | alpha       | `alpha-<app>.digitalhome.cloud` |

### Release Flows

**Minor releases:**
```
stage → prod
```

**Major releases:**
```
alpha → beta → stage → prod
```
Notes:

- Not every repo must use `alpha` and `beta` branches from day one; they can be introduced when major features require them.
- Hotfix branches (`hotfix/*`) are short-lived and usually merge into `main` and `stage`.
---

## 2. Platform Architecture (Short Overview)

DigitalHome.Cloud consists of:

- **Portal** (Gatsby + Amplify Hosting)
- **DHC SmartHome Designer** (Gatsby + Blockly)
- **DHC Modeler** (Gatsby + Three.js / react-force-graph-3d — 3D ontology viewer)
- **Future Operator App**

All frontend apps use:
- **Amazon Cognito** (authentication & groups)
- **Amplify Hosting** (per‑branch deployments)
- **Serverless APIs** (AppSync/Lambda)
- **Amazon S3** (ontology files, real estate models, runtime JSON-LD)

A simplified logical flow:

```
Browser
   ↓
Gatsby Frontends (Portal, Designer, Modeler)
   ↓
Cognito (Auth)
   ↓
AppSync / Lambda (APIs)
   ↓
S3 (Semantic Core & Instance Models)
```

GitHub (DigitalHome-cloud organization) hosts:
- Portal
- Designer (SmartHome Designer)
- Modeler (3D ontology viewer + semantic-core ontology files)
- Documentation

---

## 3. Purpose of This Document

This is a short initial overview to make the environment and architecture strategy
easy to read and reference. A full version will follow in the `digitalhome-cloud-docs`
repository.
