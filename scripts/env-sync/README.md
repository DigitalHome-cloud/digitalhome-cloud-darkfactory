# env-sync — move data between stage and prod

Each Amplify branch of `digitalhome-cloud-core` is its own backend: its own
Cognito user pool, DynamoDB tables and S3 bucket. `env_sync.py` copies what
should travel between them and translates user identities on the way.
Run `env_sync.py --help` for the full description.

```bash
# what would change (writes nothing)
.venv/bin/python scripts/env-sync/env_sync.py plan  --from stage --to main --user you@example.org
# do it
.venv/bin/python scripts/env-sync/env_sync.py apply --from stage --to main --user you@example.org
# only the reference data, the other way round
.venv/bin/python scripts/env-sync/env_sync.py plan --from main --to stage --only reference
```

| Part | What travels |
|---|---|
| `reference` | LibraryItem, Area rows; the marketplace (MarketSeller rows, `market/graphs/`, `public/market/`; ADR 0016); `public/ontology/`, `public/weather/` |
| `groups` | every Cognito group |
| `users` | the users named with `--user`, created without a password, in the same groups |
| `homes` | DigitalHome rows with their designs, devices, profiles and S3 files |

**Identities.** The target pool mints its own user IDs. Users are matched by
email, and their source IDs are rewritten to the target IDs in every copied
row. Owners not migrated are left out; a home with none left is skipped.

**Not copied:** passwords, two-step (authenticator) secrets, edges and
device codes. A migrated user signs in with "Forgot password" (or `--invite`)
and sets up two-step sign-in again; an edge links to each cloud separately.

**Permissions.** The AWS identity running it needs, on both backends:
Cognito `ListGroups`, `CreateGroup`, `ListUsers`, `AdminCreateUser`,
`AdminListGroupsForUser`, `AdminAddUserToGroup`; DynamoDB `DescribeTable`,
`Scan`, `GetItem`, `PutItem` on the Amplify model tables; S3 `ListBucket`,
`GetObject`, `PutObject` on the storage buckets; read access to Amplify and
CloudFormation to find them.

Nothing is ever deleted, and a target row with a newer `updatedAt` is kept.
