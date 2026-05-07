/**
 * dhcDesignStorageProxy — AppSync Lambda resolver for multi-owner S3 access.
 *
 * Handles two AppSync mutations:
 *   - requestDesignReadUrl(smartHomeId, fileName) → { url, expiresAt, contentType }
 *   - requestDesignWriteUrl(smartHomeId, fileName, contentType?) → { url, expiresAt, contentType }
 *
 * Authorization:
 *   - Caller in `dhc-admins` Cognito group → allowed.
 *   - Otherwise: caller's username (cognito:sub) must appear in the
 *     `owners` field of the SmartHomeDesign for the given smartHomeId.
 *
 * Returns a 5-minute pre-signed S3 URL for the key
 *     tenant/{smartHomeId}/{fileName}
 *
 * Env vars (provided automatically by `amplify add function` when you grant
 * Storage and API access):
 *   STORAGE_DHCSTORAGE_BUCKETNAME
 *   API_DIGITALHOMECLOUDBACK_SMARTHOMEDESIGNTABLE_NAME
 *   REGION
 */

const {
  S3Client,
  GetObjectCommand,
  PutObjectCommand,
} = require("@aws-sdk/client-s3");
const { getSignedUrl } = require("@aws-sdk/s3-request-presigner");
const { DynamoDBClient, ScanCommand } = require("@aws-sdk/client-dynamodb");
const { unmarshall } = require("@aws-sdk/util-dynamodb");

const REGION = process.env.REGION || "eu-central-1";
const BUCKET = process.env.STORAGE_DHCSTORAGE_BUCKETNAME;
const SMARTHOMEDESIGN_TABLE =
  process.env.API_DIGITALHOMECLOUDBACK_SMARTHOMEDESIGNTABLE_NAME;
const URL_TTL_SECONDS = 300;

const s3 = new S3Client({ region: REGION });
const ddb = new DynamoDBClient({ region: REGION });

exports.handler = async (event) => {
  const { fieldName, identity, arguments: args = {} } = event;
  const { smartHomeId, fileName, contentType } = args;

  if (!smartHomeId || !fileName) {
    throw new Error("smartHomeId and fileName are required");
  }
  if (!BUCKET || !SMARTHOMEDESIGN_TABLE) {
    throw new Error(
      "Server misconfigured: missing STORAGE_DHCSTORAGE_BUCKETNAME or API_DIGITALHOMECLOUDBACK_SMARTHOMEDESIGNTABLE_NAME"
    );
  }

  // AppSync passes Cognito identity claims through `event.identity` when the
  // resolver auth mode is AMAZON_COGNITO_USER_POOLS.
  const username = identity?.username;
  const groups = identity?.groups || [];
  const isAdmin = groups.includes("dhc-admins");

  if (!username) {
    throw new Error("Unauthenticated");
  }

  // Validate fileName to prevent path traversal in the constructed S3 key.
  if (!/^[A-Za-z0-9._-]+$/.test(fileName)) {
    throw new Error("Invalid fileName: only [A-Za-z0-9._-] characters allowed");
  }

  if (!isAdmin) {
    // Look up SmartHomeDesign by smartHomeId. Schema partition key is `id`
    // (auto-generated UUID), so we scan with a filter. For better performance
    // at scale, add a GSI on smartHomeId via @index in the schema.
    const result = await ddb.send(
      new ScanCommand({
        TableName: SMARTHOMEDESIGN_TABLE,
        FilterExpression: "smartHomeId = :sh",
        ExpressionAttributeValues: { ":sh": { S: smartHomeId } },
        ProjectionExpression: "#id, owners",
        ExpressionAttributeNames: { "#id": "id" },
        Limit: 1,
      })
    );
    const design = (result.Items || []).map(unmarshall)[0];
    if (!design) {
      throw new Error("SmartHomeDesign not found for " + smartHomeId);
    }
    const owners = design.owners || [];
    if (!owners.includes(username)) {
      throw new Error("Not authorized");
    }
  }

  const key = `tenant/${smartHomeId}/${fileName}`;
  let url;
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
    contentType: contentType || null,
  };
};
