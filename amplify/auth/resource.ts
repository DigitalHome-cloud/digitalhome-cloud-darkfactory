import { defineAuth, secret } from "@aws-amplify/backend";
import { postConfirmation } from "../functions/postConfirmation/resource";

/**
 * Cognito User Pool + Identity Pool, with Google federation and 5 groups
 * matching the platform's tier system.
 *
 * Group meanings:
 *   - dhc-admins:      Library + ontology admins, full SmartHome read access
 *   - dhc-modelers:    can edit ontology drafts in the Modeler
 *   - dhc-professional: paid tier, future feature gating
 *   - dhc-standard:    default paid tier, future feature gating
 *   - dhc-welcome:     auto-assigned on sign-up (postConfirmation Lambda)
 *
 * Federation: Google OAuth.
 *   Set the secrets via:
 *     npx amplify sandbox secret set GOOGLE_CLIENT_ID
 *     npx amplify sandbox secret set GOOGLE_CLIENT_SECRET
 *
 *   For pipeline-deploy, set them in AWS Secrets Manager or via the Amplify
 *   Hosting console (Settings → Secrets).
 *
 *   NOTE: the new Cognito Hosted UI domain will differ from the old Gen 1
 *   one. After cutover, update the OAuth client redirect URIs in the
 *   Google Cloud Console to point at the new domain — otherwise Google
 *   sign-in breaks.
 */
export const auth = defineAuth({
  loginWith: {
    email: true,
    externalProviders: {
      google: {
        clientId: secret("GOOGLE_CLIENT_ID"),
        clientSecret: secret("GOOGLE_CLIENT_SECRET"),
        scopes: ["email", "profile", "openid"],
        attributeMapping: {
          email: "email",
          fullname: "name",
        },
      },
      callbackUrls: [
        "http://localhost:8000/",
        "http://localhost:8001/",
        "http://localhost:8002/",
        "https://stage-portal.digitalhome.cloud/",
        "https://stage-designer.digitalhome.cloud/",
        "https://stage-modeler.digitalhome.cloud/",
        "https://portal.digitalhome.cloud/",
        "https://designer.digitalhome.cloud/",
        "https://modeler.digitalhome.cloud/",
      ],
      logoutUrls: [
        "http://localhost:8000/",
        "http://localhost:8001/",
        "http://localhost:8002/",
        "https://stage-portal.digitalhome.cloud/",
        "https://stage-designer.digitalhome.cloud/",
        "https://stage-modeler.digitalhome.cloud/",
        "https://portal.digitalhome.cloud/",
        "https://designer.digitalhome.cloud/",
        "https://modeler.digitalhome.cloud/",
      ],
    },
  },
  groups: [
    "dhc-admins",
    "dhc-modelers",
    "dhc-professional",
    "dhc-standard",
    "dhc-welcome",
  ],
  triggers: {
    postConfirmation,
  },
});
