**Performance Requirements Matrix**

| **Operation / System Action** | **Description** | **Target / Maximum Acceptable Response Time** |
| --- | --- | --- |
| **Report Submission** | Time taken from user submission until the report is successfully stored in the database. | **$\\le$ 2 seconds** |
| --- | --- | --- |
| **AI Analysis — Detection** | Object detection / anomaly recognition phase by the AI model. | **$\\le$ 3 seconds** |
| **AI Analysis — Classification** | Categorization and classification of detected issues. | **$\\le$ 2 seconds** |
| **AI Analysis — Scoring** | Risk scoring and severity index calculation. | **$\\le$ 1 second** |
| **Total AI Analysis Turnaround** | End-to-end AI pipeline execution (Detection + Classification + Scoring). | **$\\le$ 6 seconds** |
| **Dashboard Load Time** | Initial render and data fetch for main analytical dashboards under normal load. | **$\\le$ 2 seconds** |
| **Map Load Time** | Rendering interactive maps and loading spatial data/geolocations under normal load. | **$\\le$ 3 seconds** |
