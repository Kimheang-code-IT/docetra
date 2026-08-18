# Docetra Project Summary Dashboard

Dashboard owner: Sothay  
Dashboard verifier: Oudom  
Project manager: Vechika  
Jira dashboard name: `Docetra Delivery Summary`

## 1. Dashboard purpose

The dashboard gives the team and stakeholders one trustworthy view of delivery, schedule, scope, quality, workload, risks, and release readiness. Jira data is authoritative. Numbers shown in weekly reports must match the dashboard filters at the time the report is published.

Jira dashboards can be shared and configured with gadgets that use filters and project data. See [Atlassian: Create and edit dashboards](https://support.atlassian.com/jira-software-cloud/docs/create-and-edit-dashboards/).

## 2. Audience views

| Audience | Needs | Default view |
| --- | --- | --- |
| Delivery team | Current work, blockers, review/QA queues, workload | Operational section |
| Project manager | Sprint forecast, milestones, scope change, defects, risk | Delivery-control section |
| BA/stakeholders | Accepted outcomes, Must-have progress, decisions, release forecast | Executive section |
| BI/data team | KPI reconciliation, data-quality defects, reporting work | Data section |
| Support/release team | UAT, open defects, documentation, release checklist | Release section |

## 3. Dashboard layout

### Row 1 — Executive status

1. Text gadget: current sprint goal, overall RAG, release forecast, latest decision needed.
2. Filter Results: current milestone items due in the next 14 days.
3. Two-Dimensional Filter Statistics: Epic by Status Category.

### Row 2 — Sprint delivery

1. Sprint Health or sprint progress gadget.
2. Burndown Chart.
3. Created vs Resolved Chart for the current sprint.
4. Filter Results: blocked items.

### Row 3 — Quality and release

1. Pie Chart: open bugs by severity/priority.
2. Filter Results: Blocker, Critical, and High bugs.
3. Filter Results: UAT items not Done.
4. Filter Results: release checklist not Done.

### Row 4 — Team and flow

1. Two-Dimensional Filter Statistics: Assignee by Status.
2. Average Age Chart for unresolved work.
3. Resolution Time gadget for bugs.
4. Filter Results: unassigned ready items.

### Row 5 — Scope, risk, and data

1. Filter Results: open Change tasks.
2. Filter Results: open Risk/Decision tasks or labelled items.
3. Filter Results: BI/Data Quality component work.
4. Text gadget: latest KPI reconciliation result and reporting timestamp.

## 4. Saved filters

Create and share these filters with the project team.

### DCT — Active Sprint

```jql
project = DCT AND sprint in openSprints() ORDER BY Rank ASC
```

### DCT — Blocked

```jql
project = DCT AND status = Blocked ORDER BY priority DESC, created ASC
```

### DCT — Open Bugs

```jql
project = DCT AND issuetype = Bug AND statusCategory != Done ORDER BY priority DESC, created ASC
```

### DCT — Release Blockers

```jql
project = DCT AND fixVersion = "Docetra v1.0" AND statusCategory != Done AND (priority = Highest OR labels = release-blocker) ORDER BY priority DESC
```

### DCT — UAT Remaining

```jql
project = DCT AND labels = uat AND statusCategory != Done ORDER BY priority DESC, assignee ASC
```

### DCT — Due in 14 Days

```jql
project = DCT AND due >= startOfDay() AND due <= endOfDay("+14d") AND statusCategory != Done ORDER BY due ASC
```

### DCT — Overdue

```jql
project = DCT AND due < startOfDay() AND statusCategory != Done ORDER BY due ASC
```

### DCT — Changes and Decisions

```jql
project = DCT AND (issuetype = Change OR labels in (decision, scope-change)) AND statusCategory != Done ORDER BY priority DESC, created ASC
```

### DCT — Data and Dashboard

```jql
project = DCT AND component in ("BI/Dashboard", "Search/AI") AND statusCategory != Done ORDER BY priority DESC, Rank ASC
```

## 5. KPI definitions

| KPI | Calculation | Green | Amber | Red | Owner |
| --- | --- | --- | --- | --- | --- |
| Sprint completion | Completed committed points ÷ committed points × 100 | ≥85% | 70–84% | <70% | Vechika |
| Must-have completion | Done Must-have items ÷ total Must-have items × 100 | On/above planned curve | ≤5 points behind | >5 points behind | Bong Limeng |
| Schedule variance | Forecast milestone date − baseline date | ≤0 days | 1–3 days | >3 days | Vechika |
| Blocker age | Oldest active blocker in working days | 0 | 1 | >1 | Vechika |
| Defect closure ratio | Bugs resolved in period ÷ bugs created in period | ≥1.0 | 0.75–0.99 | <0.75 | Vechika |
| Critical open defects | Count of unresolved Blocker/Critical bugs | 0 | 1 with owned fix | >1 or unowned | Vechika |
| Reopen rate | Reopened items ÷ completed items × 100 | ≤5% | 6–10% | >10% | Vechika |
| UAT pass rate | Passed scenarios ÷ executed scenarios × 100 | ≥95% | 85–94% | <85% | Oudom |
| Requirements coverage | Must-have requirements with linked accepted story ÷ total Must-haves | 100% by UAT | 90–99% | <90% | Bong Limeng |
| Dashboard reconciliation | Dashboard values matching approved source results ÷ tested metrics | 100% | 95–99% | <95% | Sothay |
| Documentation readiness | Approved required release documents ÷ required documents | 100% at gate | One document late | More than one late | Oudom |

## 6. Overall RAG calculation

Overall status is not an average that can hide a serious problem.

- Red when any release-blocking security/data defect exists, release forecast slips more than three working days, UAT is below 85%, or a critical blocker is older than one day.
- Amber when no Red condition exists but any schedule, completion, quality, data, or documentation KPI is Amber.
- Green only when every release-critical KPI is Green and no unowned high risk exists.
- Vechika may override the calculated status only with a written reason and recovery/monitoring action.

## 7. Workload review

Use Assignee × Status statistics to detect overload, not to rank people. Review:

- More than two active implementation/QA items for one person.
- Items waiting in review or QA for more than two working days.
- Unassigned items in `Selected for Development`.
- Critical work owned by a person who is unavailable.
- Role collision, especially Vechika handling PM and QA or Kimheang handling backend, frontend, DevOps, and release work simultaneously.

When overloaded, first reduce work in progress, reassign review/support, or move lower-priority work. Do not use raw issue count as individual performance measurement.

## 8. Dashboard update responsibility

| Data | Update owner | Frequency | Verification |
| --- | --- | --- | --- |
| Jira status, remaining estimate, blockers | Each assignee | Daily | Vechika |
| Sprint scope and release forecast | Vechika | Daily/when changed | Bong Limeng |
| Acceptance and requirements coverage | Bong Limeng | Twice weekly | Vechika |
| Bugs, test execution, release quality | Vechika | Daily | Oudom |
| UAT and support readiness | Oudom | Daily during UAT | Bong Limeng |
| KPI/data reconciliation | Sothay | Weekly; daily before release | Oudom |
| Deployment and operational readiness | Kimheang | At each release gate | Vechika |

## 9. Weekly executive summary template

```md
# Docetra Executive Summary — YYYY-MM-DD

**Overall:** Green / Amber / Red  
**Current sprint:** Sprint N  
**Release forecast:** YYYY-MM-DD  
**Confidence:** High / Medium / Low

## Outcome this week
One short paragraph describing delivered business value.

## KPI snapshot
| KPI | Current | Previous | Target | RAG |
| --- | ---: | ---: | ---: | --- |
| Sprint completion | | | 85% | |
| Must-have completion | | | planned curve | |
| Open critical defects | | | 0 | |
| UAT pass rate | | | 95% | |
| Dashboard reconciliation | | | 100% | |

## Top three risks/issues
1. Risk — impact — owner — next action/date

## Decision required
Decision, recommendation, decision owner, deadline; or “None”.

## Next milestone
Milestone, date, entry/exit condition, confidence.
```

## 10. Dashboard quality checklist

- All gadgets use shared filters, not private copies.
- Dashboard viewers have permission to see every intended filter.
- Filter names, owners, and descriptions are clear.
- Status mappings place completed statuses in Jira's Done category.
- Sprint and Release fields are populated consistently.
- Due dates exist for milestone work, not every tiny subtask.
- Every KPI has one formula, one data source, one owner, and one refresh timestamp.
- Sothay and Oudom reconcile figures before the Friday report.
- Vechika archives obsolete filters and gadgets after release.
