# Prompt 22 — OTP Verification

## Copy/paste prompt

Implement the OTP Verification page at `/otp` in the existing Nuxt UI application. Follow `prompt/frontend/00-shared-foundation.md`.

### Implement now

The page uses the `auth` layout and renders a `UPinInput` of 6 digits. The verify button is disabled until all 6 digits are filled. On submit it simulates a delay and redirects to `/`. A resend button re-triggers the code send with a loading state and shows a success toast on completion. A "Back to Login" link in the footer navigates to `/login`. All labels use i18n keys under `pages.otp`.

### Future UI contract

When a real API is connected, POST the 6-digit code to `/api/v2/auth/verify-otp` along with the session token from the forgot-password flow. Handle expired codes (re-prompt resend), invalid codes (show inline error), and maximum attempts exceeded (lock and redirect to login). Add a countdown timer showing how long until the current code expires, and disable resend until the timer expires.

### Acceptance

`/otp` renders in the `auth` layout, the verify button is disabled until 6 digits are entered, submitting redirects to `/`, resend shows a toast, the "Back to Login" link navigates to `/login`, and typecheck/build remain clean.
