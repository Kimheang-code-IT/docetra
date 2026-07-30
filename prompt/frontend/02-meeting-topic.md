# Prompt 02 — Meeting Topic

## Copy/paste prompt

Implement `/meetings/topics` using the shared table, Kanban, ERP-style document page, comments/activity, attachments, and record configuration components.

### Page design

- Default Kanban view grouped by configured topic stage, with a table-view toggle.
- Toolbar filters: search, stage, status, owner, organization, meeting date, and child-meeting count.
- Topic cards show title, status, owner, date, child count, and the first ordered child meetings.
- Support dragging an unlinked meeting into a topic. After backend confirmation, remove it from the standalone meeting collection and show it only under the topic.
- Provide accessible “Add meeting to topic” and “Move stage” actions as non-drag alternatives.

### Create and document pages

Add Topic navigates to `/meetings/topics/new`; rows and cards navigate to `/meetings/topics/:id`. Use the shared Nuxt UI document shell with header actions, Summary/Meetings/Relationships/Files tabs, a right metadata rail, and Comments & Activity below the form. Activity includes creation, edits, stage changes, child-link changes, files, and email events with an optional “New Email” action.

### Large data

Paginate the table server-side and incrementally load each Kanban column and child list. Make drag/link operations optimistic only with rollback and conflict handling.

### Acceptance

Table and Kanban share one query state, topic linking follows the no-duplicate rule, document routes work, comments/activity are separate datasets, and checks pass.
