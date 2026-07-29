# Prompt 13 — Officer

## Copy/paste prompt

Implement the Officer page at `/organizations/officers`. Follow the shared foundation, organization module, and people/access module.

### Implement now

Create only the localized Officer title, Organization breadcrumb, permission metadata, and standard placeholder. Do not build a people directory or user-account form.

### Future UI contract

The full page will manage business-side officer entities, including department/organization membership, status, contact/profile fields allowed by policy, and optional linked user account. Use server-side pagination/search/filtering. Clearly distinguish “officer” from “login user”; an officer may exist without an account. Sensitive fields and actions must be access-controlled, and account linking changes must be auditable.

### Acceptance

The route is linked under Organization and the scaffold contains no data or requests.

