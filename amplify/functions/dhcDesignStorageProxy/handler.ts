/**
 * dhcDesignStorageProxy — AppSync Lambda resolver for multi-owner S3 access.
 *
 * Handles two AppSync mutations:
 *   - requestDesignReadUrl(smartHomeId, fileName)  → { url, expiresAt, contentType }
 *   - requestDesignWriteUrl(smartHomeId, fileName, contentType?) → { url, expiresAt, contentType }
 *
 * Authorization:
 *   - Caller in `dhc-admins` Cognito group → allowed.
 *   - Otherwise: caller's username (cognito:sub) must appear in the
 *     `owners` field of the SmartHomeDesign for the given smartHomeId.
 *
 * Returns a 5-minute pre-signed S3 URL for the key
 *   tenant/{smartHomeId}/{fileName}
 *
 * Env vars (set in backend.ts via addEnvironment):
 *   STORAGE_BUCKET_NAME           — the dhcStorage S3 bucket
 *   SMARTHOMEDESIGN_TABLE_NAME    — the SmartHomeDesign DDB table
 *   AWS_REGION                    — Lambda runtime default
 */

import {
  S3Client,
  GetObjectCommand,
  PutObjectCommand,
} from "@aws-sdk/client-s3";
import { getSignedUrl } from "@aws-sdk/s3-request-presigner";
import {
  DynamoDBClient,
  ScanCommand,
  type ScanCommandInput,
} from "@aws-sdk/client-dynamodb";
import { unmarshall } from "@aws-sdk/util-dynamodb";
import type {
  AppSyncResolverEvent,
  AppSyncIdentityCognito,
} from "aws-lambda";

const REGION = process.env.AWS_REGION || "eu-central-1";
const BUCKET = process.env.STORAGE_BUCKET_NAME;
const SMARTHOMEDESIGN_TABLE = process.env.SMARTHOMEDESIGN_TABLE_NAME;
const URL_TTL_SECONDS = 300;
const FILE_NAME_RE = /^[A-Za-z0-9._-]+$/;

const s3 = new S3Client({ region: REGION });
const ddb = new DynamoDBClient({ region: REGION });

interface ProxyArgs {
  smartHomeId: string;
  fileName: string;
  contentType?: string;
}

interface ProxyResponse {
  url: string;
  expiresAt: string;
  contentType: string | null;
}

export const handler = async (
  event: AppSyncResolverEvent<ProxyArgs>
): Promise<ProxyResponse> => {
  const fieldName = event.info.fieldName;
  // We only authorize the AppSync API with Cognito User Pool, so identity is
  // always the Cognito variant when the resolver is invoked. Narrow the union.
  const identity = event.identity as AppSyncIdentityCognito | undefined;
  const { smartHomeId, fileName, contentType } = event.arguments ?? ({} as ProxyArgs);

  if (!smartHomeId || !fileName) {
    throw new Error("smartHomeId and fileName are required");
  }
  if (!BUCKET || !SMARTHOMEDESIGN_TABLE) {
    throw new Error(
      "Server misconfigured: missing STORAGE_BUCKET_NAME or SMARTHOMEDESIGN_TABLE_NAME"
    );
  }
  if (!FILE_NAME_RE.test(fileName)) {
    throw new Error("Invalid fileName: only [A-Za-z0-9._-] characters allowed");
  }

  const username = identity?.username;
  const groups = identity?.groups || [];
  const isAdmin = groups.includes("dhc-admins");

  if (!username) {
    throw new Error("Unauthenticated");
  }

  if (!isAdmin) {
    const scanInput: ScanCommandInput = {
      TableName: SMARTHOMEDESIGN_TABLE,
      FilterExpression: "smartHomeId = :sh",
      ExpressionAttributeValues: { ":sh": { S: smartHomeId } },
      ProjectionExpression: "#id, owners",
      ExpressionAttributeNames: { "#id": "id" },
      Limit: 1,
    };
    const result = await ddb.send(new ScanCommand(scanInput));
    const design = (result.Items || []).map(
      (it: Record<string, unknown>) => unmarshall(it as Record<string, never>)
    )[0];
    if (!design) {
      throw new Error(`SmartHomeDesign not found for ${smartHomeId}`);
    }
    const owners: string[] = design.owners || [];
    if (!owners.includes(username)) {
      throw new Error("Not authorized");
    }
  }

  const key = `tenant/${smartHomeId}/${fileName}`;
  let url: string;

  if (fieldName === "requestDesignReadUrl") {
    url = await getSignedUrl(
      s3,
      new GetObjectCommand({ Bucket: BUCKET, Key: key }),
      { expiresIn: URL_TTL_SECONDS }
    );
  } else if (fieldName === "requestDesignWriteUrl") {
    url = await getSignedUrl(
      s3,
      new PutObjectCommand({
        Bucket: BUCKET,
        Key: key,
        ContentType: contentType,
      }),
      { expiresIn: URL_TTL_SECONDS }
    );
  } else {
    throw new Error(`Unknown field: ${fieldName}`);
  }

  return {
    url,
    expiresAt: new Date(Date.now() + URL_TTL_SECONDS * 1000).toISOString(),
    contentType: contentType ?? null,
  };
};
