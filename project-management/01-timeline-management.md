# Docetra Timeline Management

Document owner: Vechika  
Planning baseline: 18 August 2026  
Delivery window: 24 August–13 November 2026  
Jira project key: `DCT`  
Method: six two-week Scrum sprints

## 1. Purpose and planning assumptions

This timeline manages the delivery of Docetra as one Jira Software project. The existing frontend is the product baseline; the plan focuses on completing backend integration, data behavior, quality assurance, reporting, documentation, and release readiness.

Assumptions:

- The six named team members are the complete delivery team.
- Team members may hold more than one role, but every Jira item has exactly one assignee and one accountable reviewer.
- Each sprint reserves approximately 20% of capacity for review, support, defects, and unexpected work.
- New scope must replace work of similar size or move to a later release; it must not be silently added to an active sprint.
- Public holidays, academic commitments, and individual leave must be entered in the Jira calendar before sprint planning.

Jira's Scrum backlog supports ranking work and assigning it to sprints, epics, and versions. The project Timeline should contain epics and standard work items with Start date and Due date; subtasks remain on their parent task instead of being used as timeline milestones. See [Atlassian: Use your Scrum backlog](https://support.atlassian.com/jira-software-cloud/docs/use-your-scrum-backlog/) and [Atlassian: Timeline limits](https://support.atlassian.com/jira-software-cloud/docs/set-up-the-roadmap/).

## 2. Team and ownership

| Person | Primary role | Planning ownership |
| --- | --- | --- |
| Bong Limeng | Business Analyst | Requirements, acceptance criteria, workflow validation, stakeholder acceptance |
| Vechika | Project Manager, QA Tester | Schedule, scope, risks, sprint facilitation, QA coordination, release approval |
| Vitou | Frontend Developer, Support | Frontend completion, UI defects, accessibility, user support |
| Kimheang | Backend Developer, Frontend Developer, DevOps, Marketing | APIs, database, integration, deployment, cross-stack defects, release communication |
| Sothay | Data Scientist, BI Analyst | Data quality, metrics, dashboards, AI/search evaluation, business analysis |
| Oudom | Support, BI Analyst | UAT coordination, issue triage, operational reports, dashboard verification, user guidance |

Vechika owns the master schedule. Workstream owners update dates and dependencies before the daily check-in. Only Vechika changes sprint dates or the release date after discussing the impact with the team.

## 3. Jira epic timeline

| Epic ID | Jira epic name | Start | Due | Accountable | Main contributors | Depends on |
| --- | --- | --- | --- | --- | --- | --- |
| E01 | Product Requirements and Governance | 24 Aug | 18 Sep | Bong Limeng | Vechika, Oudom | — |
| E02 | Platform, Authentication and Permissions | 24 Aug | 18 Sep | Kimheang | Vitou, Vechika | E01 requirements |
| E03 | Organization and User Management | 7 Sep | 2 Oct | Kimheang | Vitou, Bong Limeng | E02 |
| E04 | Record Configuration and Workflow | 7 Sep | 16 Oct | Kimheang | Vitou, Bong Limeng | E01, E02 |
| E05 | Meetings and Collaboration | 21 Sep | 16 Oct | Vitou | Kimheang, Vechika | E02, E04 schema |
| E06 | Portal, Files and Storage | 5 Oct | 30 Oct | Kimheang | Vitou, Oudom | E02, E04 |
| E07 | BI, Search and Summary Dashboard | 5 Oct | 30 Oct | Sothay | Oudom, Kimheang | E03, E04, E05 |
| E08 | QA, Documentation and Release | 19 Oct | 13 Nov | Vechika | Entire team | E02–E07 |

## 4. Sprint calendar and exit milestones

| Sprint | Dates | Delivery objective | Required exit evidence |
| --- | --- | --- | --- |
| Sprint 1 — Control and Contracts | 24 Aug–4 Sep | Confirm scope, Jira structure, acceptance criteria, API contract, environments, and CI baseline | Approved backlog; API contract linked; CI typecheck/build passing; top risks logged |
| Sprint 2 — Identity and Master Data | 7–18 Sep | Integrate authentication, session expiry, permissions, departments, companies, officers, roles, and users | Permission tests pass; access-denied/session dialogs verified; master-data CRUD demo accepted |
| Sprint 3 — Configurable Records | 21 Sep–2 Oct | Complete record types, attributes, dynamic forms, record workflows, assignments, and logs | Create/edit/list/board flows use API; schema validation passes; audit events visible |
| Sprint 4 — Meetings and Collaboration | 5–16 Oct | Complete topic/meeting boards, APScheduler reminders/recurrence, Telegram Meeting Bot, multi-assignment, comments, notes, deletion, archive behavior, and permissions | Meeting schedules survive restart without duplicate delivery; Telegram reminders, meeting/document workflows, and permission tests pass |
| Sprint 5 — Portal and Intelligence | 19–30 Oct | Complete upload/storage/Drive behavior, operational logs, search, KPI dataset, and dashboard | File/security tests pass; dashboard metrics reconcile to source data; high defects closed |
| Sprint 6 — UAT and Release | 2–13 Nov | UAT, accessibility, security review, password-reset email, Development Telegram Bot, performance checks, final reports, deployment, training, handover | UAT sign-off; external delivery and monitoring tests pass; zero open Blocker/Critical defects; release notes and rollback plan approved |

Sprint Review occurs on the final Thursday of each sprint. Sprint Retrospective and next Sprint Planning occur on the final Friday. The production release decision is 12 November; planned release is 13 November.

## 5. Milestones and gates

| Gate | Target | Approvers | Pass condition |
| --- | --- | --- | --- |
| Scope baseline | 28 Aug | Bong Limeng, Vechika | Requirements are prioritized and each Must-have has acceptance criteria |
| Architecture/API freeze | 11 Sep | Kimheang, Vitou | API routes, auth strategy, errors, pagination, and upload contract are documented |
| Feature complete | 23 Oct | Vechika, workstream owners | All Must-have stories are Done or formally deferred |
| Code complete | 30 Oct | Kimheang, Vitou | Only approved defects/documentation changes remain |
| UAT complete | 10 Nov | Bong Limeng, Oudom, Vechika | Business scenarios pass and evidence is attached |
| Go-live approval | 12 Nov | Vechika, Kimheang | Release checklist, backup, monitoring, and rollback are ready |

## 6. Dependencies and critical path

Critical path:

`Requirements → API/auth → record schema/workflow → meeting/portal integration → BI reconciliation → UAT → release`

Dependency rules:

- Use Jira link type `blocks / is blocked by`; do not describe a dependency only in a comment.
- A blocked item keeps its original assignee, moves to `Blocked`, and records the blocking Jira key.
- A blocker older than one working day is raised by Vechika at the daily check-in.
- Changes to shared API types require Kimheang and Vitou as reviewers.
- Dashboard tasks cannot close until Sothay and Oudom reconcile the metric against a known test dataset.

## 7. Timeline maintenance routine

### Daily

- Assignees update status, remaining estimate, and blocker before the check-in.
- Vechika checks overdue items and blockers.
- Support issues are triaged by Oudom and Vitou; only production-impacting issues interrupt the sprint.

### Weekly

- Monday: confirm sprint capacity and dependency dates.
- Wednesday: review risk and milestone forecast.
- Friday: publish the weekly report defined in `02-documentation-reporting.md`.
- Any epic forecast that moves by more than three working days becomes an Amber schedule risk.

### Sprint boundary

- Do not carry unfinished work automatically. Re-estimate and re-prioritize it in the backlog.
- Close the sprint only after acceptance evidence is linked.
- Record planned versus completed story points and explain spillover.
- Update Release `Docetra v1.0` scope and forecast.

## 8. Change control

Every scope change is a Jira `Change` task containing reason, value, urgency, requested date, affected requirements, estimate, timeline impact, and decision. Bong Limeng evaluates business value, Kimheang/Vitou estimate technical impact, and Vechika approves schedule placement. A change affecting the release baseline must include one decision: swap scope, extend date, add capacity, or reject/defer.

## 9. Schedule health rules

| Status | Rule | Required response |
| --- | --- | --- |
| Green | Milestones on forecast; sprint completion at least 85%; no critical blocker older than one day | Continue and monitor |
| Amber | Milestone forecast slips 1–3 working days; sprint completion 70–84%; critical blocker open | Recovery plan within one working day |
| Red | Milestone forecast slips more than 3 days; sprint completion below 70%; release blocker unresolved | Scope/date decision by Vechika and workstream owners |
