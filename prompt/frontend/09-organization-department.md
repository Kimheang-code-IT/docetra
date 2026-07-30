# Prompt 09 — Department

## Copy/paste prompt

Implement `/organizations/departments` using shared master-data components.

### Page design

Provide server table plus an optional hierarchy view, not Kanban. Filters: search, parent department, status, officer count, and organization scope. Table columns show code, name, parent, status, officer count, related-record count, and updated time. Hierarchy children load lazily.

Add navigates to `/organizations/departments/new`; rows navigate to `/organizations/departments/:id`. Use the Nuxt UI document page with code, localized name, parent, contact/metadata, status, and cycle-safe validation. Tabs include Details, Officers, Child Departments, Related Records, and Access; place Comments & Activity below the form. Comments may be enabled for internal collaboration; Activity is always immutable.

### Acceptance

Hierarchy is cycle-safe and lazy, codes remain stable, document permissions/history work, and checks pass.
