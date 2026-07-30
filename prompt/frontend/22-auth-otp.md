# Prompt 22 — OTP Verification

## Copy/paste prompt

Implement `/otp` in the auth layout with a six-digit accessible `UPinInput`, expiry countdown, verify loading state, inline invalid/expired feedback, resend cooldown, and Back to Login.

The verify button remains disabled until six digits are present. Preserve pasted-code support and correct focus movement. Connect through an isolated adapter for `/api/v2/auth/verify-otp`; handle expiry, invalid code, attempt limit, and lost reset session safely.

This page does not use workspace tables, Kanban, business document forms, comments, or activity.

### Acceptance

Keyboard/paste behavior works, timers clean up on unmount, error states are clear, and checks pass.
