# Prompt 21 — Forget Password (3-step reset)

## Copy/paste prompt

Implement the forgot-password flow under `app/pages/auth/` in the shared auth design language.

### Flow (separate pages)

1. **`/auth/forget-password`** — email form → send reset code → start a client password-reset session → navigate to verify-code.
2. **`/auth/verify-code`** — 6-digit `UPinInput`, Verify, Resend, Change email, Back to Login. Guard: no session email → redirect to forget-password. On valid code, mark session verified and navigate to reset-password.
3. **`/auth/reset-password`** — new password + confirm password. Guard: requires verified session + code; otherwise redirect. On success, clear session and navigate to `/auth/login` so the user signs in again with email + new password.

Keep legacy `/forget-password` as a redirect to `/auth/forget-password`.

Do **not** fold verify + reset into one page. Do **not** add OTP after login. Mock verify code: `123456`. Do not reveal whether an account exists. Connect through adapters (`requestPasswordReset`, `verifyPasswordResetCode`, `resendPasswordResetCode`, `resetPasswordWithCode`). Keep copy localized (en/km). Language switcher lives in the auth layout (top-right).

### Acceptance

Each step is keyboard accessible; 6-digit paste works; step guards prevent skipping; passwords must match and meet min length; success returns to login; checks pass.
