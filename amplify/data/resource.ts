import { type ClientSchema, a, defineData } from "@aws-amplify/backend";
import { dhcDesignStorageProxy } from "../functions/dhcDesignStorageProxy/resource";

/**
 * AppSync data layer. Models + custom mutations.
 *
 * Authorization rules ported from the Gen 1 schema (post-C-1 + C-5 closure):
 *   - UserProfile:    owner-only + admin read   (audit C-5)
 *   - LibraryItem:    admin write, any signed-in user read
 *   - SmartHome:      multi-owner + admin       (audit C-1)
 *   - SmartHomeDesign: multi-owner + admin      (audit C-1)
 *   - requestDesignReadUrl / requestDesignWriteUrl: signed-URL mutations
 *     backed by dhcDesignStorageProxy Lambda    (audit C-2 v2)
 */

const schema = a.schema({
  // ─── enums ────────────────────────────────────────────────────────
  Locale: a.enum(["EN", "FR", "DE"]),

  // ─── models ───────────────────────────────────────────────────────
  UserProfile: a
    .model({
      displayName: a.string(),
      email: a.email(),
      locale: a.ref("Locale"),
      marketingOptIn: a.boolean(),
    })
    .authorization((allow) => [
      allow.owner(),
      allow.group("dhc-admins").to(["read"]),
    ]),

  LibraryItem: a
    .model({
      title: a.string().required(),
      compatibleClasses: a.string().array().required(),
      region: a.string(),
      standards: a.string().array(),
      version: a.string().required(),
      description: a.string(),
      hasActorCapability: a.boolean(),
      hasSensorCapability: a.boolean(),
      hasControllerCapability: a.boolean(),
    })
    .authorization((allow) => [
      allow.group("dhc-admins").to(["create", "update", "delete"]),
      allow.authenticated().to(["read"]),
    ]),

  SmartHome: a
    .model({
      owners: a.string().array(),
      country: a.string().required(),
      zip: a.string().required(),
      streetCode: a.string().required(),
      houseNumber: a.string().required(),
      suffix: a.string().required(),
      address: a.string(),
      description: a.string(),
      ownerName: a.string(),
    })
    .authorization((allow) => [
      allow.ownersDefinedIn("owners"),
      allow.group("dhc-admins"),
    ]),

  SmartHomeDesign: a
    .model({
      smartHomeId: a.string().required(),
      owners: a.string().array(),
      version: a.integer().required(),
      lastModified: a.datetime().required(),
      lockedBy: a.string(),
      lockedAt: a.datetime(),
      ontologyVersion: a.string(),
    })
    .authorization((allow) => [
      allow.ownersDefinedIn("owners"),
      allow.group("dhc-admins"),
    ])
    // Index on smartHomeId so the Lambda's owner-check Query is O(items per
    // SmartHome) instead of a full Scan (scales as the table grows).
    .secondaryIndexes((index) => [index("smartHomeId")]),

  // ─── custom return type for the signed-URL mutations ─────────────
  DesignStorageUrl: a.customType({
    url: a.string().required(),
    expiresAt: a.datetime().required(),
    contentType: a.string(),
  }),

  // ─── signed-URL mutations (backed by dhcDesignStorageProxy) ──────
  requestDesignReadUrl: a
    .mutation()
    .arguments({
      smartHomeId: a.id().required(),
      fileName: a.string().required(),
    })
    .returns(a.ref("DesignStorageUrl"))
    .handler(a.handler.function(dhcDesignStorageProxy))
    .authorization((allow) => [allow.authenticated()]),

  requestDesignWriteUrl: a
    .mutation()
    .arguments({
      smartHomeId: a.id().required(),
      fileName: a.string().required(),
      contentType: a.string(),
    })
    .returns(a.ref("DesignStorageUrl"))
    .handler(a.handler.function(dhcDesignStorageProxy))
    .authorization((allow) => [allow.authenticated()]),
});

export type Schema = ClientSchema<typeof schema>;

export const data = defineData({
  schema,
  authorizationModes: {
    defaultAuthorizationMode: "userPool",
  },
});
