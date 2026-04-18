const CONTEXT_URL = "https://digitalhome.cloud/context/v1.2.0/context.jsonld";

export function generateRealEstateABox({
  smartHomeId,
  name,
  preferredLanguage = "en",
  country,
  postalCode,
  streetName,
  streetNumber,
  locality,
  adminRegion,
  formattedAddress,
  latitude,
  longitude,
  placeId,
  placeIdProvider = "manual",
  geocodeVerified = false,
  isDemo = false,
  createdBy,
}) {
  const now = new Date().toISOString();
  const realEstateUri = `urn:dh:${smartHomeId}`;

  const realEstate = {
    "@context": CONTEXT_URL,
    "@id": realEstateUri,
    "@type": "RealEstate",
    smartHomeId,
    name: name || `${streetName || ""} ${streetNumber || ""}`.trim() || smartHomeId,
    preferredLanguage,
    country,
    postalCode,
    streetName,
    streetNumber,
    locality,
    adminRegion,
    formattedAddress,
    latitude,
    longitude,
    placeId: placeId || null,
    placeIdProvider,
    geocodeVerified,
    isDemo,
    creationStatus: "draft",
    createdAt: now,
    updatedAt: now,
    createdBy: createdBy ? { "@id": createdBy } : null,
  };

  const roleAssignment = {
    "@context": CONTEXT_URL,
    "@id": `${realEstateUri}:roleassign:owner:01`,
    "@type": "dhc:RoleAssignment",
    assignedAgent: createdBy ? { "@id": createdBy } : null,
    assignedRole: { "@id": "dhc:Role_Owner" },
    assignmentContext: { "@id": realEstateUri },
    assignmentStatus: "active",
    validFrom: now,
  };

  const manifest = {
    smartHomeId,
    name: realEstate.name,
    locality,
    country,
    latitude,
    longitude,
    isDemo,
    creationStatus: "draft",
    tier: null,
    storage: null,
    createdAt: now,
    updatedAt: now,
    ownerSub: createdBy
      ? createdBy.replace("urn:agent:cognito:sub:", "")
      : null,
    aboxVersion: "1.2.0",
  };

  return { realEstate, roleAssignment, manifest };
}
