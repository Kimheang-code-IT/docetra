# Prompt 22 — Auth verify / reset steps

OTP is **not** a post-login 2FA step. Docetra uses a **password-reset code** after forgot-password only.

### Routes

| Route | Purpose |
| --- | --- |
| `/auth/verify-code` | Enter the 6-digit email code |
| `/auth/reset-password` | Set new password + confirm |

### Rules

- Do **not** implement a generic `/otp` login challenge.
- Do **not** add OTP after successful login.
- Require a password-reset session (email from step 1; verified + code before reset).
- After password update, clear the session and send the user to `/auth/login`.

If an old standalone `/otp` route exists, delete it and remove it from public auth middleware and route inventories.
