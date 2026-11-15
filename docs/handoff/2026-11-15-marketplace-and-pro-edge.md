# Handoff 2026-11-15: the marketplace, DeviceModel retired, digitalhome.pro polish

Start here: `./start-claude.sh` in this repository opens Claude Code with
`../digitalhome-devops-edge` and `../digitalhome-pro-edge` added. Then ask
Claude to read this file.

## What is live (all on `stage`)

| Repo | Commit | What |
|---|---|---|
| core | 57579fd | Edge ↔ data stack cycle broken: the approval Lambda finds the edge tables through SSM (`/dhc/<app>/<branch>/edge-tables/*`) and table-name IAM patterns |
| core | 160a009 | The **marketplace**: one SHACL-validated, versioned Turtle graph per seller (`schema/market/`, `market/graphs/<seller>/v<n>-<token>.ttl`), `MarketSeller` table, edge routes `/edge/v1/market/{sellers,graphs/get,graphs/put,uploads}`, AppSync `market` Lambda, `market-*` editor groups behind the TOTP gate |
| core | cb5f207 | Articles as JSON for the Portal (`marketArticles`, `editMarketArticle` = a fact-level merge); `DeviceInstance.article` |
| core | 0ef31d1 | **DeviceModel retired** (stage table deleted; both envs were empty), import removed |
| portal | fbd6402, 553e30c | Catalogue tab is now **Marketplace**; Sellers panel (dhc-admins); devices keep the article IRI; DeviceModel ops gone |
| designer | 55ec960 | DeviceModel ops removed from the hand-curated GraphQL |
| pro edge | 71a401d | Partner catalogues sync with the marketplace (ADR-0006): three-way merge, mine/theirs conflicts, files by SHA-256, prices never leave |
| pro edge | 009594d | `.pro` in green, new head-with-brain icon, **one folder per workspace** `mydocs/<id>/` (ADR-0007), Rename, **EN/DE/FR** |
| darkfactory | 7869cbf, cfb89aa, this commit | ADR 0016, DH-SPEC-100 §3.1, env-sync for the marketplace, `dhc-device-autodiscovery` 1.1.0, `start-claude.sh`, this handoff |

Stage deploys: core job 21 SUCCEED (0ef31d1), Portal job 47 SUCCEED (553e30c).

Decisions are in `docs/adr/0016-catalogue-is-a-marketplace-of-seller-graphs.md`
(here) and the pro edge's `docs/adr/0006-…` and `0007-one-folder-per-workspace.md`.

## Waiting on you (stage)

1. **Seller `digitalhome-cloud`:** Portal → Inventory → Marketplace → Sellers.
   Create it with kind *platform* and add yourself as an editor. Then sign in
   again, so the token carries `market-digitalhome-cloud`. This needs TOTP.
2. **Check /link approval and My Edges** in the Portal. `edgeDeviceApproval`
   now reads the edge table names from SSM, and `dlab5_devops` cannot read SSM,
   so I could not verify it.
3. **Bring in the discovered devices:** Inventory → Import with the CSVs from
   `experimental/catalogue/` (gitignored, local). Stage 1 saves the models as
   articles of a seller; add the images in the article form.
4. **Pro edge:** it runs on 8773 with the new layout. In Partners →
   digitalhome.cloud marketplace, **Subscribe** to `digitalhome-cloud`, then
   Sync.
   - Backup of the old `mydocs/`:
     `/tmp/claude-1000/-home-frankuwe-digitalhomeCloud/e1a62211-f268-4fde-b423-ee1714298fa1/scratchpad/mydocs-backup-before-ws-folders`.
     It is in a temp folder; copy it out if you want to keep it.
5. **End to end:** edit an article in the Portal and sync, so it arrives on the
   edge. Change another on the edge and sync, so it shows in the Portal. Change
   the same fact on both sides: the edge asks mine or theirs.

## Open work

- **Production.** Core `stage` is 32 commits ahead of `main`. That includes
  the Blockly designer work (branch `claude/electrical-blockly-designer`, not
  ours), so the promotion PR is a release decision. The core `main` backend
  exists since 2026-11-15 (AppSync API `weyg4pfrz5ebfnonr6q2sn4k3q`, bucket
  `amplify-d1abchwrql1qxd-ma-dhcstoragebucket…`).
  - Promoting deletes main's DeviceModel table, which was empty when checked.
  - The Portal/Designer `article` selection needs the promoted schema.
- **Bulk image upload** into a seller: there is no script yet. It would go
  through `marketUploads` as an editor. `upload_catalogue_images.py` is
  retired.
- **Modeler:** show the market vocabulary (`repos/core/schema/market/`) beside
  dhc-core.
- **Pro edge i18n:**
  - Texts the server sends (error messages, the inbox's "what it is" notes)
    are still English.
  - The template-owned header and edge panels are translated from the tool by
    id and exact text. Proper i18n support upstream in python-tool-template and
    template-dlab5-edge would be cleaner.
- **Older device rows** that only have a `modelNumber` match the first seller
  with that reference.
- `env_sync.py` was never dry-run: there is no boto3 here, and the AWS user
  cannot scan the tables.

## Constraints that still hold

- Never commit: `src/aws-exports.js`, `.env.development`,
  `repos/core/amplify_outputs.json`, `.amplify/`, runtime data (labels.json,
  panel-codes.json, cbox.jsonld, dynamic-security.json, device IPs, keys or
  tokens), `.idea/`, `.swp`, `docs/specs/portal-link-page.md`.
- Others' uncommitted work stays untouched:
  - Portal `src/pages/userprofile.js`, `src/ui-components/*`, `yarn.lock`.
  - Designer `src/pages/debug.js`, `.gitignore`, `yarn.lock`.
  - `repos/core` is checked out on `claude/electrical-blockly-designer`, with
    Blockly WIP.
  - Core work went through a separate worktree pushed to `stage` (`git
    worktree add <dir> origin/stage`).
- Kill processes by port (`ss -ltnp`), never `pkill -f`.
- Keep CCU and Hue names; translate on the edge (labels.json).
- Do not change system or security settings; give the user the commands.
  Never enter credentials.
- Pro edge: `core/` and `edge/` are Copier-owned (python-tool-template,
  template-dlab5-edge), so change only tool-owned files. Run the tests with
  `env -u PYTHONPATH ./test.sh`, because the ROS PYTHONPATH leaks in otherwise.

## Useful checks

- **Stack cycles.** Synthesize core locally:
  `NODE_OPTIONS=--preserve-symlinks AWS_BRANCH=stage AWS_APP_ID=d1abchwrql1qxd npx cdk synth --app 'npx tsx amplify/backend.ts' -c amplify-backend-namespace=d1abchwrql1qxd -c amplify-backend-name=stage -c amplify-backend-type=branch -o <dir> -q`.
  Then look at the nested-stack references in the root template: data must not
  reference edge. The script that does this was in this session's scratchpad.
  Rewrite it if needed; it only reads `Fn::GetAtt` into nested stacks.
- **Deploys:** `aws amplify list-jobs --app-id d1abchwrql1qxd --branch-name stage`
  for core, `d2996kz21l6s55` for the Portal.
- **Headless Portal checks:** build, serve `public/` on 127.0.0.1, and drive
  Chrome over CDP. Use a made-up Cognito session in localStorage and answer
  every non-local request locally (`Fetch.requestPaused`), so nothing reaches
  AWS.
