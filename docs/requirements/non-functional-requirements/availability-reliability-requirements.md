# Availability & Reliability Requirements
### CleanStreet AI — Backend & AI Service

**Scope:** Define availability expectations for the Backend System and AI Service, and specify the fallback behavior when the AI Service is temporarily unavailable.

---

## 1. Backend and AI Service Separation

The CleanStreet AI architecture treats the Backend System and AI Service as separate components (Section 15.1, Figure 4).

The **Backend System** is responsible for core application functions — API operations, database access, report management, and image storage. The **AI Service** performs image analysis and supports report prioritization. The architecture describes the backend as storing the submitted report and image first, after which the AI component analyzes the image and writes its analysis results back to the system.

This separation means temporary AI failure should not prevent the core reporting workflow from operating. It is also consistent with the proposal's design principle that AI is a decision-support component, with the final operational decision remaining with the operator (Section 16.3).

---

## 2. Availability Targets

| Component | Proposed Availability Target | Purpose |
|---|---|---|
| **Backend System** | 99.5% monthly availability | Protects the core citizen and operator workflow, including authentication, report submission, storage, and tracking. |
| **AI Service** | 99% monthly availability | Supports image analysis and prioritization while remaining non-blocking to the core reporting workflow. |
| **AI Recovery** | 15-minute proposed RTO | Target for resuming queued AI processing after the AI service becomes available. |

*Note: These values are proposed project requirements for the MVP/pilot phase. The project proposal does not specify numerical uptime targets explicitly.*

**Planned maintenance** may be excluded from the availability calculation when it is scheduled in advance, communicated at least 24 hours beforehand, and performed outside expected peak reporting periods. *These maintenance rules are also proposed operational requirements, not drawn from the proposal.*

---

## 3. Availability Measurement

Availability should be monitored separately for the Backend System and AI Service. A proposed implementation is a dedicated health-check endpoint for each service (Backend: `/health`, AI Service: `/health`), polled periodically to record service failures, downtime duration, and recovery time.

*Note: The health-check mechanism and polling interval are proposed implementation details; they are not explicitly defined in the project proposal.*

---

## 4. Fallback Behavior When the AI Service Is Unavailable

**Main rule:** AI downtime must not prevent citizens from submitting reports or operators from reviewing and managing reports. This follows the project's architecture, in which the report and image are stored before AI analysis is performed.

### 4.1 Citizen-Facing Behavior
- The citizen can still create and submit a waste report.
- The report image and required information are stored normally.
- The citizen receives the normal submission confirmation and tracking ID.
- The report remains visible in the citizen's history and tracking interface.
- The report is marked **"Pending AI Analysis,"** and this status is visible to the citizen in the report detail/tracking view — the citizen is informed that AI analysis is pending, while report submission and tracking continue normally.
- The citizen does not need to resubmit the report when the AI Service becomes available.
- The citizen's manually selected report category remains available and displayed even if AI analysis has not yet completed.

### 4.2 Backend Behavior
The backend treats AI analysis as a separate processing step, not a requirement for successful report submission.
- The report is saved successfully; the uploaded image remains stored.
- The report is placed in a pending AI-processing state and kept available for later processing.
- Failed AI-processing attempts do not result in loss of the original report or image.

*A proposed implementation is a retry queue with progressively increasing intervals — e.g., 1 minute → 5 minutes → 15 minutes → every 15 minutes thereafter. This retry strategy is a proposed implementation detail, not a requirement explicitly stated in the proposal.*

### 4.3 Operator-Facing Behavior
Operators can still manage reports while the AI Service is unavailable. Reports awaiting analysis are clearly identified (e.g., "AI Analysis: Pending"). The operator can still:
- View the report, its image, and its location.
- Review the citizen-provided category and description.
- Manually prioritize the report.
- Assign the report to a cleaning team.
- Continue the operational workflow without waiting for AI.

AI-dependent features — automated image analysis and AI-based prioritization — remain unavailable until the AI Service recovers, consistent with the proposal's principle that AI supports decisions while the operator makes the final call.

---

## 5. Recovery Behavior

When the AI Service becomes available again:
- Pending reports are submitted for AI analysis and processed by the service.
- Analysis results are saved against the corresponding reports; priority/category/severity fields are updated where applicable.
- Each report remains linked to its original submission and tracking ID — no citizen is required to submit again.

**Manual decisions during AI downtime:** If an operator has already manually reviewed or assigned a report while AI was unavailable, a later AI result does not silently undo that operational decision. The AI result is instead stored as additional decision-support information for the operator to consider.

*This behavior is a proposed reliability/operational rule derived from the project's human-in-the-loop design, rather than an explicit rule stated in the proposal.*

---

## 6. Feature Availability During AI Downtime

| Function | During AI Downtime |
|---|---|
| Citizen registration/login | Available |
| Report creation | Available |
| Image upload/storage | Available |
| Location capture | Available |
| Category selection | Available |
| Report tracking | Available |
| Operator dashboard | Available |
| Manual report review | Available |
| Manual assignment | Available |
| AI image analysis | Temporarily unavailable |
| AI priority scoring | Temporarily unavailable |
| AI-dependent duplicate detection | Temporarily unavailable |
| AI-dependent hotspot/analysis features | Temporarily unavailable |

The proposal identifies AI image analysis, priority scoring, and derived duplicate/related-report detection as the AI-supported capabilities (Section 11) — this table simply confirms none of them sit on the critical path for core citizen or operator functions.

---

## 7. Acceptance Conditions

| Requirement | Acceptance Condition |
|---|---|
| Backend availability | Backend has a proposed target of ≥99.5% monthly availability. |
| AI availability | AI Service has a proposed target of ≥99% monthly availability. |
| Report submission during AI outage | A citizen can successfully submit a report while the AI Service is unavailable. |
| No data loss | Reports and uploaded images submitted during AI downtime remain stored and available. |
| Pending AI state | Reports waiting for AI processing are clearly identified as pending. |
| Operator continuity | Operators can view, manually prioritize, and assign reports without AI results. |
| Automatic recovery | Pending reports are processed automatically when the AI Service becomes available again. |
| No duplicate submission | Citizens do not need to resubmit reports after AI recovery. |
| Manual decision preservation | A later AI result does not silently overwrite an operator's existing assignment or operational decision. |
| AI result persistence | Completed AI analysis is stored against the original report. |

---

## Delivered Means

A documented **99.5% monthly uptime target** for the Backend System and a documented **99% monthly uptime target** for the AI Service (with a 15-minute recovery objective), together with a documented fallback in which — during AI downtime — reports and images are saved normally, marked "Pending AI Analysis," remain fully available for citizen tracking and manual operator review/assignment, are retried automatically on a defined backoff schedule, and receive AI results attached to the original report without overwriting any decision an operator already made.

---

## Source Note

The proposal supports the backend-first architecture (Section 15.1) and the AI decision-support role (Section 16.3). It does **not** explicitly specify: the 99.5%/99% uptime targets, the 15-minute RTO, the "Pending AI Analysis" status, the health-check/polling mechanism, the retry-interval schedule, or the no-overwrite rule on manually assigned reports. These are proposed implementation requirements for this task, consistent with the proposal's architecture and principles but not drawn verbatim from it.

*End of section.*
