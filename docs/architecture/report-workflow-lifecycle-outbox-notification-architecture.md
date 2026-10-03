# Report Workflow Lifecycle & Outbox Notification Architecture

## 1. Purpose

This document defines the operational workflow for CleanStreet AI reports and the asynchronous notification integration. It explains the report lifecycle, backend state enforcement, background triggers, transactional outbox processing, notification dispatch, and retry handling.

The design follows the project proposal, where citizens submit reports with a photo, GPS location, category, and optional description. Reports are analysed and prioritised, assigned to cleaning teams, updated during response, and verified using completion evidence. Notifications are part of the system scope.

## 2. Scope

This document covers:
- Report status lifecycle and transition rules.
- Backend enforcement of report status changes.
- Events that trigger background processing.
- Transactional outbox creation and processing.
- Outbox worker behaviour.
- SMS and push notification dispatch.
- Failure handling and retry semantics.
- Auditability and duplicate protection.

## 3. Report Workflow Lifecycle

The project proposal describes the report workflow as five sequential stages:

1. Reporting
2. Analysis
3. Prioritisation
4. Response
5. Verification

The backend should enforce the lifecycle so that a report cannot move directly to a later stage without satisfying the required processing step.

### Lifecycle flow

```text
Citizen Report
      |
      v
  Reporting
      |
      v
   Analysis
      |
      v
Prioritisation
      |
      v
   Response
      |
      v
 Verification
      |
      v
Verified Resolution
```

The exact persisted state names should follow the project's approved Report Lifecycle State Machine. This document uses the proposal's stage terminology rather than inventing additional official state names.

## 4. Backend State Machine Enforcement

The backend is responsible for controlling report lifecycle transitions.

Rules:
- A report starts when a citizen submits the required report information.
- Analysis occurs after report submission and validates/categorises the request and processes the submitted image.
- Prioritisation uses severity, location density, repeat occurrence, and report age.
- Response begins when a cleaning team receives the prioritised work request and the request is assigned.
- During response, the cleaning team updates progress.
- Verification requires completion evidence from the cleaning team.
- A report must not be treated as finally resolved only because a cleaning team marks the work as complete.
- Verification must confirm the completion evidence before final resolution.
- Every status change should be recorded in the project's status history/audit record.

Invalid transitions should be rejected by the backend rather than relying only on the user interface.

## 5. Background Triggers

Background processing can be triggered by lifecycle events that require asynchronous work.

| Trigger | Background action |
|---|---|
| New report submitted | Process the report and create required notification/event work |
| Report status changes | Create the corresponding notification event |
| Report assigned to a cleaning team | Notify the relevant operational user/team |
| Cleaning progress changes | Create a status-update notification when required |
| Completion evidence submitted | Trigger verification-related processing |
| Report verified/resolved | Create the citizen resolution notification |
| Notification delivery failure | Schedule a retry according to retry policy |

The exact notification recipients and message templates should follow the approved application requirements.

## 6. Transactional Outbox Pattern

The notification system uses a transactional outbox pattern so that a database transaction can record both the business change and the notification event reliably.

### Basic flow

```text
Backend Request
     |
     v
Update Report Status
     |
     +----> Write Status History
     |
     +----> Create Outbox Event
     |
     v
Commit Database Transaction
     |
     v
Outbox Worker
     |
     v
Notification Adapter
     |
     +----> Push Provider
     |
     +----> SMS Provider
```

The report update and creation of the outbox event are committed together. If the transaction fails, neither the business change nor its notification event should be committed.

## 7. Outbox Event Data

An outbox record should contain enough information for reliable processing and auditing.

Recommended fields:
- `id` — unique event identifier.
- `event_type` — type of event, such as report status changed.
- `report_id` — related report identifier.
- `recipient_id` — intended recipient when applicable.
- `channel` — push, SMS, or another approved channel.
- `payload` — notification data required by the adapter.
- `status` — pending, processing, sent, or failed.
- `attempt_count` — number of delivery attempts.
- `available_at` — time when the event can next be processed.
- `created_at` — event creation time.
- `processed_at` — successful processing time.
- `last_error` — latest delivery error when applicable.

The final database field names should follow the project's implementation conventions.

## 8. Outbox Worker Mechanics

The outbox worker continuously looks for pending events that are ready for processing.

Processing steps:
1. Read pending outbox events.
2. Claim an event so multiple workers do not process it at the same time.
3. Build the notification request.
4. Select the correct notification adapter.
5. Send the notification to the external provider.
6. Mark the event as sent after successful delivery.
7. If delivery fails, record the error and schedule a retry.
8. After the configured retry limit, mark the event as failed and make it visible for operational review.

The worker should be safe to restart. Events already completed should not be sent again unnecessarily.

## 9. Notification Dispatch Architecture

Provider-specific details should remain outside the core report workflow.

```text
                +----------------------+
                |   Report Backend     |
                +----------+-----------+
                           |
                           v
                +----------------------+
                | Transactional Outbox |
                +----------+-----------+
                           |
                           v
                +----------------------+
                |    Outbox Worker     |
                +----------+-----------+
                           |
                 +---------+---------+
                 |                   |
                 v                   v
        +----------------+   +----------------+
        | Push Adapter   |   |  SMS Adapter   |
        +-------+--------+   +-------+--------+
                |                    |
                v                    v
        External Push          External SMS
           Provider               Provider
```

Adapters isolate provider-specific APIs from the report workflow, allowing a provider to be changed without changing the report lifecycle logic.

## 10. Retry and Failure Semantics

External notification providers can fail because of temporary network problems, provider errors, rate limits, or unavailable services.

When delivery fails:
- The failure must be recorded.
- The attempt count must increase.
- The event must remain available for retry when the failure is retryable.
- The next retry time should be controlled by the configured retry policy.
- Repeated failures should eventually move the event to a failed state for operational review.
- A permanent failure should not cause the report transaction itself to be rolled back after the business transaction has already committed.

The exact retry count and backoff values should be configurable by the implementation and should not be hard-coded here unless approved elsewhere.

## 11. Idempotency and Duplicate Protection

The notification flow should prevent duplicate processing when a worker restarts or when more than one worker is active.

Controls include:
- A unique outbox event ID.
- Atomic event claiming/locking.
- Persisting the successful delivery result.
- Idempotency support where the external provider supports it.
- Checking the event status before retrying.

The system should distinguish between an event that is still pending and an event that has already been successfully processed.

## 12. Audit and Status History

The project proposal includes a status history mechanism for recording report status changes.

For each lifecycle transition, the system should preserve:
- Report identifier.
- Previous status/stage.
- New status/stage.
- Time of transition.
- Actor or system component responsible for the transition.
- Relevant reason or metadata when required.

Notification processing should also retain enough information to determine whether a notification was sent, retried, or failed.

## 13. End-to-End Example

A typical verified-resolution flow is:

```text
1. Citizen submits a waste report.
2. Backend stores the report.
3. Analysis is performed.
4. Priority is calculated.
5. A cleaning team is assigned.
6. The team updates the work progress.
7. The team submits completion evidence.
8. The report enters verification.
9. The operator reviews the evidence.
10. If verification succeeds, the report moves to final resolution.
11. The backend records the lifecycle change and creates an outbox event in the same transaction.
12. The outbox worker processes the event.
13. The appropriate push/SMS adapter sends the citizen notification.
14. Successful delivery is recorded.
15. If delivery fails temporarily, the event is retried according to the configured retry policy.
```

## 14. Operational Failure Cases

| Failure | System response |
|---|---|
| Database transaction fails | Do not commit the report change or its outbox event |
| Worker stops after claiming an event | Event becomes available again according to the worker's recovery/lease mechanism |
| Push provider temporarily unavailable | Keep event for retry |
| SMS provider temporarily unavailable | Keep event for retry |
| Permanent provider failure | Record failure and expose event for operational review |
| Duplicate worker processing | Use event claiming/idempotency controls |
| Invalid report transition | Reject the transition in the backend |
| Team marks work complete without valid verification | Keep the report in the verification workflow rather than treating it as finally resolved |

## 15. Implementation Alignment

This architecture supports the CleanStreet AI proposal requirements for:
- Report status tracking.
- Cleaning-team assignment and progress updates.
- Completion evidence.
- Notifications.
- Authentication and authorisation.
- Audit/status history.
- PostgreSQL/PostGIS-based backend data management.

The exact state names, transition identifiers, notification templates, provider configuration, retry limits, and timing values should remain aligned with the project's approved architecture and lifecycle specification.

## 16. Acceptance Checklist

- [ ] Report lifecycle transitions are enforced by the backend.
- [ ] Invalid transitions are rejected.
- [ ] Status changes are recorded in status history.
- [ ] Background triggers are defined for required asynchronous work.
- [ ] Business updates and outbox events are committed transactionally.
- [ ] The outbox worker processes pending events.
- [ ] Push and SMS provider adapters are separated from core workflow logic.
- [ ] Successful notifications are recorded.
- [ ] Failed notifications are retried according to configurable policy.
- [ ] Repeated failures are visible for operational handling.
- [ ] Duplicate notification processing is controlled.
- [ ] Completion is not treated as final resolution without the required verification.

## 17. Core Design Principle

The report lifecycle remains the source of truth for the report's business state. Notifications are asynchronous side effects of approved lifecycle events.

The transactional outbox ensures that an important lifecycle event is recorded reliably before an external notification provider is called, while the worker and retry mechanism handle delivery outside the main report transaction.
