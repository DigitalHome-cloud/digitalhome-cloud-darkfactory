import capabilities from "./capabilities.json";

const TIER_ORDER = capabilities.tiers;
const GROUP_TO_TIER = Object.fromEntries(
  Object.entries(capabilities.tierGroups).map(([tier, group]) => [group, tier])
);

export function resolveTier(cognitoGroups = []) {
  let highest = 0;
  for (const g of cognitoGroups) {
    const tier = GROUP_TO_TIER[g];
    if (tier) {
      const idx = TIER_ORDER.indexOf(tier);
      if (idx > highest) highest = idx;
    }
  }
  return TIER_ORDER[highest];
}

export function tierIndex(tier) {
  const idx = TIER_ORDER.indexOf(tier);
  return idx >= 0 ? idx : 0;
}

export function canAccess(tier, capabilityId, context) {
  const cap = capabilities.capabilities[capabilityId];
  if (!cap) return { allowed: false, requiredTier: null };

  const requiredIdx = TIER_ORDER.indexOf(cap.minTier);
  const currentIdx = tierIndex(tier);

  if (currentIdx < requiredIdx) {
    return { allowed: false, requiredTier: cap.minTier };
  }

  const constraint = cap.constraints?.[tier] ?? null;
  return { allowed: true, constraint };
}

export function getConstraint(tier, capabilityId) {
  const cap = capabilities.capabilities[capabilityId];
  return cap?.constraints?.[tier] ?? null;
}

export function getQuota(tier, quotaKey) {
  return capabilities.quotas?.[tier]?.[quotaKey] ?? null;
}

export { capabilities };
