import { defineBackend } from "@aws-amplify/backend";
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

// ─── postConfirmation IAM (Cognito group management) ────────────────────────
// The trigger needs to call cognito-idp:AdminAddUserToGroup on the same User
// Pool. Gen 2 auto-grants this when the trigger is declared in defineAuth(),
// so no explicit IAM here.

export default backend;
