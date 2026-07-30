# Prompt 13 — Officer

## Copy/paste prompt

Implement `/organizations/officers` as a secure people directory.

Use a server table with optional profile-card view, not Kanban. Filters: name/contact search, department, organization, role, account-link state, and status. Columns show permitted identity fields, organization, department, role, account state, status, and updated time.

Add navigates to `/organizations/officers/new`; rows/cards navigate to `/organizations/officers/:id`. The Nuxt UI document page clearly separates business-side officer data from the login user. Tabs include Details, Organization Membership, Related Records, Linked Account, Files/Profile, and Security Activity. Do not add casual comments by default. Sensitive fields and account linking require explicit permissions and audit events.

### Acceptance

Officers can exist without accounts, sensitive data is protected, activity is immutable, and checks pass.
