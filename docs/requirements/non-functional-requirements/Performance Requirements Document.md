**(Performance Requirements Document)**

**1\. Overview & Purpose**

The purpose of this section is to define measurable, verifiable non-functional performance requirements for the application (specifically for Dashboard and Map operations) under clearly specified load conditions and target percentiles.

**2\. Load Definitions & Operating Conditions**

To ensure requirement testability, system load categories are defined as follows:

- **Normal Load (Baseline):**
    - **Dashboard Operations:** Up to **100 concurrent active users** (or ~50 requests per second across dashboard telemetry/analytics endpoints).
    - **Map Operations:** Up to **150 concurrent active users** performing map interactions (pan, zoom, layer toggle, risk heatmap rendering) (or ~80 requests per second to GIS/tile APIs).
- **Peak Load (Stress Threshold):**
    - Up to **500 concurrent active users** (or ~300 requests per second across the system).

**3\. Performance Requirements & Metrics**

| **Work Package / Feature** | **Operation / API Endpoint** | **Target Response Time** | **Operating Condition** | **Measurement Criterion (Percentile)** |
| --- | --- | --- | --- | --- |
| **Dashboard** | Load Analytics & KPI Widgets | $\\le$ 2.0 seconds | Normal Load | **95th Percentile ($P\_{95}$)** |
| --- | --- | --- | --- | --- |
| **Dashboard** | Filter Data / Query Reports | $\\le$ 3.0 seconds | Normal Load | **95th Percentile ($P\_{95}$)** |
| **Map Operations** | Initial Map Tile & Heatmap Render | $\\le$ 2.5 seconds | Normal Load | **95th Percentile ($P\_{95}$)** |
| **Map Operations** | Dynamic Spatial Query / Layer Refresh | $\\le$ 1.5 seconds | Normal Load | **99th Percentile ($P\_{99}$)** |
| **Global System** | API Error Rate | $< 0.1\\%$ | Normal Load | Measured over 1-hour window |

**4\. Verification & Validation Method**

- **Testing Tool:** Performance load testing will be conducted using tools like _Apache JMeter_ / _k6_.
- **Validation Criteria:**
    1. Automated load test scripts will simulate the specified number of concurrent users / requests per second.
    2. Performance requirements are considered **PASSED** if $95\\%$ of sample requests ($P\_{95}$) complete within the specified response time under normal load conditions over a sustained period of 30 minutes.
