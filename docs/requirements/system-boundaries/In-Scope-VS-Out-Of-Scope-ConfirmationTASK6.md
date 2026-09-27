# In-Scope vs. Out-of-Scope Confirmation

Re-confirm the Section 9 scope list from the original proposal still holds, and note anything the team has since decided differently.

---

## Original Out-of-Scope List (Proposal, Section 9)

The following items were defined as explicitly **out of scope for the initial version**:

1. Physical waste collection
2. Autonomous cleaning robots
3. Nationwide municipal deployment
4. Full integration with every municipal system
5. Guaranteed real-time location tracking of all workers
6. Automated legal enforcement against littering
7. Large-scale fleet management

---

## Confirmation Status

**All seven items still hold as out of scope.** Nothing decided by the team since the original proposal changes or contradicts this list. This has been cross-checked against every requirement defined so far — AI detection/classification, priority scoring, cleaning-team schema, task assignment and notification flow, and notification timeliness — none of which touch physical collection, robotics, municipal-wide deployment, full municipal system integration, live worker GPS tracking, legal enforcement, or fleet-scale logistics.

| # | Item | Status | Note |
|---|---|---|---|
| 1 | Physical waste collection | ✅ Still out of scope | The platform remains a reporting/decision-support tool; it does not perform or arrange physical collection itself. |
| 2 | Autonomous cleaning robots | ✅ Still out of scope | No robotics component has been introduced in any AI or workflow requirement defined so far. |
| 3 | Nationwide municipal deployment | ✅ Still out of scope | Current scope remains a pilot/local test area (e.g., a defined district or campus), consistent with the original proposal's feasibility section. |
| 4 | Full integration with every municipal system | ✅ Still out of scope | The MVP is designed to operate as a standalone platform with its own dashboard, per the original proposal. |
| 5 | Guaranteed real-time location tracking of all workers | ✅ Still out of scope | The Cleaning Teams & Assignments schema tracks assignment and completion timestamps only — not continuous live GPS tracking of team members. |
| 6 | Automated legal enforcement against littering | ✅ Still out of scope | No enforcement or penalty mechanism has been defined in any requirement; the system only reports and prioritizes. |
| 7 | Large-scale fleet management | ✅ Still out of scope | Route optimization remains explicitly deferred to a later phase, per the original proposal's risk mitigation for routing. |

---

## Team Decisions Since the Original Proposal (Noted for Completeness)

These are refinements made while defining requirements — none of them expand scope into any of the seven out-of-scope items above, but are noted here for transparency:

- **Severity/priority scoring approach clarified:** The team confirmed a **rule-based, interpretable scoring system** (based on waste type, quantity/size, repeat occurrence, and report age) as the initial approach, rather than a machine-learning severity model — consistent with the proposal's own suggestion to use an interpretable baseline before considering a learned model.
- **Dataset gap identified:** No public dataset (Egyptian, Arab, or otherwise) exists for local street-level waste imagery or for waste "severity" specifically. The team has planned to collect a small local image sample (target: ~300 images) for fine-tuning, as anticipated in the proposal's risk section — this is a data-collection detail, not a scope change.
- **Detection vs. classification dataset roles clarified:** TACO confirmed as the detection dataset (bounding-box annotated); Garbage Classification v2 and RealWaste confirmed for classification training/validation respectively. This refines *how* the in-scope AI features are built, not *what* is in scope.

**Conclusion:** No changes to the Section 9 scope boundaries are proposed. The list stands as originally defined.
