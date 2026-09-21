# Performance Requirements

## 1. Purpose

This section defines measurable and verifiable non-functional performance requirements for the system. The requirements cover **report submission, AI analysis, Dashboard operations, and Map operations** under clearly defined normal-load conditions.

The requirements are designed to be objectively validated through performance and load testing.

## 2. Load Definition and Operating Conditions

### Normal Load

For performance testing, **Normal Load** is defined as:

- Up to **20 concurrent active users**.
- Users perform a representative mixture of system operations, including:
    - Report submission.
    - AI analysis requests.
    - Dashboard loading and filtering.
    - Map loading, zooming, panning, and layer/data refresh.
- The workload shall represent typical expected system usage rather than a stress or peak scenario.
- The system shall undergo a **5-minute warm-up period** before performance measurements are collected.
- Measurements shall be collected for a minimum of **30 minutes** under sustained normal load.
- Tests shall be conducted under normal server, network, and database operating conditions.

### Peak/Stress Load

Peak-load testing may additionally be performed with a higher number of concurrent users to identify the system's performance limits; however, the response-time requirements defined in this section are evaluated primarily under **Normal Load**.

# 3. Performance Requirements

| **Work Package / Feature** | **Operation** | **Maximum Response Time** | **Operating Condition** | **Acceptance Criterion** |
| --- | --- | --- | --- | --- |
| **Report Submission** | Submit a report and receive successful submission response | ≤ **3 sec** | Normal Load | **P95 ≤ 3 sec** |
| --- | --- | --- | --- | --- |
| **AI Analysis** | Detection | ≤ **5 sec** | Normal Load | **P95 ≤ 5 sec** |
| **AI Analysis** | Classification | ≤ **5 sec** | Normal Load | **P95 ≤ 5 sec** |
| **AI Analysis** | Scoring | ≤ **3 sec** | Normal Load | **P95 ≤ 3 sec** |
| **AI Analysis** | Complete analysis: Detection + Classification + Scoring | ≤ **15 sec** | Normal Load | **P95 ≤ 15 sec** |
| **Dashboard** | Initial dashboard load including KPI/analytics widgets | ≤ **3 sec** | Normal Load | **P95 ≤ 3 sec** |
| **Dashboard** | Filter/query dashboard data | ≤ **3 sec** | Normal Load | **P95 ≤ 3 sec** |
| **Map Operations** | Initial map/tile/heatmap rendering | ≤ **4 sec** | Normal Load | **P95 ≤ 4 sec** |
| **Map Operations** | Dynamic spatial query / layer refresh | ≤ **2 sec** | Normal Load | **P95 ≤ 2 sec** |
| **Global System** | API error rate | < **0.1%** | Normal Load | Measured over the complete test period |

# 4. Measurement and Verification Method

Performance requirements shall be verified using an automated load-testing tool such as **Apache JMeter or k6**.

The testing procedure shall be:

1. Simulate up to **20 concurrent active users** performing a representative workload.
2. Run the system for a **5-minute warm-up period**.
3. Collect performance measurements for at least **30 minutes** under sustained normal load.
4. Record:
    - **P50 response time**
    - **P95 response time**
    - **P99 response time**
    - Number of requests
    - Number of concurrent users
    - Error rate
5. The **P95 response time** shall be used as the primary acceptance criterion for response-time requirements.
6. A response-time requirement is considered **PASS** when the measured P95 is less than or equal to the specified target.
7. The API error-rate requirement is considered **PASS** when the measured error rate remains below **0.1%** during the test period.

# 5. Example of Objective Validation

For example, if the Dashboard Initial Load requirement is:

**P95 ≤ 3 seconds**

and the performance test produces:

- P50 = 1.2 sec
- P95 = 2.6 sec
- P99 = 3.8 sec

then the requirement **passes**, because the measured P95 of **2.6 seconds** is below the maximum allowed **3 seconds**.
