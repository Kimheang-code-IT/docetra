# Prompt 21 — Forget Password

## Copy/paste prompt

Implement the Forget Password page at `/forget-password` in the existing Nuxt UI application. Follow `prompt/frontend/00-shared-foundation.md`.

### Implement now

The page uses the `auth` layout and has two steps. Step 1: a `UAuthForm` with a single email field; on submit it simulates a delay, marks the email as sent, and transitions to Step 2. Step 2: a success state showing a mail-check icon, the sent-to email address, an "Enter OTP Code" button that navigates to `/otp`, and a "Back to Login" link. All labels use i18n keys under `pages.forgetPassword`.

### Future UI contract

When a real API is connected, POST the email to `/api/v2/auth/forgot-password`. Handle 404 (email not found) gracefully — do not reveal whether the email exists (always show the success state for security). Add a resend cooldown timer in Step 2. If the backend returns a token in the reset link, carry it as a query param to `/otp` or `/reset-password` as the flow requires.

### Acceptance

`/forget-password` renders in the `auth` layout, submitting the email transitions to the success state, the "Enter OTP Code" button navigates to `/otp`, the "Back to Login" link returns to `/login`, and typecheck/build remain clean.
