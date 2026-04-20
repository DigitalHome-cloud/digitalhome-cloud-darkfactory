import * as React from "react";

const TIER_LABELS = {
  guest: "Guest",
  welcome: "Welcome",
  standard: "Standard",
  professional: "Professional",
};

export function UpgradePrompt({ required, current, compact = false }) {
  const requiredLabel = TIER_LABELS[required] || required;
  const currentLabel = TIER_LABELS[current] || current;

  if (compact) {
    return (
      <span className="dhc-upgrade-hint">
        Requires <strong>{requiredLabel}</strong>
      </span>
    );
  }

  return (
    <div className="dhc-upgrade-prompt">
      <p className="dhc-upgrade-prompt-text">
        {current === "guest" ? (
          <>Sign up to access this feature.</>
        ) : (
          <>
            This feature requires the <strong>{requiredLabel}</strong> plan.
            You are on <strong>{currentLabel}</strong>.
          </>
        )}
      </p>
      <a href="/upgrade/" className="dhc-button-primary dhc-upgrade-prompt-btn">
        {current === "guest" ? "Sign Up" : "Upgrade"}
      </a>
    </div>
  );
}
