import { useMemo } from "react";
import { resolveTier, canAccess, getConstraint, getQuota } from "./tierResolver";

export function useTier(authContext) {
  const { groups = [], authState } = authContext;

  const tier = useMemo(() => {
    if (authState === "loading") return "guest";
    return resolveTier(groups);
  }, [groups, authState]);

  const can = useMemo(
    () => (capabilityId, context) => canAccess(tier, capabilityId, context),
    [tier]
  );

  const constraint = useMemo(
    () => (capabilityId) => getConstraint(tier, capabilityId),
    [tier]
  );

  const quota = useMemo(
    () => (quotaKey) => getQuota(tier, quotaKey),
    [tier]
  );

  return { tier, can, constraint, quota };
}
