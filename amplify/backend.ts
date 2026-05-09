import { defineBackend } from "@aws-amplify/backend";
import { Stack } from "aws-cdk-lib";
import { Effect, PolicyStatement } from "aws-cdk-lib/aws-iam";
import { auth } from "./auth/resource";
import { data } from "./data/resource";
import { storage } from "./storage/resource";
import { dhcDesignStorageProxy } from "./functions/dhcDesignStorageProxy/resource";
import { postConfirmation } from "./functions/postConfirmation/resource";

const backend = defineBackend({
  auth,
  data,
  storage,
  dhcDesignStorageProxy,
  postConfirmation,
});

// ─── dhcDesignStorageProxy IAM + env wiring (DH-SPEC-203, audit C-2 v2) ─────
// The Lambda needs:
//   1. S3 GetObject/PutObject/DeleteObject on the bucket (so it can sign URLs).
//   2. DDB Query on the SmartHomeDesign table (so it can verify ownership).
//   3. Two env vars resolving to the bucket name and table name.
// Gen 2 doesn't auto-grant cross-resource IAM when a function is attached as
// a custom-mutation handler, so we do it explicitly here.
const proxyLambda = backend.dhcDesignStorageProxy.resources.lambda;
const bucket = backend.storage.resources.bucket;
const smartHomeDesignTable = backend.data.resources.tables.SmartHomeDesign;

proxyLambda.addToRolePolicy(
  new PolicyStatement({
    effect: Effect.ALLOW,
    actions: ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"],
    resources: [`${bucket.bucketArn}/*`],
  })
);

proxyLambda.addToRolePolicy(
  new PolicyStatement({
    effect: Effect.ALLOW,
    actions: [
      "dynamodb:GetItem",
      "dynamodb:Query",
      "dynamodb:Scan",
      "dynamodb:BatchGetItem",
    ],
    resources: [
      smartHomeDesignTable.tableArn,
      `${smartHomeDesignTable.tableArn}/index/*`,
    ],
  })
);

backend.dhcDesignStorageProxy.addEnvironment(
  "STORAGE_BUCKET_NAME",
  bucket.bucketName
);
backend.dhcDesignStorageProxy.addEnvironment(
  "SMARTHOMEDESIGN_TABLE_NAME",
  smartHomeDesignTable.tableName
);

// ─── DDB Point-in-Time Recovery (audit M-6) ────────────────────────────────
// Gen 2's data tables are wrapped by the AmplifyDynamoDbTable construct (not
// standard CfnTable), so the knob is exposed via cfnResources.amplifyDynamoDb
// Tables[name].pointInTimeRecoveryEnabled. PITR is free up to 35 days of
// recovery window and gives us a rollback path if a table is accidentally
// truncated.
const tablesNeedingPITR = [
  "UserProfile",
  "LibraryItem",
  "SmartHome",
  "SmartHomeDesign",
] as const;
for (const tableName of tablesNeedingPITR) {
  backend.data.resources.cfnResources.amplifyDynamoDbTables[
    tableName
  ].pointInTimeRecoveryEnabled = true;
}

// ─── postConfirmation IAM (Cognito group management) ────────────────────────
// The trigger needs to call cognito-idp:AdminAddUserToGroup, GetGroup, and
// CreateGroup. Gen 2's defineAuth({ triggers }) wires the Lambda invocation
// principal but does NOT auto-grant Cognito admin IAM, so we add it here.
//
// Important: scope to a wildcard userpool ARN, NOT backend.auth.resources
// .userPool.userPoolArn, to avoid a CFN circular dependency. The auth stack
// already references the postConfirmation Lambda (as a trigger), so adding
// a back-reference from the Lambda's role to the User Pool would close the
// cycle. The trigger event carries `event.userPoolId` at runtime — the
// Lambda uses that to address the actual pool — so a region+account-scoped
// wildcard is sufficient and keeps the IAM tight to this AWS account.
const proxyStack = Stack.of(backend.postConfirmation.resources.lambda);
const userPoolWildcardArn = `arn:aws:cognito-idp:${proxyStack.region}:${proxyStack.account}:userpool/*`;

backend.postConfirmation.resources.lambda.addToRolePolicy(
  new PolicyStatement({
    effect: Effect.ALLOW,
    actions: [
      "cognito-idp:AdminAddUserToGroup",
      "cognito-idp:GetGroup",
      "cognito-idp:CreateGroup",
    ],
    resources: [userPoolWildcardArn],
  })
);

export default backend;
