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
| Digital Twin Demo | `repos/digital-twin-demo/` | — | [GitHub](https://github.com/DigitalHome-cloud/dhc-digital-twin-demo) |

All apps are Gatsby 5 / React 18 static sites sharing a common AWS Amplify Gen1 backend (Cognito, AppSync, DynamoDB, S3).

## Development

### First-time setup

```bash
# Install dependencies in each app
(cd repos/portal && yarn install)
(cd repos/designer && yarn install)
(cd repos/modeler && yarn install)

# Pull Amplify backend config (once, at umbrella root)
amplify pull

# Symlink amplify/ + aws-exports.js into each repo, generate .env.development, run codegen
./scripts/sync-env.sh
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

After `amplify pull` or switching branches with backend changes:

```bash
./scripts/sync-env.sh
```

This re-symlinks `amplify/` and `aws-exports.js`, regenerates `.env.development`, and runs `amplify codegen` to update GraphQL types.

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
