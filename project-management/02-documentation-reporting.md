# Docetra Documentation and Reporting Management

Document owner: Bong Limeng  
Reporting coordinator: Vechika  
Repository location: `project-management/` and existing product references under `prompt/`

## 1. Documentation policy

Jira is the system of record for work status, ownership, dates, estimates, acceptance evidence, defects, risks, and decisions. This repository is the system of record for versioned technical and project documents. Every relevant Markdown document is linked from its Jira epic or task; do not maintain a second disconnected status list in chat.

Documentation principles:

- One owner writes; one named reviewer approves.
- Use short sections, tables, decisions, and links to evidence.
- Update the source document instead of creating `final-v2-new` copies.
- Record decisions with date, owner, context, decision, and consequence.
- Never include passwords, tokens, private personal data, or production secrets.
- Mark assumptions explicitly and replace them when confirmed.

## 2. Document register

| Document | Owner | Reviewer | Update cadence | Jira location / completion rule |
| --- | --- | --- | --- | --- |
| Product brief and objectives | Bong Limeng | Vechika | On approved scope change | Linked to E01; approved objectives and exclusions |
| Business requirements | Bong Limeng | Oudom | Weekly until scope freeze | Every Must-have mapped to acceptance criteria |
| Architecture and API contracts | Kimheang | Vitou | When contract changes | Linked to E02/E04; examples and error cases included |
| Permissions/access matrix | Bong Limeng | Vechika, Kimheang | Every role change | Route, action, and API enforcement covered |
| Test plan and test cases | Vechika | Bong Limeng | Every sprint | Each accepted story has test evidence |
| Data and KPI dictionary | Sothay | Oudom | Every metric change | Formula, source, owner, refresh frequency documented |
| User guide and support FAQ | Oudom | Vitou | From Sprint 4; weekly | Covers primary user flows and known recovery actions |
| Deployment/runbook | Kimheang | Vechika | Every environment/release change | Deploy, verify, monitor, backup, rollback documented |
| Release notes | Vechika | All workstream owners | Each release candidate | User-visible changes, fixes, limitations, upgrade notes |
| Weekly project report | Vechika | Workstream owners | Every Friday | Published before end of day with current Jira data |
| Final project report | Bong Limeng | Entire team | Sprint 6 | Approved scope, implementation, tests, outcomes, lessons |

## 3. Jira evidence rules

Every Story, Task, or Bug must contain:

1. Clear summary using an action and outcome.
2. Business context or problem statement.
3. Acceptance criteria with testable results.
4. Assignee, reporter, priority, epic, sprint, component, estimate, and due date when applicable.
5. Links to designs, API contracts, source documentation, dependencies, and related issues.
6. Test evidence before `Done`: screenshots, test output, request/response sample, or report link.
7. A resolution comment stating what changed, what was tested, and any follow-up.

## 4. Report cadence

| Report | Audience | Owner | Time | Source |
| --- | --- | --- | --- | --- |
| Daily check-in | Delivery team | Vechika | Each working morning, 15 minutes | Active Sprint board and blockers filter |
| Defect/triage note | Developers, QA, Support | Oudom | Daily when defects exist | Open Bugs filter |
| Weekly status report | Team and stakeholders | Vechika | Friday | Dashboard, epic forecast, risks, decisions |
| Sprint review report | Stakeholders | Vechika | End of each sprint | Completed stories and demo evidence |
| KPI/data quality report | PM, BA, BI | Sothay | Weekly from Sprint 4 | Dashboard reconciliation filters |
| Release readiness report | Release team | Vechika | Daily in final week | Release checklist and open defects |
| Final project report | Sponsors/team | Bong Limeng | End of Sprint 6 | All approved artifacts and Jira metrics |

## 5. Weekly project status template

Copy this template into the weekly Jira reporting task or a linked Markdown report.

```md
# Docetra Weekly Status — YYYY-MM-DD

## Overall status
- RAG: Green / Amber / Red
- Current sprint:
- Release forecast: 13 November 2026 / revised date
- One-sentence summary:

## Completed this week
- DCT-000 — outcome and evidence

## Planned next week
- DCT-000 — expected outcome — owner

## Delivery metrics
- Sprint committed / completed points:
- Open Blocker/Critical/High bugs:
- Blocked items older than one day:
- Must-have completion:

## Risks and issues
| ID | Risk/issue | Impact | Owner | Mitigation | Due | Status |
| --- | --- | --- | --- | --- | --- | --- |

## Decisions required
| Decision | Options | Recommendation | Decision owner | Needed by |
| --- | --- | --- | --- | --- |

## Scope changes
- Added, removed, exchanged, or none.

## Demo/evidence links
- Link — description
```

## 6. Sprint review report template

```md
# Sprint N Review — YYYY-MM-DD

## Sprint goal

## Commitment result
- Committed points:
- Completed points:
- Spillover and reason:

## Accepted outcomes
| Jira key | Outcome | Acceptance owner | Evidence |
| --- | --- | --- | --- |

## Rejected or incomplete outcomes
| Jira key | Gap | Next decision |
| --- | --- | --- |

## Quality
- Bugs opened / closed:
- Escaped defects:
- Automated checks:
- UAT scenarios:

## Stakeholder feedback

## Decisions and backlog changes
```

## 7. Decision record template

```md
# Decision: Short title

- Date:
- Jira key:
- Owner:
- Reviewers:
- Status: Proposed / Accepted / Rejected / Superseded

## Context

## Options considered

## Decision

## Consequences

## Follow-up actions
```

## 8. Defect report standard

A Bug is actionable only when it includes environment, build/version, user/role, preconditions, numbered reproduction steps, expected result, actual result, severity, frequency, evidence, and affected data. Severity definitions:

| Severity | Meaning | Initial response |
| --- | --- | --- |
| Blocker | System or release cannot proceed; no workaround | Immediate triage |
| Critical | Security/data-loss/core workflow failure | Same working day |
| High | Major feature failure with difficult workaround | Within one working day |
| Medium | Partial failure with practical workaround | Prioritize in sprint/backlog |
| Low | Cosmetic, copy, or minor usability issue | Backlog |

## 9. Final project report outline

1. Executive summary
2. Problem, objectives, stakeholders, and success criteria
3. Scope delivered and scope deferred
4. Team roles and project method
5. Requirements and business workflows
6. Architecture, modules, data model, APIs, security, and permissions
7. Implementation by workstream
8. Test strategy, test results, defect analysis, accessibility, security, and performance
9. Dashboard results and business insights
10. Deployment, operations, backup, monitoring, and support
11. Timeline and effort performance
12. Risks, changes, decisions, and lessons learned
13. Limitations and recommended next phase
14. References and appendices

## 10. Review and approval workflow

Document status is `Draft → In Review → Changes Requested → Approved → Superseded`. The owner attaches or links the draft to Jira and assigns the review subtask. The reviewer comments in one location, not in separate chat threads. Approval requires reviewer name and date in the Jira resolution comment. Material changes after approval reopen review.

