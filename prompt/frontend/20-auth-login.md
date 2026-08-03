# Prompt 20 — Login

## Copy/paste prompt

Implement `/auth/login` as the focused Docetra authentication entry using the `auth` layout and Nuxt UI. Keep legacy `/login` as a redirect to `/auth/login`.

Design a responsive branded form with email, password, remember-me, Forgot Password link (`/auth/forget-password`), submit loading state, validation, and accessible errors. Keep keyboard focus correct and prevent duplicate submission.

On success, store the session and redirect to `/` (or the first permitted route). **Do not add an OTP / 2FA step after login.** Keep the mock adapter isolated.

For the real API, use `/api/v2/auth/login`, secure HttpOnly session strategy, and distinct handling for invalid credentials, disabled account, rate limiting, and network failure without leaking sensitive details. Authentication pages do not use workspace tables, Kanban, document forms, comments, or activity.

### Acceptance

Login goes straight to the app with no OTP page; the page is mobile-friendly; validation and focus are accessible; checks pass.
