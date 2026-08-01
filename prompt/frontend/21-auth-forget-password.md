# Prompt 21 — Forget Password

## Copy/paste prompt

Implement `/forget-password` in the shared auth design language.

### Flow

1. **Request:** email form → send reset code (not an OTP login step).
2. **Verify on same page:** after success, show “Check your email” with a **6-character** `UPinInput`, Verify Code, Resend, and Back to Login.
3. On valid code, continue (mock: toast + redirect to `/login`). Do **not** use a separate `/otp` page and do **not** add OTP after login.

Validate email, show loading, prevent duplicate submission. Do not reveal whether an account exists. Connect through adapters for forgot-password, verify, and resend. Keep copy localized. Language switcher lives in the auth layout (top-right).

### Acceptance

Both states are keyboard accessible; 6-digit code input works with paste; account existence is not disclosed; no dedicated OTP route; checks pass.
