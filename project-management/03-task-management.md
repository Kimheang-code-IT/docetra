# Docetra Jira Task Management

Process owner: Vechika  
Jira project: `DCT`  
Board type: Scrum  
Release: `Docetra v1.0`

## 1. Jira project setup

Use one Jira Software project for the six-person team. Configure:

- Work types: Epic, Story, Task, Bug, Spike, Change, and Subtask.
- Components: Product, Frontend, Backend/API, Database, Authentication, Permissions, Organization, Records, Meetings, Portal/Storage, Search/AI, BI/Dashboard, QA, DevOps, Documentation, and Support.
- Versions: `v0.1 Internal Integration`, `v0.5 Feature Complete`, `v0.9 UAT`, `v1.0 Production`.
- Two-week sprints matching `01-timeline-management.md`.
- Estimation: story points using 1, 2, 3, 5, 8, 13. Split anything larger than 8 points before sprint commitment.
- Labels only for cross-cutting retrieval: `must-have`, `security`, `accessibility`, `data-migration`, `tech-debt`, `uat`, `release-blocker`, `risk`, `decision`, and `scope-change`. Use Components instead of creating uncontrolled labels.

Recommended workflow:

`Backlog → Selected for Development → In Progress → In Review → Ready for QA → In QA → Ready for Acceptance → Done`

Any active status may move to `Blocked`; removing the blocker returns it to the prior active status. Reopened work returns to `In Progress` with the reason documented.

## 2. Work type rules

| Type | Use when | Required owner |
| --- | --- | --- |
| Epic | A measurable module or workstream spans multiple sprints | Workstream accountable person |
| Story | A user/stakeholder receives testable value | BA acceptance owner plus one assignee |
| Task | Technical, operational, reporting, or documentation work | One assignee |
| Bug | Observed behavior differs from expected behavior | Developer assignee; QA verifier |
| Spike | Time-boxed research with a decision/output | Technical or analysis owner |
| Change | Approved request changes scope, cost, date, or behavior | Vechika |
| Subtask | Work is necessary to finish one parent and has no independent value | Contributor |

## 3. Priority model

| Priority | Rule | Scheduling expectation |
| --- | --- | --- |
| Highest | Security, data loss, release blocker, or core system unavailable | Interrupt current work after PM triage |
| High | Must-have workflow cannot meet acceptance criteria | Current or next sprint |
| Medium | Important behavior with workaround | Prioritized backlog |
| Low | Improvement, polish, or nonessential report | After Must-haves |
| Lowest | Idea requiring future validation | Icebox/backlog |

Priority is not severity. Bugs have both a priority and the severity defined in the reporting guide.

## 4. Responsibility matrix

| Work area | Accountable | Primary implementer | Reviewer/tester |
| --- | --- | --- | --- |
| Requirements and business process | Bong Limeng | Bong Limeng | Vechika, Oudom |
| Planning, risks, and release control | Vechika | Vechika | Workstream owners |
| Frontend and UI behavior | Vitou | Vitou, Kimheang | Vechika |
| Backend, API, database | Kimheang | Kimheang | Vitou, Vechika |
| Authentication, permissions, DevOps | Kimheang | Kimheang | Vechika, Vitou |
| Data processing and metrics | Sothay | Sothay | Oudom |
| Dashboard and BI verification | Sothay | Sothay, Oudom | Bong Limeng |
| QA execution and release acceptance | Vechika | Vechika, Oudom | Bong Limeng |
| Support, triage, user guide | Oudom | Oudom, Vitou | Vechika |

## 5. Initial epic backlog

The IDs below are planning IDs for Jira creation, not existing Jira issue keys.

### E01 — Product Requirements and Governance

| ID | Type | Summary | Assignee | Reviewer | Points |
| --- | --- | --- | --- | --- | --- |
| E01-01 | Story | Confirm actors, business processes, and system boundaries | Bong Limeng | Vechika | 5 |
| E01-02 | Task | Map requirements to modules and acceptance scenarios | Bong Limeng | Oudom | 5 |
| E01-03 | Task | Configure Jira project, workflow, components, versions, and dashboard | Vechika | Oudom | 3 |
| E01-04 | Task | Establish risk, decision, change, and reporting registers | Vechika | Bong Limeng | 3 |

### E02 — Platform, Authentication and Permissions

| ID | Type | Summary | Assignee | Reviewer | Points |
| --- | --- | --- | --- | --- | --- |
| E02-01 | Story | Integrate login, logout, reset, and expired-session behavior | Kimheang | Vechika | 5 |
| E02-02 | Story | Enforce role permissions on routes, actions, API, and records | Kimheang | Vitou | 8 |
| E02-03 | Task | Add access-control integration and negative tests | Vechika | Kimheang | 5 |
| E02-04 | Task | Configure CI, environments, secrets, logging, and health checks | Kimheang | Vechika | 5 |
| E02-05 | Task | Review browser security headers, upload rules, and session design | Kimheang | Vechika | 5 |
| E02-06 | Story | Deliver Redis short/long cache tiers, invalidation, and observability | Kimheang | Sothay | 5 |
| E02-07 | Story | Deliver RabbitMQ workers, retries, dead letters, and job monitoring | Kimheang | Vechika | 8 |
| E02-08 | Story | Route version, code, documentation, deployment, and technical alerts to private IT Telegram groups | Kimheang | Vechika | 5 |

### E03 — Organization and User Management

| ID | Type | Summary | Assignee | Reviewer | Points |
| --- | --- | --- | --- | --- | --- |
| E03-01 | Story | Deliver department hierarchy management | Kimheang | Bong Limeng | 5 |
| E03-02 | Story | Deliver companies, purposes, and sectors | Kimheang | Bong Limeng | 5 |
| E03-03 | Story | Deliver officer profiles and searchable assignment options | Vitou | Vechika | 5 |
| E03-04 | Story | Deliver roles, users, permission matrix, and user profile | Kimheang | Vechika | 8 |
| E03-05 | Task | Validate organization and user data quality | Sothay | Oudom | 3 |
| E03-06 | Story | Implement user disable/admin restore and protected role lifecycle with immutable activity | Kimheang | Vechika | 5 |

### E04 — Record Configuration and Workflow

| ID | Type | Summary | Assignee | Reviewer | Points |
| --- | --- | --- | --- | --- | --- |
| E04-01 | Story | Deliver Record Attribute catalog and validation rules | Kimheang | Vitou | 8 |
| E04-02 | Story | Deliver Record Type schema, stages, transitions, and field assignment | Kimheang | Bong Limeng | 8 |
| E04-03 | Story | Integrate incoming, outgoing, document, and master-list workflows | Vitou | Kimheang | 8 |
| E04-04 | Story | Support multi-person and multi-organization mention assignment | Vitou | Vechika | 5 |
| E04-05 | Story | Deliver comments, attachments, activity, logs, export, and archive | Kimheang | Vechika | 8 |
| E04-06 | Task | Test dynamic schemas, permissions, transitions, and data retention | Vechika | Bong Limeng | 8 |
| E04-07 | Story | Implement owner archive/restore, admin tombstone recovery, retention-safe purge, and lifecycle comments/activity | Kimheang | Vechika | 8 |

### E05 — Meetings and Collaboration

| ID | Type | Summary | Assignee | Reviewer | Points |
| --- | --- | --- | --- | --- | --- |
| E05-01 | Story | Integrate meeting topic board, search, counts, and pagination | Vitou | Kimheang | 5 |
| E05-02 | Story | Integrate meeting creation, assignment, ordering, and unassignment | Kimheang | Vitou | 8 |
| E05-03 | Story | Deliver participant mentions, notes, files, and meeting links | Vitou | Vechika | 5 |
| E05-04 | Story | Deliver permission-aware topic and meeting deletion | Kimheang | Vechika | 3 |
| E05-05 | Task | Execute meeting workflow and concurrent-update tests | Vechika | Oudom | 5 |
| E05-06 | Story | Deliver APScheduler meeting reminders, recurrence, reconciliation, and recovery | Kimheang | Vechika | 8 |
| E05-07 | Story | Deliver Telegram Meeting Bot reminders and verified user channel mapping | Kimheang | Vitou | 5 |
| E05-08 | Story | Deliver allowlisted meeting Telegram groups and UI-ready user notification preferences | Kimheang | Vitou | 5 |

### E06 — Portal, Files and Storage

| ID | Type | Summary | Assignee | Reviewer | Points |
| --- | --- | --- | --- | --- | --- |
| E06-01 | Story | Integrate secure file upload, listing, deletion, and metadata | Kimheang | Vitou | 8 |
| E06-02 | Story | Complete Google Drive synchronization and recovery states | Kimheang | Vechika | 8 |
| E06-03 | Story | Deliver storage settings, connection tests, and operational logs | Kimheang | Oudom | 5 |
| E06-04 | Task | Test file restrictions, failures, retry, and permissions | Vechika | Kimheang | 5 |
| E06-05 | Story | Deliver optional Google OAuth account linking, capability controls, and revocation | Kimheang | Vechika | 8 |
| E06-06 | Story | Project Docetra meetings to Google Calendar with conflict and lifecycle handling | Kimheang | Vitou | 8 |
| E06-07 | Task | Complete Google consent, scope, privacy, quota, security, and revocation acceptance tests | Vechika | Bong Limeng | 5 |

### E07 — BI, Search and Summary Dashboard

| ID | Type | Summary | Assignee | Reviewer | Points |
| --- | --- | --- | --- | --- | --- |
| E07-01 | Task | Define KPI dictionary, sources, dimensions, and refresh rules | Sothay | Oudom | 5 |
| E07-02 | Story | Deliver operational summary API and reconciled dataset | Kimheang | Sothay | 8 |
| E07-03 | Story | Deliver summary dashboard filters, cards, charts, and drill-down | Sothay | Bong Limeng | 8 |
| E07-04 | Story | Validate keyword/semantic search and permission filtering | Sothay | Vitou | 5 |
| E07-05 | Task | Create data-quality and dashboard reconciliation tests | Oudom | Sothay | 5 |

### E08 — QA, Documentation and Release

| ID | Type | Summary | Assignee | Reviewer | Points |
| --- | --- | --- | --- | --- | --- |
| E08-01 | Task | Maintain regression suite and acceptance evidence | Vechika | Bong Limeng | 8 |
| E08-02 | Task | Run accessibility, responsive, security, and performance checks | Vechika | Vitou, Kimheang | 8 |
| E08-03 | Task | Coordinate UAT, triage feedback, and secure sign-off | Oudom | Vechika | 5 |
| E08-04 | Task | Complete user guide, support FAQ, and training | Oudom | Vitou | 5 |
| E08-05 | Task | Complete deployment, monitoring, backup, and rollback runbook | Kimheang | Vechika | 5 |
| E08-06 | Task | Publish final report and release notes | Bong Limeng | Entire team | 8 |
| E08-07 | Story | Deliver Development Telegram Bot for version, code, docs, CI/CD, and monitoring alerts | Kimheang | Vechika | 5 |
| E08-08 | Story | Integrate secure third-party forgot-password email delivery | Kimheang | Vechika | 5 |

## 6. Definition of Ready

An item may enter a sprint only when:

- The user/business outcome is understandable.
- Acceptance criteria are testable.
- Dependencies, designs, data/API needs, and permissions are identified.
- The team has estimated it at 8 points or less.
- One assignee and one acceptance owner are named.
- No unresolved decision prevents implementation.

## 7. Definition of Done

An item is Done only when:

- Acceptance criteria pass.
- Relevant typecheck, build, automated tests, and manual tests pass.
- Permission-denied, empty, loading, error, responsive, and localization states are checked where relevant.
- Code review is complete and no unresolved review comment remains.
- API/data/documentation changes are updated.
- QA evidence is attached or linked.
- No known Blocker/Critical defect remains.
- The acceptance owner approves the outcome.

## 8. Working agreement

- Work in progress limit: one primary implementation item per developer and one QA verification item per tester.
- Pull requests and commits include the Jira key.
- Comments record decisions or evidence, not routine “still working” messages.
- Do not close a parent while any required subtask is incomplete.
- Bugs discovered in the current story are linked to that story.
- Production support issues are triaged by Oudom; Vitou handles UI/user issues and Kimheang handles service/data/infrastructure issues.

## 9. Ceremonies

| Ceremony | Frequency | Duration | Facilitator | Required output |
| --- | --- | --- | --- | --- |
| Daily check-in | Daily | 15 min | Vechika | Updated blockers and daily focus |
| Backlog refinement | Weekly | 45 min | Bong Limeng | Ready, ranked work for next sprint |
| Sprint planning | Every 2 weeks | 90 min | Vechika | Sprint goal and committed backlog |
| Technical sync | Twice weekly | 30 min | Kimheang | API/dependency decisions |
| Defect triage | As needed, at least weekly | 30 min | Vechika/Oudom | Severity, owner, target sprint |
| Sprint review | Every 2 weeks | 60 min | Vechika | Accepted outcomes and feedback |
| Retrospective | Every 2 weeks | 45 min | Vechika | Maximum three owned improvements |

## 10. Useful Jira filters

Replace dates or project key if the Jira setup differs.

```jql
-- Active sprint work
project = DCT AND sprint in openSprints() ORDER BY Rank ASC

-- My open work
project = DCT AND assignee = currentUser() AND statusCategory != Done ORDER BY priority DESC, updated ASC

-- Blocked work
project = DCT AND status = Blocked ORDER BY priority DESC, created ASC

-- Open release defects
project = DCT AND issuetype = Bug AND fixVersion = "Docetra v1.0" AND statusCategory != Done ORDER BY priority DESC, created ASC

-- Overdue work
project = DCT AND due < startOfDay() AND statusCategory != Done ORDER BY due ASC

-- Unassigned ready work
project = DCT AND status = "Selected for Development" AND assignee is EMPTY ORDER BY priority DESC, Rank ASC

-- Recently completed
project = DCT AND statusCategory = Done AND resolved >= startOfWeek() ORDER BY resolved DESC
```

Jira's backlog is the place to rank items and plan sprints; Atlassian recommends fixed two-week sprints for teams new to sprint delivery. See [Atlassian: What is a sprint?](https://support.atlassian.com/jira-software-cloud/docs/what-is-a-sprint/).
