# Prompt 22 — OTP Verification (removed)

OTP verification is **not** part of Docetra auth.

- Do **not** implement `/otp`.
- Do **not** add an OTP step after login.
- Forget-password success returns to Login (or an email-link reset flow), not OTP.

If an old `/otp` route exists, delete the page and remove it from public auth middleware and route inventories.
