# Prompt 21 — Forget Password

## Copy/paste prompt

Implement `/forget-password` in the shared auth design language.

Use two clear states: email request form and neutral success confirmation. Validate email, show loading, prevent duplicate submission, provide Back to Login, and offer Enter OTP after success. Do not reveal whether an account exists. Add an accessible resend cooldown when connected to `/api/v2/auth/forgot-password`.

Keep all copy localized. This page does not use workspace tables, Kanban, business document forms, comments, or activity.

### Acceptance

Both states are keyboard accessible, account existence is not disclosed, navigation works, and checks pass.
