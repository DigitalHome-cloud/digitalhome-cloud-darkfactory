#!/usr/bin/env python3
"""
env_sync.py — migrate and sync data between two DigitalHome.Cloud backends
(the core app's Amplify branches: stage and main = prod).

Every backend is its own Cognito pool, tables and bucket, so moving data
means copying it and translating identities. Nothing is hard-coded: each
environment's resources are found from the core Amplify app's branch stack.

  plan   say what would change (the default; writes nothing)
  apply  do it

Parts (--only, default all):

  reference  LibraryItem, Area rows; the marketplace (MarketSeller rows,
             their catalogue graphs under market/graphs/ and files under
             public/market/, ADR 0016); S3 public/ontology/,
             public/weather/ (the data lake)
  groups     every Cognito group (name, description, precedence)
  users      the users named with --user EMAIL: created in the target pool
             (no password; they use "Forgot password", or --invite sends
             Cognito's invitation), added to the same groups
  homes      DigitalHome rows (all, or --home ID) with their SmartHomeDesign
             and DeviceInstance rows, the users' UserProfile rows, and the
             home's S3 objects (Private|Public/DigitalHomes/<id>/,
             tenant/<id>/, public/smarthomes/<id>/)

A user's ID (Cognito sub) cannot be carried over: the target pool mints its
own. Users are matched by email, and every source sub of a migrated user is
rewritten to the target sub in the rows copied (owners, createdBy, owner).
Owners who are not migrated are dropped from a home's owners; a home left
with no owner is skipped unless --keep-orphans.

Two-step sign-in secrets cannot be read from Cognito, so each user sets up
their authenticator again in the target environment.

Not copied, on purpose: edges and device codes (an edge links to one cloud),
passwords, MFA secrets.

Rows are written when missing or different; a target row with a newer
updatedAt is left alone and reported. S3 objects are copied when missing or
of a different ETag. Nothing is deleted.

  .venv/bin/python scripts/env-sync/env_sync.py plan  --from stage --to main --user you@example.org
  .venv/bin/python scripts/env-sync/env_sync.py apply --from stage --to main --user you@example.org
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from typing import Dict, Iterable, List, Optional, Set

import boto3
from boto3.dynamodb.types import TypeDeserializer, TypeSerializer
from botocore.exceptions import ClientError

CORE_APP = "digitalhome-cloud-core"
# MarketSeller is a plain CDK table (backend.ts), not an Amplify model; a
# seller row names its graph's S3 key, so rows and market/graphs/ go together.
# market/staging/ holds uploads in flight and is never copied.
REFERENCE_TABLES = ("LibraryItem", "Area", "MarketSeller")
REFERENCE_PREFIXES = ("public/ontology/", "public/weather/", "market/graphs/", "public/market/")
HOME_TABLES = ("SmartHomeDesign", "DeviceInstance")          # rows with smartHomeId
PARTS = ("reference", "groups", "users", "homes")

_ser, _de = TypeSerializer(), TypeDeserializer()


def plain(item: Dict) -> Dict:
    return {k: _de.deserialize(v) for k, v in item.items()}


def typed(item: Dict) -> Dict:
    return {k: _ser.serialize(v) for k, v in item.items()}


# ------------------------------------------------------------ discovery ----

class Env:
    """One backend: the core app's branch stack, resolved to its resources."""

    def __init__(self, branch: str, session: boto3.Session):
        self.branch = branch
        amp = session.client("amplify")
        apps = [a for a in amp.list_apps(maxResults=100)["apps"] if a["name"] == CORE_APP]
        if not apps:
            sys.exit(f"no Amplify app named {CORE_APP}")
        try:
            stack = amp.get_branch(appId=apps[0]["appId"], branchName=branch)["branch"]["backend"]["stackArn"]
        except (ClientError, KeyError):
            sys.exit(f"{CORE_APP} has no deployed backend on branch {branch}")
        cfn = session.client("cloudformation")
        self.pool = self.bucket = ""
        self.tables: Dict[str, str] = {}

        def walk(name: str) -> None:
            for page in cfn.get_paginator("list_stack_resources").paginate(StackName=name):
                for r in page["StackResourceSummaries"]:
                    t, lid, pid = r["ResourceType"], r["LogicalResourceId"], r.get("PhysicalResourceId", "")
                    if t == "AWS::CloudFormation::Stack":
                        walk(pid)
                    elif t == "AWS::Cognito::UserPool":
                        self.pool = pid
                    elif t == "AWS::S3::Bucket" and lid.startswith("dhcStorageBucket"):
                        self.bucket = pid
                    elif t == "Custom::AmplifyDynamoDBTable" and lid.endswith("Table"):
                        self.tables[lid[:-len("Table")]] = pid
                    elif t == "AWS::DynamoDB::Table" and lid.startswith("MarketSeller"):
                        self.tables["MarketSeller"] = pid
        walk(stack)
        if not (self.pool and self.bucket and self.tables):
            sys.exit(f"{branch}: could not find the user pool, bucket and tables in its stack")
        self.idp = session.client("cognito-idp")
        self.ddb = session.client("dynamodb")
        self.s3 = session.client("s3")

    # ---- Cognito
    def groups(self) -> List[Dict]:
        out = []
        for page in self.idp.get_paginator("list_groups").paginate(UserPoolId=self.pool):
            out += page["Groups"]
        return out

    def user_by_email(self, email: str) -> Optional[Dict]:
        got = self.idp.list_users(UserPoolId=self.pool, Filter=f'email = "{email}"', Limit=2)["Users"]
        return got[0] if got else None

    def user_groups(self, username: str) -> List[str]:
        out = []
        for page in self.idp.get_paginator("admin_list_groups_for_user").paginate(
                UserPoolId=self.pool, Username=username):
            out += [g["GroupName"] for g in page["Groups"]]
        return out

    # ---- DynamoDB
    def scan(self, model: str) -> List[Dict]:
        out = []
        for page in self.ddb.get_paginator("scan").paginate(TableName=self.tables[model]):
            out += [plain(i) for i in page["Items"]]
        return out

    def key_of(self, model: str) -> List[str]:
        d = self.ddb.describe_table(TableName=self.tables[model])["Table"]["KeySchema"]
        return [k["AttributeName"] for k in d]

    def get(self, model: str, key: Dict) -> Optional[Dict]:
        got = self.ddb.get_item(TableName=self.tables[model], Key=typed(key)).get("Item")
        return plain(got) if got else None

    def put(self, model: str, item: Dict) -> None:
        self.ddb.put_item(TableName=self.tables[model], Item=typed(item))

    # ---- S3
    def objects(self, prefix: str) -> Dict[str, Dict]:
        out = {}
        for page in self.s3.get_paginator("list_objects_v2").paginate(Bucket=self.bucket, Prefix=prefix):
            for o in page.get("Contents", []):
                out[o["Key"]] = {"etag": o["ETag"], "size": o["Size"]}
        return out


# ---------------------------------------------------------------- sync ----

class Sync:
    def __init__(self, src: Env, dst: Env, apply: bool, users: List[str], homes: List[str],
                 keep_orphans: bool, invite: bool):
        self.src, self.dst, self.apply = src, dst, apply
        self.emails, self.home_ids = users, homes
        self.keep_orphans, self.invite = keep_orphans, invite
        self.subs: Dict[str, str] = {}           # source sub -> target sub
        self.counts: Dict[str, int] = defaultdict(int)
        self.notes: List[str] = []

    def say(self, what: str, n: int = 1) -> None:
        self.counts[what] += n

    # ---- rows
    def copy_row(self, model: str, item: Dict, keys: List[str]) -> None:
        key = {k: item[k] for k in keys}
        have = self.dst.get(model, key)
        if have == item:
            self.say(f"{model}: same")
            return
        if have and str(have.get("updatedAt", "")) > str(item.get("updatedAt", "")):
            self.say(f"{model}: newer in target, kept")
            return
        self.say(f"{model}: {'update' if have else 'new'}")
        if self.apply:
            self.dst.put(model, item)

    def remap(self, value):
        """Rewrite every source sub to its target sub, in strings only, so
        numbers, sets and binary values keep their DynamoDB types."""
        if isinstance(value, str):
            for old, new in self.subs.items():
                value = value.replace(old, new)
            return value
        if isinstance(value, dict):
            return {k: self.remap(v) for k, v in value.items()}
        if isinstance(value, list):
            return [self.remap(v) for v in value]
        if isinstance(value, set):
            return {self.remap(v) for v in value}
        return value

    # ---- S3
    def copy_prefix(self, prefix: str) -> None:
        have = self.dst.objects(prefix)
        for key, meta in self.src.objects(prefix).items():
            if have.get(key, {}).get("etag") == meta["etag"]:
                self.say("S3: same")
                continue
            self.say("S3: copy")
            self.say("S3: bytes", meta["size"])
            if self.apply:
                self.dst.s3.copy({"Bucket": self.src.bucket, "Key": key}, self.dst.bucket, key)

    # ---- parts
    def reference(self) -> None:
        for model in REFERENCE_TABLES:
            if model not in self.src.tables or model not in self.dst.tables:
                self.notes.append(f"{model}: missing on one side, skipped")
                continue
            keys = self.src.key_of(model)
            for item in self.src.scan(model):
                self.copy_row(model, item, keys)
        for prefix in REFERENCE_PREFIXES:
            self.copy_prefix(prefix)

    def groups(self) -> None:
        have = {g["GroupName"] for g in self.dst.groups()}
        for g in self.src.groups():
            if g["GroupName"] in have:
                self.say("group: exists")
                continue
            self.say("group: new")
            if self.apply:
                args = {"UserPoolId": self.dst.pool, "GroupName": g["GroupName"]}
                if g.get("Description"):
                    args["Description"] = g["Description"]
                if g.get("Precedence") is not None:
                    args["Precedence"] = g["Precedence"]
                self.dst.idp.create_group(**args)

    def users(self) -> None:
        for email in self.emails:
            src = self.src.user_by_email(email)
            if not src:
                self.notes.append(f"{email}: not in the source pool")
                continue
            attrs = {a["Name"]: a["Value"] for a in src["Attributes"]}
            dst = self.dst.user_by_email(email)
            if not dst:
                self.say("user: new")
                if self.apply:
                    keep = [{"Name": n, "Value": v} for n, v in attrs.items()
                            if n not in ("sub", "email_verified", "identities") and not n.startswith("dev:")]
                    keep.append({"Name": "email_verified", "Value": "true"})
                    args = {"UserPoolId": self.dst.pool, "Username": email, "UserAttributes": keep,
                            "DesiredDeliveryMediums": ["EMAIL"]}
                    if not self.invite:
                        args["MessageAction"] = "SUPPRESS"
                    dst = self.dst.idp.admin_create_user(**args)["User"]
            else:
                self.say("user: exists")
            if dst:
                dsub = {a["Name"]: a["Value"] for a in dst["Attributes"]}["sub"]
                self.subs[attrs["sub"]] = dsub
                if src["Username"] != attrs["sub"]:
                    self.subs[src["Username"]] = dst["Username"]
                target_groups = set(self.dst.user_groups(dst["Username"])) if dst.get("UserStatus") else set()
            else:
                self.subs[attrs["sub"]] = f"<new user {email}>"
                target_groups = set()
            for g in self.src.user_groups(src["Username"]):
                if g in target_groups:
                    continue
                self.say("membership: add")
                if self.apply and dst:
                    try:
                        self.dst.idp.admin_add_user_to_group(UserPoolId=self.dst.pool,
                                                             Username=dst["Username"], GroupName=g)
                    except self.dst.idp.exceptions.ResourceNotFoundException:
                        self.notes.append(f"group {g} missing in target: run with groups")

    def homes(self) -> None:
        mapped: Set[str] = set(self.subs)
        wanted = set(self.home_ids)
        copied: List[str] = []
        for h in self.src.scan("DigitalHome"):
            hid = h["smartHomeId"]
            if wanted and hid not in wanted:
                continue
            owners = [o for o in (h.get("owners") or []) if o in mapped]
            if not owners and not self.keep_orphans:
                self.notes.append(f"home {hid}: no migrated owner, skipped (use --user, or --keep-orphans)")
                continue
            dropped = len(h.get("owners") or []) - len(owners)
            if dropped:
                self.notes.append(f"home {hid}: {dropped} owner(s) not migrated, left out")
            item = self.remap({**h, "owners": owners})
            self.copy_row("DigitalHome", item, ["smartHomeId"])
            copied.append(hid)
        for model in HOME_TABLES:
            if model not in self.src.tables:
                continue
            keys = self.src.key_of(model)
            for item in self.src.scan(model):
                if item.get("smartHomeId") in copied:
                    self.copy_row(model, self.remap(item), keys)
        if "UserProfile" in self.src.tables:
            keys = self.src.key_of("UserProfile")
            for item in self.src.scan("UserProfile"):
                if any(s in json.dumps(item, default=str) for s in mapped):
                    self.copy_row("UserProfile", self.remap(item), keys)
        for hid in copied:
            for prefix in (f"Private/DigitalHomes/{hid}/", f"Public/DigitalHomes/{hid}/",
                           f"tenant/{hid}/", f"public/smarthomes/{hid}/"):
                self.copy_prefix(prefix)

    def run(self, parts: Iterable[str]) -> None:
        parts = list(parts)
        for p in PARTS:                  # always in this order: groups before users before homes
            if p in parts or (p == "users" and "homes" in parts and self.emails):
                getattr(self, p)()


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("action", choices=("plan", "apply"))
    ap.add_argument("--from", dest="src", required=True, help="source branch: stage or main")
    ap.add_argument("--to", dest="dst", required=True, help="target branch: main or stage")
    ap.add_argument("--only", default=",".join(PARTS), help=f"comma list of {', '.join(PARTS)}")
    ap.add_argument("--user", action="append", default=[], help="email of a user to migrate (repeatable)")
    ap.add_argument("--home", action="append", default=[], help="a SmartHome ID (repeatable; default all)")
    ap.add_argument("--keep-orphans", action="store_true", help="copy homes none of whose owners is migrated")
    ap.add_argument("--invite", action="store_true", help="send Cognito's invitation email to new users")
    ap.add_argument("--profile", default=None, help="AWS profile")
    a = ap.parse_args(argv)
    if a.src == a.dst:
        ap.error("--from and --to must differ")
    parts = [p.strip() for p in a.only.split(",") if p.strip()]
    bad = set(parts) - set(PARTS)
    if bad:
        ap.error(f"unknown part(s): {', '.join(sorted(bad))}")
    session = boto3.Session(profile_name=a.profile)
    src, dst = Env(a.src, session), Env(a.dst, session)
    s = Sync(src, dst, a.action == "apply", a.user, a.home, a.keep_orphans, a.invite)
    s.run(parts)
    print(f"{a.action}: {a.src} -> {a.dst} ({', '.join(parts)})")
    for k in sorted(s.counts):
        v = s.counts[k]
        print(f"  {k:32} {v / 1e6:.1f} MB" if k == "S3: bytes" else f"  {k:32} {v}")
    for n in s.notes:
        print(f"  note: {n}")
    if a.action == "plan":
        print("Nothing was written. Run again with apply to do it.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
