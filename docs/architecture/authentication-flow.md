# DigitalHome.Cloud – Authentication Mechanism

This document explains how authentication works in the DigitalHome.Cloud
portal with Amplify Gen1 backend + Gen2 frontend, and how the different
pieces (Cognito, Amplify, AuthContext, pages) fit together.

---

## 1. Building blocks

### 1.1 Amazon Cognito

- Manages users, groups, and tokens.
- Each user has:
  - `sub` (UUID) – internal stable ID
  - `email` – unique login/email, verified
  - `cognito:username` – usually same as `sub` in this setup
  - `cognito:groups` – e.g. `["dhc-users", "dhc-welcome"]`

Cognito issues two main tokens:

- **ID token**
  - Contains identity claims (email, username, groups).
- **Access token**
  - Used for authorization decisions (groups, scopes).

Both are JWTs that the client stores in browser storage after sign-in.

---

### 1.2 Amplify Auth (frontend)

The frontend uses the Amplify Auth library to talk to Cognito:

- `fetchAuthSession()` – fetches the current session (ID + access tokens).
- `getCurrentUser()` – returns the basic Cognito user info.
- `signOut()` – logs the user out and clears tokens.

The Amplify `<Authenticator>` component (in `/signin`) handles the full
Hosted-UI / sign-in UI flow and writes the tokens so that
`fetchAuthSession()` can see them afterwards.

---

### 1.3 AuthContext (React)

`AuthContext` is a thin wrapper around Amplify Auth that provides a
clean React API to the rest of the app.

It exposes:

- `authState` – `"loading" | "demo" | "authenticated"`
- `isLoading` – `true` while we don’t yet know the auth state
- `isAuthenticated` – `true` when there is a valid Cognito session
- `user` – Cognito user object + ID token payload
- `groups` – list of Cognito groups (`cognito:groups`)
- `hasGroup(name)` – convenience checker
- `reloadSession()` – force re-check against Cognito
- `signOut()` – wrapper around Amplify `signOut` + local reset

This context is implemented in `src/context/AuthContext.js` and is
provided to the whole app via Gatsby’s `wrapRootElement` API in
`gatsby-browser.js` and `gatsby-ssr.js`.

---

## 2. How the flow works

### 2.1 Initial load

1. Gatsby renders the app.
2. On the **client** (browser), `AuthProvider` runs `useEffect` once.
3. Inside `useEffect`, it calls `fetchAuthSession()` and `getCurrentUser()`.
4. There are two possible outcomes:

   **A) Session found (signed in):**
   - `fetchAuthSession()` returns a valid session with ID token.
   - `AuthProvider`:
     - sets `user` to the current user + ID token payload
     - extracts `groups` from the ID token (`cognito:groups`)
     - sets `authState = "authenticated"`

   **B) No session / error (not signed in):**
   - `fetchAuthSession()` throws `NotAuthorizedException` or similar.
   - `AuthProvider`:
     - clears `user` / `groups`
     - sets `authState = "demo"`

5. While the check is running, `authState` is `"loading"`.

### 2.2 DEMO vs AUTHENTICATED

The navigation uses `useAuth()` and shows different UI depending on
`authState`:

- `authState === "demo"`
  - Show a “DEMO” pill and a sign-in link.
  - The app behaves like a demo instance (no personal data).
- `authState === "authenticated"`
  - Show a greeting / account tile.
  - Sections such as design/operate can be enabled based on `groups`
    (`dhc-users`, `dhc-operators`, etc.).

### 2.3 Sign in flow

1. User clicks the sign-in tile → navigates to `/signin`.
2. `/signin` renders the Amplify `<Authenticator>` with your custom theme.
3. When sign-in completes:
   - Amplify stores the ID + access tokens in browser storage.
4. `AuthContext` will see this in two ways:
   - On a *fresh page load*, the `useEffect` in `AuthProvider` runs again,
     calls `fetchAuthSession()`, and now finds a valid session →
     `authState = "authenticated"`.
   - Or you can call `reloadSession()` manually (e.g. after sign-in) to
     re-check without reloading the page.

Once `authState` becomes `"authenticated"`, all components using
`useAuth()` immediately render in the signed-in state.

### 2.4 Debug page

`/debug-auth` uses:

- `useAuth()` to show high-level state (authState, groups, username).
- `fetchAuthSession()` directly to decode ID and access tokens.
- A test GraphQL query `listUserProfiles` with `authMode: "userPool"`.

This confirms that:

- The Amplify Auth session is valid.
- AppSync accepts the token and allows Cognito-authenticated calls.

---

## 3. Why sign-in can “seem to work” while the rest is in DEMO

A common failure mode is:

- `<Authenticator>` signs in successfully and shows “you’re signed in”.
- But the global `AuthContext` **never updates** and stays in `"demo"`.

Typical causes:

1. `AuthProvider` is **not wrapping** the entire app.
   - `gatsby-browser.js` / `gatsby-ssr.js` must export `wrapRootElement`
     that wraps the root with `<AuthProvider>`.

2. `AuthContext` never calls `fetchAuthSession()` on the client.
   - Missing `useEffect` or guarded by a bad condition.

3. Amplify is not configured on the client.
   - You must call `Amplify.configure(awsExports)` in `gatsby-browser.js`
     (and often also `gatsby-ssr.js`) with the *same* config your
     `<Authenticator>` uses.

When these are fixed, `/signin`, `/debug-auth`, and the main pages all
see the same session and switch between DEMO and AUTHENTICATED together.

---

## 4. Improved AuthContext implementation

The improved `AuthContext.js` used in this setup looks like this:

```js
import React, {
  createContext,
  useContext,
  useEffect,
  useState,
} from "react";
import {
  fetchAuthSession,
  getCurrentUser,
  signOut as amplifySignOut,
} from "aws-amplify/auth";

/**
 * AuthContext / AuthProvider
 *
 * Responsibilities:
 * - On client mount, try to load the current Cognito session.
 * - Expose:
 *   - authState: "loading" | "demo" | "authenticated"
 *   - isLoading: boolean
 *   - isAuthenticated: boolean
 *   - user: Cognito user object (or null)
 *   - groups: string[] from ID token ("cognito:groups")
 *   - hasGroup(name): boolean
 *   - reloadSession(): force-refresh from Cognito
 *   - signOut(): sign out via Amplify and reset state
 *
 * Notes:
 * - SSR-safe: never calls Amplify Auth on the server (no window).
 * - Uses fetchAuthSession() + getCurrentUser() so it stays in sync
 *   with the Amplify <Authenticator> component on /signin.
 */

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [authState, setAuthState] = useState("loading"); // "loading" | "demo" | "authenticated"
  const [user, setUser] = useState(null);
  const [groups, setGroups] = useState([]);

  const isBrowser = typeof window !== "undefined";

  const loadSession = async () => {
    if (!isBrowser) {
      // On SSR render, don't call Amplify. Client hydration will re-run this.
      setAuthState((prev) => (prev === "loading" ? "demo" : prev));
      return;
    }

    try {
      setAuthState("loading");

      // getCurrentUser() checks local tokens — doesn't need Identity Pool.
      // Call it first so an Identity Pool misconfiguration doesn't break auth.
      const currentUser = await getCurrentUser();

      // User is authenticated. Now try to get the session for group claims.
      let idPayload = {};
      try {
        const session = await fetchAuthSession();
        idPayload = session?.tokens?.idToken?.payload || {};
      } catch (sessionErr) {
        // Identity Pool errors (e.g. DNS resolution) must not block auth.
        console.warn(
          "[AuthContext] fetchAuthSession failed (Identity Pool?), proceeding without token payload:",
          sessionErr
        );
      }

      const tokenGroups = idPayload["cognito:groups"] || [];

      setUser({
        ...currentUser,
        idTokenPayload: idPayload,
      });
      setGroups(tokenGroups);
      setAuthState("authenticated");
    } catch (err) {
      console.warn("[AuthContext] No valid session, using DEMO mode:", err);
      setUser(null);
      setGroups([]);
      setAuthState("demo");
    }
  };

  useEffect(() => {
    // Run once on client mount
    if (!isBrowser) {
      // SSR: do nothing; initial state will stay "loading" until hydration.
      return;
    }
    loadSession();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleSignOut = async () => {
    try {
      await amplifySignOut();
    } catch (err) {
      console.error("[AuthContext] Error during sign-out:", err);
    } finally {
      // Regardless of error, reset local auth state
      setUser(null);
      setGroups([]);
      setAuthState("demo");
    }
  };

  const value = {
    authState,
    isLoading: authState === "loading",
    isAuthenticated: authState === "authenticated",
    user,
    groups,
    hasGroup: (g) => groups.includes(g),
    reloadSession: loadSession,
    signOut: handleSignOut,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return ctx;
};
```

Place this in:

```text
src/context/AuthContext.js
```

and ensure that both `gatsby-browser.js` and `gatsby-ssr.js` wrap the
root element with `AuthProvider`.

---

## 5. Summary

- Cognito + Amplify Auth manage the real authentication state.
- `<Authenticator>` on `/signin` drives the login UI and stores tokens.
- `AuthContext` turns tokens into a simple React API:
  - `authState`, `isAuthenticated`, `user`, `groups`, etc.
- Gatsby’s `wrapRootElement` makes `AuthContext` available everywhere.
- `/debug-auth` is your live “truth-checker” showing tokens + GraphQL
  connectivity.
- When wired correctly, signing in once updates the whole app:
  nav, tiles, profile page, and debug tools.

