import type { ReactNode } from "react";

/**
 * No-op auth provider.
 *
 * This export was missing from the source package this app was built from
 * (along with a few files it would have depended on: `./providers`,
 * `./preview`, `./use-current-user`) — those wire this app into a
 * platform-specific OAuth broker that isn't available outside that platform,
 * and nothing in this app's UI actually reads auth state (no route mounts
 * `/api/auth/*`, and no component imports `useCurrentUser`, `SignedIn`,
 * `UserButton`, etc.). Auth is also off by default in this prototype (see
 * README — "Auth is off. This is a demonstration control plane, not a
 * multi-tenant production service").
 *
 * This stub exists only so `src/routes/__root.tsx` has something to render.
 * It renders children unchanged. If you want real sign-in on this
 * deployment, you'll need to build out `./providers`, `./preview`, and
 * `./use-current-user` yourself and wire a `/api/auth/*` server route to the
 * `auth` object already defined in `./server.ts` — that file expects a real
 * OAuth broker (issuer URL, client id/secret) which this stub does not
 * assume or fabricate.
 */
export function AuthProvider({ children }: { children: ReactNode }) {
  return <>{children}</>;
}
