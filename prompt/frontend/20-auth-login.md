# Prompt 20 — Login

## Copy/paste prompt

Implement `/login` as the focused Docetra authentication entry using the `auth` layout and Nuxt UI.

Design a responsive branded card with email, password visibility toggle, remember-me, Forgot Password link, submit loading state, validation, and accessible error summary. Keep keyboard focus correct and prevent duplicate submission.

On success, store the session and redirect to `/` (or the first permitted route). **Do not add an OTP / 2FA step after login.** Keep the mock adapter isolated.

For the real API, use `/api/v2/auth/login`, secure HttpOnly session strategy, and distinct handling for invalid credentials, disabled account, rate limiting, and network failure without leaking sensitive details. Authentication pages do not use workspace tables, Kanban, document forms, comments, or activity.

### Acceptance

Login goes straight to the app with no OTP page; the page is mobile-friendly; validation and focus are accessible; checks pass.
