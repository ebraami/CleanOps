# Notification Timeliness Requirements

Define the acceptable delay between a status or assignment change and the resulting push notification being delivered.

---

## Target Delay Window

**Target:** Under normal network conditions, a push notification must be delivered to the recipient's device within **10 seconds** of the triggering status or assignment change being written to the database.

**Degraded-condition allowance:** Under poor network conditions (weak signal, high latency, or temporary connectivity loss), a delay of up to **60 seconds** is considered acceptable. If the recipient's device is fully offline, the notification is queued by FCM and delivered once connectivity is restored, per FCM's standard queuing behavior (message lifespan configurable up to 28 days; this project will use a much shorter TTL, e.g. 24 hours, since a stale status notification loses its value).

---

## Assumptions Behind the Target

### 1. Network Conditions
- The 10-second target assumes the recipient's device has an active internet connection (Wi-Fi or mobile data) and is not in an extreme battery-saving or Doze mode that defers network access.
- The 60-second degraded allowance accounts for typical mobile-network variability (3G/weak 4G conditions, brief handoffs between cell towers) rather than a complete outage.

### 2. FCM (Firebase Cloud Messaging) Latency
- FCM's own service-level objective states that 95% of HTTP v1 API requests receive a response (i.e., the message is accepted by FCM's backend) in under 350 milliseconds. This covers only the "acceptance" step, not end-to-end delivery to the device.
- FCM documentation states that messages are typically delivered immediately after being accepted, but delivery is not guaranteed to be instant: FCM may intentionally delay messages to preserve device battery life, and delivery depends on device availability.
- To minimize this delay, all status-change and assignment notifications in CleanOps will be sent with FCM's **"high priority"** setting, which instructs FCM to attempt immediate delivery even if the recipient device is in a low-power/sleep state. Normal-priority delivery is not used for these notifications, since it allows FCM to batch or defer delivery.
- Given these factors, a 10-second target under normal conditions is a realistic and slightly conservative window: it allows for backend processing time (writing the status change, triggering the notification function) plus FCM's typical near-immediate delivery, without assuming a zero-latency network.

### 3. Backend Processing
- The 10-second window includes the time taken by the backend to detect the status/assignment change (e.g., via a database trigger or event listener) and construct/send the FCM request — not just FCM's own delivery time. This is a conservative allowance since backend trigger-to-send time is expected to be well under 1 second in practice.

### 4. Scope and Exclusions
- This target applies to standard status-change and assignment notifications (e.g., "report acknowledged," "report assigned to a cleaning team," "report marked resolved"). It does not apply to bulk/broadcast notifications (e.g., system-wide announcements), which may be sent with normal priority and are not time-sensitive in the same way.
- Per FCM's own guidance, push notification services are not designed for safety-critical or emergency use; this target reflects a best-effort operational SLA appropriate for a civic-reporting workflow, not a guaranteed real-time system.

---

## Acceptance Condition

- A status or assignment change triggers a push notification to be sent within 10 seconds under normal network and device conditions.
- Notifications are sent using FCM high-priority delivery to minimize OS-level delay.
- Under degraded network conditions, delivery occurs within 60 seconds or once connectivity is restored, whichever is sooner.
- If a device is offline beyond the configured message TTL, the notification is dropped per FCM's standard behavior rather than delivered late with stale information; the in-app status still reflects the current (correct) state when the user next opens the app.
