# Prompt 20 — Login

## Copy/paste prompt

Implement the Login page at `/login` in the existing Nuxt UI application. Follow `prompt/frontend/00-shared-foundation.md`.

### Implement now

The page uses the `auth` layout and renders a `UAuthForm` with email, password, and remember-me fields. On successful mock authentication it writes the session token, shows a success toast, and redirects to `/`. On failure it shows an error toast. A "Forgot password?" link in the footer navigates to `/forget-password`. All labels use i18n keys under `pages.auth`.

### Future UI contract

When a real API is connected, replace `authenticateMock` with a POST to `/api/v2/auth/login`. Handle 401 (wrong credentials), 403 (account disabled), and network errors with distinct toasts. Add rate-limiting feedback (too many attempts). Support SSO/OAuth entry points if required by the specification. Keep remember-me as a secure HttpOnly cookie strategy coordinated with the backend.

### Acceptance

`/login` renders in the `auth` layout, mock login succeeds and redirects to `/`, wrong credentials show an error toast, the "Forgot password?" link navigates correctly, and typecheck/build remain clean.
