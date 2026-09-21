**\*(Performance Requirements Document)**

**1\. Purpose**

This section defines measurable and verifiable non-functional performance requirements for the system. The requirements explicitly cover **Report Submission**, **AI Detection**, **AI Classification**, **AI Scoring / End-to-End AI Analysis Turnaround**, **Dashboard Operations**, and **Map Operations** under clearly defined normal-load conditions.

All requirements are designed to be objectively validated through automated performance and load testing.

**2\. Load Definition and Operating Conditions**

**Normal Load (Baseline Condition)**

For performance testing, **Normal Load** is defined as:

- **Up to 20 concurrent active users** performing a representative mixture of system operations (Report Submission, AI Analysis, Dashboard queries, and Map interactions).
- **Warm-up Period:** The system shall undergo a 5-minute warm-up period before performance measurements are collected.
- **Test Duration:** Measurements shall be collected for a minimum of 30 minutes under sustained normal load.
- **Environment:** Tests shall be conducted under normal server, network, and database operating conditions.

**Peak / Stress Load**

Peak-load testing may additionally be performed with a higher number of concurrent users to identify system saturation limits; however, the formal response-time acceptance criteria defined in this section are evaluated under Normal Load.

**3\. Performance Requirements Target Table**

| **Work Package / Feature** | **Operation** | **Maximum Response Time** | **Operating Condition** | **Measurement Criterion (Acceptance Target)** |
| --- | --- | --- | --- | --- |
| **Report Submission** | Submit a report & receive acknowledgment | $\\le$ 3.0 sec | Normal Load | **P95 $\\le$ 3.0 sec** |
| --- | --- | --- | --- | --- |
| **AI Analysis** | AI Detection (Object/Anomaly Detection) | $\\le$ 5.0 sec | Normal Load | **P95 $\\le$ 5.0 sec** |
| **AI Analysis** | AI Classification | $\\le$ 5.0 sec | Normal Load | **P95 $\\le$ 5.0 sec** |
| **AI Analysis** | AI Scoring | $\\le$ 3.0 sec | Normal Load | **P95 $\\le$ 3.0 sec** |
| **AI Analysis** | **End-to-End AI Analysis Turnaround** (Detection + Classification + Scoring) | $\\le$ 15.0 sec | Normal Load | **P95 $\\le$ 15.0 sec** |
| **Dashboard** | Initial dashboard load (KPI & analytics widgets) | $\\le$ 3.0 sec | Normal Load | **P95 $\\le$ 3.0 sec** |
| **Dashboard** | Filter / query dashboard data | $\\le$ 3.0 sec | Normal Load | **P95 $\\le$ 3.0 sec** |
| **Map Operations** | Initial map / tile / heatmap rendering | $\\le$ 4.0 sec | Normal Load | **P95 $\\le$ 4.0 sec** |
| **Map Operations** | Dynamic spatial query / layer refresh | $\\le$ 2.0 sec | Normal Load | **P95 $\\le$ 2.0 sec** |
| **Global System** | API Error Rate | $< 0.1\\%$ | Normal Load | Measured over the 30-min test period |

**4\. Measurement and Verification Method**

Performance requirements shall be verified using an automated load-testing tool (e.g., _Apache JMeter_ or _k6_).

1. **Simulation:** Simulate 20 concurrent active users executing a scenario mix (Report Submission, AI pipeline execution, Dashboard, and Map queries).
2. **Execution:** Allow a 5-minute warm-up, followed by 30 minutes of continuous metrics collection.
3. **Metrics Recorded:** $P\_{50}$, $P\_{95}$, and $P\_{99}$ response times, request rate, concurrent active users, and API error percentage.
4. **Pass/Fail Criteria:**
    - A response-time requirement is marked as **PASS** if the measured **$P\_{95}$** response time is less than or equal to the defined maximum target.
    - The API error-rate requirement is marked as **PASS** if total failed requests remain below **0.1%** during the test duration.

**5\. Example of Objective Validation**

For the **End-to-End AI Analysis Turnaround** requirement ($P\_{95} \\le 15.0 \\text{ sec}$):

- **Measured Test Results:** $P\_{50} = 8.2 \\text{ sec}$, $P\_{95} = 13.4 \\text{ sec}$, $P\_{99} = 16.1 \\text{ sec}$.
- **Verdict:** **PASS**, because the 95th percentile ($P\_{95} = 13.4 \\text{ sec}$) is strictly below the target limit of $15.0 \\text{ seconds}$.
