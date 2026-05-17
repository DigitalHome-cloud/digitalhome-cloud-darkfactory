# DigitalHome.Cloud — DarkFactory Workspace

Umbrella repository for the [DigitalHome.Cloud](https://portal.digitalhome.cloud) platform. Aggregates all application repos as git submodules and provides platform-level documentation, specifications, and helper scripts.

## Quick Start

```bash
# Clone with all sub-repos
git clone --recurse-submodules https://github.com/DigitalHome-cloud/digitalhome-cloud-darkfactory.git
cd digitalhome-cloud-darkfactory

# If already cloned without submodules
git submodule update --init --recursive
```

## Applications

| App | Sub-Repo | Port | Production URL |
|-----|----------|------|----------------|
| Portal | `repos/portal/` | 8000 | [portal.digitalhome.cloud](https://portal.digitalhome.cloud) |
| Designer | `repos/designer/` | 8001 | [designer.digitalhome.cloud](https://designer.digitalhome.cloud) |
| Modeler | `repos/modeler/` | 8002 | [modeler.digitalhome.cloud](https://modeler.digitalhome.cloud) |

All apps are Gatsby 5 / React 18 static sites sharing a common AWS Amplify **Gen 2** backend (Cognito, AppSync, DynamoDB, S3), defined in TypeScript in the `repos/core` submodule (`repos/core/amplify/`).

## Development

### First-time setup

```bash
# Install dependencies in each app
(cd repos/portal && yarn install)
(cd repos/designer && yarn install)
(cd repos/modeler && yarn install)

# Boot the Amplify Gen 2 backend (the backend lives in repos/core)
(cd repos/core && npm install && npx ampx sandbox --once)

# Seed each app's src/amplify_outputs.json from the sandbox output
# (dev-start-all.sh also does this automatically)
for app in portal designer modeler; do
  cp repos/core/amplify_outputs.json "repos/$app/src/"
done
```

### Start all dev servers

```bash
./scripts/dev-start-all.sh          # detached, returns the prompt
tail -f /tmp/dhc-*.log              # follow logs
./scripts/dev-stop-all.sh           # stop all servers
./scripts/dev-start-all.sh --clean  # wipe caches before starting
```

### Check status across repos

```bash
./scripts/status.sh
```

### Pull latest changes

```bash
./scripts/pull-all.sh
```

### Re-sync after backend changes

After a backend change (sandbox redeploy or `git pull` with new outputs):

```bash
(cd repos/core && npx ampx sandbox --once)
for app in portal designer modeler; do
  cp repos/core/amplify_outputs.json "repos/$app/src/"
done
```

This regenerates `repos/core/amplify_outputs.json` from the Gen 2 stack and propagates the public Cognito/AppSync/S3 IDs into each app. In CI each app's Hosting build pulls them with `npx ampx generate outputs` instead. See the `dhc-amplify-gen2` skill for the full workflow.

## Documentation

- `docs/architecture/` — Platform architecture overview, authentication flow, Amplify backend integration
- `docs/specs/` — Feature specifications for the modeler and ontology design
- `docs/adr/` — Architecture Decision Records

## Repository Structure

```
repos/          Git submodules for each application
docs/           Platform-level documentation
scripts/        Cross-repo helper scripts
archive/        Historical files
```

## License

See individual sub-repos for license information.
