/**
 * Drop-in replacement for repos/designer/src/utils/s3.js after Phase 1d
 * (`amplify push`) succeeds and the new mutations exist in AppSync.
 *
 * Demo SmartHomes (DE-DEMO-01, FR-DEMO-01, BE-DEMO-01) keep using the
 * direct uploadData / downloadData flow against `public/smarthomes/...`.
 * Real SmartHomes route through the new AppSync mutations:
 *   1. requestDesignReadUrl  → 5-min pre-signed S3 GET URL
 *   2. requestDesignWriteUrl → 5-min pre-signed S3 PUT URL
 * The Lambda dhcDesignStorageProxy enforces SmartHomeDesign.owners
 * membership before signing.
 *
 * Multi-owner-safe: any user in SmartHomeDesign.owners can both read
 * and write the design.
 */
import { uploadData, downloadData } from "aws-amplify/storage";
import { generateClient } from "aws-amplify/api";
import { isDemoSmartHome } from "../context/SmartHomeContext";

const S3_PREFIX_ONTOLOGY = "ontology";
const S3_PREFIX_SMARTHOMES = "smarthomes";

// ─── Demo path helpers (Amplify Storage direct, public/) ──────────────────

function demoDesignPath(smartHomeId, fileName) {
  return `public/${S3_PREFIX_SMARTHOMES}/${smartHomeId}/design/${fileName}`;
}

// ─── Real-tenant signed-URL helpers (AppSync-mediated) ────────────────────

async function fetchReadUrl(smartHomeId, fileName) {
  const client = generateClient();
  const { requestDesignReadUrl } = await import("../graphql/mutations");
  const result = await client.graphql({
    query: requestDesignReadUrl,
    variables: { smartHomeId, fileName },
  });
  return result.data.requestDesignReadUrl.url;
}

async function fetchWriteUrl(smartHomeId, fileName, contentType) {
  const client = generateClient();
  const { requestDesignWriteUrl } = await import("../graphql/mutations");
  const result = await client.graphql({
    query: requestDesignWriteUrl,
    variables: { smartHomeId, fileName, contentType },
  });
  return result.data.requestDesignWriteUrl.url;
}

async function readJsonViaSignedUrl(smartHomeId, fileName) {
  const url = await fetchReadUrl(smartHomeId, fileName);
  const res = await fetch(url);
  if (!res.ok) {
    if (res.status === 404) return null;
    throw new Error(`S3 GET ${fileName} failed: ${res.status}`);
  }
  return res.json();
}

async function readTextViaSignedUrl(smartHomeId, fileName) {
  const url = await fetchReadUrl(smartHomeId, fileName);
  const res = await fetch(url);
  if (!res.ok) {
    if (res.status === 404) return null;
    throw new Error(`S3 GET ${fileName} failed: ${res.status}`);
  }
  return res.text();
}

async function writeViaSignedUrl(smartHomeId, fileName, body, contentType) {
  const url = await fetchWriteUrl(smartHomeId, fileName, contentType);
  const res = await fetch(url, {
    method: "PUT",
    headers: { "Content-Type": contentType },
    body,
  });
  if (!res.ok) {
    throw new Error(`S3 PUT ${fileName} failed: ${res.status}`);
  }
}

// ─── Public API ──────────────────────────────────────────────────────────

export async function fetchToolboxFromS3(version = "latest") {
  const prefix = `${S3_PREFIX_ONTOLOGY}/${version === "latest" ? "latest" : `v${version}`}`;
  try {
    const [blocksResult, toolboxResult] = await Promise.all([
      downloadData({ path: `public/${prefix}/blockly-blocks.json` }).result,
      downloadData({ path: `public/${prefix}/blockly-toolbox.json` }).result,
    ]);
    const blocksJson = await blocksResult.body.text();
    const toolboxJson = await toolboxResult.body.text();
    return {
      blocks: JSON.parse(blocksJson),
      toolbox: JSON.parse(toolboxJson),
    };
  } catch (err) {
    console.warn("[S3] Failed to fetch toolbox from S3, will use local fallback:", err.message);
    return null;
  }
}

export async function fetchDesignFromS3(smartHomeId) {
  try {
    if (isDemoSmartHome(smartHomeId)) {
      const result = await downloadData({
        path: demoDesignPath(smartHomeId, "workspace.json"),
      }).result;
      const json = await result.body.text();
      return JSON.parse(json);
    }
    return await readJsonViaSignedUrl(smartHomeId, "workspace.json");
  } catch (err) {
    console.warn("[S3] No saved design found for", smartHomeId, err.message);
    return null;
  }
}

export async function saveDesignToS3(smartHomeId, { workspaceJson, aboxTtl, aboxJson }) {
  if (isDemoSmartHome(smartHomeId)) {
    await Promise.all([
      uploadData({
        path: demoDesignPath(smartHomeId, "workspace.json"),
        data: JSON.stringify(workspaceJson, null, 2),
        options: { contentType: "application/json" },
      }).result,
      uploadData({
        path: demoDesignPath(smartHomeId, "abox.ttl"),
        data: aboxTtl,
        options: { contentType: "text/turtle" },
      }).result,
      uploadData({
        path: demoDesignPath(smartHomeId, "abox.json"),
        data: JSON.stringify(aboxJson, null, 2),
        options: { contentType: "application/json" },
      }).result,
    ]);
    return;
  }
  await Promise.all([
    writeViaSignedUrl(
      smartHomeId,
      "workspace.json",
      JSON.stringify(workspaceJson, null, 2),
      "application/json"
    ),
    writeViaSignedUrl(smartHomeId, "abox.ttl", aboxTtl, "text/turtle"),
    writeViaSignedUrl(
      smartHomeId,
      "abox.json",
      JSON.stringify(aboxJson, null, 2),
      "application/json"
    ),
  ]);
}

export async function fetchABoxFromS3(smartHomeId) {
  try {
    if (isDemoSmartHome(smartHomeId)) {
      const result = await downloadData({
        path: demoDesignPath(smartHomeId, "abox.json"),
      }).result;
      const json = await result.body.text();
      return JSON.parse(json);
    }
    return await readJsonViaSignedUrl(smartHomeId, "abox.json");
  } catch (err) {
    console.warn("[S3] No A-Box data found for", smartHomeId, err.message);
    return null;
  }
}
