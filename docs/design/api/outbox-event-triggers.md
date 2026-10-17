# CleanStreet AI --- Outbox Pattern & Notification Event Trigger Architecture

**Document path:** `docs/design/api/outbox-event-triggers.md`\
**Project:** CleanStreet AI --- A Smart Citizen-Requested Street
Cleaning and Waste Management Platform\
**Status:** Proposed design for the MVP\
**Related architecture:** PostgreSQL + PostGIS, REST API backend,
citizen mobile application, operations dashboard, object storage for
images, Firebase Cloud Messaging (FCM) for push notifications.

------------------------------------------------------------------------

## 1. Purpose

This document defines how CleanStreet AI creates, processes, and
delivers notification events reliably. It covers database triggers, the
transactional Outbox pattern, background event polling, notification
delivery, retry handling, and the event sequence.

CleanStreet AI lets citizens report waste using a photograph, location,
category, and optional description. Operators review and prioritise
reports, assign cleaning teams, update progress, and verify completion
evidence. Notifications keep citizens and authorised operators informed
as a report moves through this workflow.

The design is intended for the project MVP. It does not assume that
CleanStreet AI performs physical waste collection or that it is already
integrated with every municipal system.

## 2. Design goals

1.  Do not lose a notification event when a report change is committed
    to the database.
2.  Keep the report change and creation of its notification event in the
    same database transaction.
3.  Deliver events asynchronously so that a slow notification provider
    does not block report submission or status updates.
4.  Make retries safe and prevent duplicate processing where possible.
5.  Keep a traceable record of report status changes and notification
    delivery attempts.
6.  Respect user roles, notification preferences where implemented, and
    protection of account and location data.
7.  Keep AI outputs advisory: AI analysis and priority scores may inform
    an operator, but the final operational decision remains with a human
    operator.

## 3. Scope and assumptions

### In scope

-   Database events for report submission, report assignment, status
    changes, and verified resolution.
-   A transactional `OUTBOX_EVENTS` table in PostgreSQL.
-   A background worker that polls pending events.
-   Push notification delivery through Firebase Cloud Messaging (FCM).
-   A provider-neutral delivery interface for optional webhooks.
-   Retry, failure, idempotency, logging, and monitoring rules.
-   A sequence diagram and event specifications.

### MVP assumptions

-   PostgreSQL is the system of record; PostGIS supports location-based
    queries.
-   Images are stored in object storage, while their URLs and metadata
    are stored in PostgreSQL.
-   The backend exposes REST APIs.
-   FCM is the proposed push-notification service, consistent with the
    project proposal.
-   External municipal integration is not an MVP dependency. Generic
    outbound webhooks are documented as an extension point and should
    only be enabled for approved endpoints.
-   Exact framework, queue service, deployment platform, and final event
    naming conventions remain implementation choices.

## 4. Architecture overview

The main components are:

  -----------------------------------------------------------------------
  Component                           Responsibility
  ----------------------------------- -----------------------------------
  Citizen application                 Submits reports and displays report
                                      status and notifications.

  Operations dashboard                Lets authorised operators review
                                      reports, assign teams, update
                                      status, and verify completion.

  REST API backend                    Validates requests, enforces
                                      authentication and authorisation,
                                      and performs business transactions.

  PostgreSQL + PostGIS                Stores users, reports, images
                                      metadata, assignments, status
                                      history, and outbox events.

  Database trigger                    Inserts an outbox event when a
                                      relevant committed data change
                                      occurs.

  Outbox worker / poller              Finds pending events, claims them
                                      safely, and sends them to delivery
                                      handlers.

  Notification service                Builds notification content and
                                      sends push messages through FCM.

  Optional webhook adapter            Sends a minimal event payload to an
                                      explicitly configured, authorised
                                      endpoint.

  Delivery log / event state          Records attempts, success, and
                                      failures for monitoring and retry.
  -----------------------------------------------------------------------

### Core principle

The application must not update a report and then independently attempt
to publish a notification as two unrelated operations. If the report
update succeeds but notification publication fails, the event could be
lost. Instead, the report change and the outbox row are committed
together in one PostgreSQL transaction. A background worker publishes
the event after the transaction commits.

## 5. Event model

Each outbox event should contain at least:

  -----------------------------------------------------------------------
  Field                               Purpose
  ----------------------------------- -----------------------------------
  `id`                                Unique event identifier, generated
                                      by the database or application.

  `event_type`                        Stable name, such as
                                      `report.created` or
                                      `report.status_changed`.

  `aggregate_type`                    Entity type; for this MVP, usually
                                      `report`.

  `aggregate_id`                      ID of the related report.

  `occurred_at`                       Time the event was created.

  `payload`                           JSON data required by the consumer,
                                      with only necessary fields.

  `status`                            Processing state: `pending`,
                                      `processing`, `delivered`, or
                                      `failed`.

  `attempt_count`                     Number of delivery attempts.

  `next_attempt_at`                   Earliest time a retry may occur.

  `locked_at`                         Time a worker claimed the event, if
                                      applicable.

  `delivered_at`                      Time successful delivery was
                                      recorded.

  `last_error`                        Sanitised summary of the latest
                                      failure.

  `idempotency_key`                   Stable key used to identify the
                                      event during processing.
  -----------------------------------------------------------------------

### Suggested SQL shape

The following is a design proposal and should be adjusted to the
project's migration conventions.

``` sql
CREATE TABLE outbox_events (
    id UUID PRIMARY KEY,
    event_type TEXT NOT NULL,
    aggregate_type TEXT NOT NULL DEFAULT 'report',
    aggregate_id UUID NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    payload JSONB NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'processing', 'delivered', 'failed')),
    attempt_count INTEGER NOT NULL DEFAULT 0,
    next_attempt_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    locked_at TIMESTAMPTZ,
    delivered_at TIMESTAMPTZ,
    last_error TEXT,
    idempotency_key TEXT NOT NULL UNIQUE
);

CREATE INDEX outbox_pending_idx
    ON outbox_events (next_attempt_at, occurred_at)
    WHERE status IN ('pending', 'processing');

CREATE INDEX outbox_aggregate_idx
    ON outbox_events (aggregate_type, aggregate_id, occurred_at);
```

**Implementation note:** use the actual primary-key data type of
`REPORTS.id` for `aggregate_id`; the proposal does not specify whether
report IDs are UUIDs or another type. If report IDs are not UUIDs,
adjust this column accordingly. A foreign key may be added if the team
wants outbox rows to be retained only while the related report exists;
otherwise, keep the event history independent so that audit and delivery
records remain available.

## 6. Events that produce notifications

The event is the durable record of a meaningful workflow change. The
notification worker decides which recipient and delivery channel are
appropriate.

  ---------------------------------------------------------------------------------------
  Event type                      Triggering change  Intended          Suggested message
                                                     recipient         purpose
  ------------------------------- ------------------ ----------------- ------------------
  `report.created`                A citizen report   Citizen; operator Confirm that the
                                  is created         queue may refresh report was
                                  successfully.      separately.       received.

  `report.analysis_completed`     AI analysis and    Operations        Tell operators the
                                  priority fields    workflow, if a    report is ready
                                  have been saved.   notification is   for review.
                                                     useful.           

  `report.assigned`               A report is        Authorised        Communicate
                                  assigned to a      operators/team    assignment or
                                  cleaning team.     recipients;       acknowledgement.
                                                     citizen           
                                                     notification is   
                                                     optional.         

  `report.status_changed`         `current_status`   Citizen who owns  Show
                                  changes.           the report;       acknowledgement or
                                                     authorised        in-progress
                                                     operators as      status.
                                                     needed.           

  `report.completion_submitted`   A team submits     Operator          Request review of
                                  completion         responsible for   completion
                                  evidence.          verification.     evidence.

  `report.resolved`               An authorised      Citizen who       Confirm resolution
                                  operator verifies  submitted the     and availability
                                  evidence and       report.           of evidence.
                                  resolves the                         
                                  report.                              

  `report.reopened`               Verification fails Assigned team and Explain that
                                  or further action  responsible       further action is
                                  is required.       operator; citizen required.
                                                     update as         
                                                     appropriate.      
  ---------------------------------------------------------------------------------------

Not every internal event needs a push notification. For example, the
dashboard can refresh or poll for internal changes. Push messages should
be sent only when they provide useful information to a real recipient.

### Status-change rule

`STATUS_HISTORY` is the audit record for status changes, as described in
the project proposal. The backend should make the status update and
status-history insert within one transaction. The outbox event must be
created in that same transaction. The exact allowed status names must be
defined by the implementation team and used consistently by the app,
backend, and database.

## 7. Database trigger specifications

Triggers should be narrow and predictable. They should capture committed
business events, not call FCM, make HTTP requests, or perform
long-running AI work.

### Trigger A --- report created

-   **Table:** `REPORTS`
-   **Timing:** `AFTER INSERT`, for each row.
-   **Action:** insert `report.created` into `OUTBOX_EVENTS`.
-   **Payload:** report ID, submitting user ID, category ID, creation
    timestamp, and current status, as available.
-   **Privacy:** do not copy full address details, raw image bytes,
    authentication data, or unnecessary personal information into the
    event.

### Trigger B --- report status changed

-   **Table:** `REPORTS`
-   **Timing:** `AFTER UPDATE`, for each row, only when `current_status`
    changes.
-   **Action:** insert `report.status_changed` with the report ID,
    previous status, new status, and change time.
-   **Audit:** the API transaction should also insert the corresponding
    `STATUS_HISTORY` row.
-   **Important:** do not emit this event for unrelated updates such as
    a description correction or priority-score refresh.

### Trigger C --- assignment created or changed

-   **Table:** `ASSIGNMENTS`
-   **Timing:** `AFTER INSERT`, and `AFTER UPDATE` only if the assigned
    team or meaningful assignment state changes.
-   **Action:** insert `report.assigned` with report ID, assignment ID,
    team ID, and timestamp.
-   **Recipient lookup:** resolve notification recipients from current
    authorised team membership at delivery time, or use a carefully
    controlled recipient reference. Do not trust recipient IDs supplied
    by an untrusted client.

### Trigger D --- completion evidence submitted

-   **Table:** the existing image/assignment/report structure, according
    to the final schema.
-   **Timing:** after the transaction records completion evidence and
    the workflow enters a review-needed state.
-   **Action:** insert `report.completion_submitted`.
-   **Constraint:** the proposal specifies an `IMAGES` table for
    before/after evidence but does not define the final evidence-upload
    status field. The team must connect this event to the actual field
    or endpoint used by the implementation.

### Trigger E --- report resolved or reopened

-   **Table:** `REPORTS`
-   **Timing:** `AFTER UPDATE`, only when the status transitions to the
    agreed resolved or reopened state.
-   **Action:** insert `report.resolved` or `report.reopened`.
-   **Rule:** a team marking work complete must not by itself close a
    report. An authorised operator reviews completion evidence and makes
    the final resolution decision, consistent with the proposal's
    operator workflow.

### Trigger implementation notes

-   Use a shared trigger function or small dedicated functions to keep
    payload structure consistent.
-   Generate a unique ID and idempotency key for each event.
-   Keep triggers free of network calls. A network failure must never
    roll back a valid report change just because a push provider is
    unavailable.
-   Avoid duplicate events by checking whether the relevant business
    field actually changed.
-   If a single database operation causes multiple meaningful changes,
    define whether it emits multiple distinct events or one canonical
    event; document the choice and test it.
-   Do not emit an event when a transaction rolls back. PostgreSQL will
    roll back the outbox row along with the business update.

## 8. Background polling and event claiming

A worker periodically queries the outbox for events whose status is
`pending` and whose `next_attempt_at` is due. To support more than one
worker safely, the worker should claim rows in a short transaction using
`FOR UPDATE SKIP LOCKED`, mark them `processing`, and set `locked_at`.
It should commit the claim before making any external network call.

Conceptual query:

``` sql
WITH batch AS (
    SELECT id
    FROM outbox_events
    WHERE status = 'pending'
      AND next_attempt_at <= now()
    ORDER BY occurred_at
    FOR UPDATE SKIP LOCKED
    LIMIT 100
)
UPDATE outbox_events AS e
SET status = 'processing',
    locked_at = now(),
    attempt_count = attempt_count + 1
FROM batch
WHERE e.id = batch.id
RETURNING e.*;
```

This is a conceptual example. Production code must also recover stale
`processing` rows whose worker died, apply an appropriate batch size,
and respect database transaction boundaries.

### Polling rules

1.  Poll at a configurable short interval, or use a queue/wakeup signal
    later if needed.
2.  Claim only a limited batch at a time.
3.  Commit the claim transaction before sending notifications.
4.  Process each event independently so one bad event does not block the
    whole batch.
5.  Set `delivered` and `delivered_at` only after the delivery provider
    reports success.
6.  If a worker stops while an event is `processing`, allow a recovery
    process to return stale claims to `pending` after a defined lease
    timeout.
7.  Use metrics for pending-event count, oldest pending age, retry
    count, failed events, and delivery latency.

## 9. Notification delivery

### Push notifications via Firebase Cloud Messaging

FCM is the proposed MVP push provider in the project proposal. The
notification service should:

1.  Validate the event type and payload.
2.  Determine the intended recipient using server-side ownership and
    role checks.
3.  Resolve the recipient's registered device token(s).
4.  Build a short notification title and body.
5.  Send a message containing a minimal payload, such as event ID,
    report ID, event type, and current status.
6.  Record the provider result and update the outbox event state.
7.  Remove or deactivate invalid device tokens according to the provider
    response and application policy.

Push payloads should not contain sensitive personal information, full
location histories, or image URLs that bypass access controls. The app
should fetch protected report details through the authenticated API.

### Optional webhook delivery

The task title mentions webhook delivery. The proposal names FCM for
push notifications but does not define a municipal webhook integration.
Therefore, webhooks should be treated as an optional adapter, not a
required dependency for the MVP.

If webhooks are enabled for a trusted integration:

-   Only administrators may register or change endpoint URLs and event
    subscriptions.
-   Use HTTPS and sign each request with an HMAC secret or an equivalent
    authenticated mechanism.
-   Include `event_id`, `event_type`, `occurred_at`, and a minimal
    payload.
-   Include an idempotency/event identifier so receivers can deduplicate
    retries.
-   Set connection and response timeouts.
-   Reject private, loopback, link-local, and otherwise disallowed
    destination addresses to reduce server-side request forgery risk.
-   Do not follow redirects to unvalidated destinations.
-   Store secrets securely; never place them in event payloads or logs.
-   Retry transient errors and record permanent failures.
-   Do not expose an endpoint for arbitrary users to submit URLs.

## 10. Retry policy and failure handling

At-least-once delivery is the practical guarantee: an event may be
attempted more than once, so consumers must be idempotent. A database
transaction alone cannot guarantee exactly-once delivery to an external
provider.

### Suggested retry schedule

Use exponential backoff with jitter. An example schedule is
approximately 1 minute, 2 minutes, 4 minutes, 8 minutes, and so on,
capped at a configurable maximum such as 1 hour. The exact limits should
be configurable and tested.

-   **Transient error:** network timeout, rate limit, or provider server
    error. Retry.
-   **Permanent error:** invalid payload or a permanently invalid
    destination. Mark failed after classification and alert/log for
    review.
-   **Invalid FCM token:** deactivate the token; do not retry the same
    token indefinitely.
-   **Maximum attempts reached:** mark the event `failed`, retain the
    failure reason in a sanitised form, and make it visible to an
    administrator or monitoring dashboard.
-   **Recovery:** an authorised operator or controlled replay process
    may requeue a failed event after the underlying issue is corrected.

Never log access tokens, secrets, full personal data, or sensitive
image/location details in error messages.

## 11. Idempotency and ordering

### Idempotency

-   `OUTBOX_EVENTS.id` is the stable event identifier.
-   `idempotency_key` should be unique and derived from the business
    event identity, not from a random value on every retry.
-   Consumers should record processed event IDs when they perform side
    effects that they control.
-   Re-sending a push notification after a timeout can still create a
    duplicate if the provider accepted the first request but the
    response was lost. The app should therefore handle repeated event
    IDs gracefully and avoid duplicate in-app entries.
-   Do not assume FCM provides exactly-once delivery.

### Ordering

Events for one report should normally be processed in `occurred_at`
order. However, parallel workers and retries can cause later events to
be delivered first. Include a report version or status timestamp if
strict client-side ordering is needed, and have the client ignore stale
updates. If strict ordering is required, partition processing by report
ID or prevent multiple events for the same report from being processed
concurrently.

## 12. Sequence flow

``` mermaid
sequenceDiagram
    autonumber
    actor Citizen
    participant App as Citizen App
    participant API as REST API Backend
    participant DB as PostgreSQL + PostGIS
    participant Trigger as Database Trigger
    participant Outbox as OUTBOX_EVENTS
    participant Worker as Background Poller
    participant Notify as Notification Service
    participant FCM as Firebase Cloud Messaging
    participant Operator as Operations Dashboard

    Citizen->>App: Submit waste report with photo and location
    App->>API: POST report
    API->>DB: Begin transaction
    API->>DB: Insert REPORTS row
    DB->>Trigger: AFTER INSERT
    Trigger->>Outbox: Insert report.created event
    API->>DB: Insert related metadata / commit
    DB-->>API: Transaction committed
    API-->>App: Report accepted with report ID

    loop Poll due events
        Worker->>Outbox: Claim pending events with SKIP LOCKED
        Outbox-->>Worker: Claimed event batch
    end
    Worker->>Notify: Process report.created
    Notify->>DB: Resolve authorised recipient and device token
    DB-->>Notify: Recipient/device details
    Notify->>FCM: Send push notification
    FCM-->>Notify: Provider result
    Notify->>Outbox: Mark delivered or schedule retry

    Operator->>API: Update status / assign team
    API->>DB: Update report and insert STATUS_HISTORY
    DB->>Trigger: Relevant status/assignment change
    Trigger->>Outbox: Insert corresponding event
    DB-->>API: Commit
    Worker->>Outbox: Claim next due event
    Worker->>Notify: Process event
    Notify->>FCM: Send appropriate notification
    FCM-->>Notify: Provider result
    Notify->>Outbox: Record result
    App->>API: Fetch current report status
    API->>DB: Read authorised report details
    DB-->>API: Current status and permitted evidence
    API-->>App: Updated report details
```

### Flow explanation

1.  The citizen submits a report through the app.
2.  The backend validates the request and starts a database transaction.
3.  PostgreSQL stores the report. A trigger writes the corresponding
    outbox event in the same transaction.
4.  The transaction commits, and the API confirms the report was
    accepted.
5.  A background worker claims the pending event and passes it to the
    notification service.
6.  The service resolves the authorised recipient and sends a push
    message through FCM.
7.  The result is recorded. Temporary failures are scheduled for retry.
8.  Later assignment and status changes follow the same pattern.
9.  The app fetches the latest report state from the authenticated API;
    the push message is a prompt to refresh, not the source of truth.

## 13. Security and privacy

The design follows the proposal's security requirements:

-   Require authentication for citizen and operator actions.
-   Enforce role-based authorisation for report details, assignment,
    evidence, and resolution.
-   Use secure API communication and protected image storage.
-   Minimise data in outbox payloads and push messages.
-   Protect location data and user account information.
-   Keep an audit trail of important status changes using
    `STATUS_HISTORY`.
-   Define image and event retention periods and delete non-essential
    data when required.
-   Consider face and vehicle-plate blurring for uploaded images where
    feasible.
-   Restrict webhook delivery to approved endpoints and protect signing
    secrets.
-   Ensure an event ID alone never grants access to a report.

## 14. Observability and operational support

Track the following:

-   Number of pending events.
-   Age of the oldest pending event.
-   Delivery success and failure counts by event type and provider.
-   Retry attempts and events moved to `failed`.
-   Time from event creation to successful delivery.
-   Stale `processing` rows and worker health.
-   Invalid or expired device tokens.
-   Webhook response codes and latency, if webhooks are enabled.

Provide a controlled way to inspect failed events and retry them after
fixing the cause. Any replay action should be authorised and audited.

## 15. Testing requirements

  -----------------------------------------------------------------------
  Test                                Expected result
  ----------------------------------- -----------------------------------
  Create a report successfully        Report and `report.created` outbox
                                      event commit together.

  Roll back report creation           Neither report nor its outbox event
                                      remains committed.

  Change report status                One relevant status event is
                                      created and `STATUS_HISTORY` is
                                      updated in the same transaction.

  Update an unrelated report field    No status-change event is emitted.

  Assign a cleaning team              An assignment event is created once
                                      for the meaningful change.

  FCM succeeds                        Event is marked delivered and
                                      delivery time is stored.

  FCM times out or returns a          Event is retried using backoff.
  transient error                     

  FCM token is invalid                Token is deactivated and not
                                      retried indefinitely.

  Worker crashes after claiming an    Stale claim is recovered after the
  event                               lease timeout.

  Two workers poll simultaneously     Row locking prevents them from
                                      claiming the same pending row at
                                      the same time.

  Same event is processed again       The consumer handles it
                                      idempotently where possible.

  Citizen requests another user's     API denies access regardless of
  report                              event IDs or notification payload.

  Completion evidence is submitted    Operator receives a review event;
                                      report is not automatically
                                      resolved.

  Operator verifies completion        Resolution event is generated and
                                      the citizen can receive an update.

  Webhook URL is untrusted or unsafe  Registration or delivery is
                                      rejected by endpoint policy.
  -----------------------------------------------------------------------

## 16. Implementation checklist

-   [ ] Confirm the actual data type of `REPORTS.id` and final status
    names.
-   [ ] Add the `OUTBOX_EVENTS` migration and indexes.
-   [ ] Implement trigger functions for report creation and relevant
    status changes.
-   [ ] Implement assignment and completion-evidence event hooks against
    the final schema.
-   [ ] Ensure report update, `STATUS_HISTORY` insertion, and event
    insertion share the intended transaction.
-   [ ] Implement worker claiming with `SKIP LOCKED` and stale-claim
    recovery.
-   [ ] Implement the notification service and FCM token management.
-   [ ] Add retry/backoff, failure state, and authorised replay.
-   [ ] Add metrics and structured, privacy-safe logs.
-   [ ] Test transaction rollback, concurrency, retry, duplicate
    handling, and access control.
-   [ ] Decide whether outbound webhooks are needed for the MVP; keep
    them disabled unless approved.
-   [ ] Document environment variables and secrets in the project's
    secure configuration guide, not in this file.

## 17. Decisions still to confirm

The proposal supports the overall architecture, but it does not settle
the following implementation details. The team should confirm them
during backend/database design:

1.  Whether primary keys use UUIDs or another type.
2.  The final list of report statuses and permitted transitions.
3.  The backend framework and migration tooling.
4.  The poller schedule, batch size, retry ceiling, and stale-lock
    timeout.
5.  How device tokens are stored and associated with authenticated
    users.
6.  Whether notifications are push-only for the MVP or also appear in an
    in-app notification centre.
7.  Whether any approved external webhook consumer exists. Municipal
    integration is currently out of scope.
8.  The exact event produced when completion evidence is uploaded, based
    on the final implementation schema.

## 18. Summary

The transactional Outbox pattern gives CleanStreet AI a reliable bridge
between database changes and asynchronous notifications. Database
triggers create durable events for important report workflow changes; a
background poller claims and processes those events; and the
notification service delivers push messages through FCM, with optional
secured webhooks only if a trusted integration is approved.

The report database remains the source of truth. Notifications help
users notice changes, while the authenticated API provides the latest
authorised report details. AI analysis and priority scoring support the
operator, and final report resolution remains a human decision.
