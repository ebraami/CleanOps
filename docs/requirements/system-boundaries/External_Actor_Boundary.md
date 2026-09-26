# External Actor Boundary

## 1. External Actors

CleanStreet AI has three main external actors for the operational workflow: Citizens, Operators, and Cleaning-Team Members.

| External Actor | Entry Point | Scope of Interaction | Boundary / Cannot Do |
|---|---|---|---|
| **Citizen** | Citizen Mobile Application | Register and log in; create and submit waste/cleanliness reports; provide an image, GPS location, category, and description; track submitted reports; receive updates; view completion evidence; and confirm resolution. | Does not directly access internal system services such as the database or AI service. Cannot assign requests to cleaning teams or make the operator's final operational resolution decision. |
| **Operator** | Operations Dashboard | Log in and access the dashboard; view and review incoming reports; check AI analysis results; review priority scores; check hotspots and repeated reports; assign requests to cleaning teams; monitor progress; review completion evidence; and resolve the request or take further action. | Operates through the Operations Dashboard. The operator is not the direct user of the internal AI or database interfaces. |
| **Cleaning-Team Member** | Cleaning Workflow / Operations Dashboard | Receive assigned cleaning requests; view assigned work; carry out the cleaning task; update progress/status; and provide completion information/evidence, including before/after evidence where applicable. | Cannot make the final `Resolved` decision. Cannot assign the request to another team unless such a capability is explicitly added later. Does not directly access the internal AI or database interfaces. |

## 2. System Boundary

External actors interact with CleanStreet AI through the application's defined interfaces. Citizens use the citizen application, operators use the Operations Dashboard, and cleaning teams use the cleaning workflow/dashboard.

The backend, PostgreSQL/PostGIS database, object storage, and AI service are internal system components. The backend stores report data and image links, while the AI service analyses submitted images and writes analysis results back to the database. External actors interact with these services through the application and dashboard rather than through their internal interfaces.

## 3. Operational Boundary

The workflow separates reporting, operational management, and cleaning work:

- **Citizen:** submits and tracks the report.
- **Operator:** reviews, prioritises, assigns, monitors, and makes the final operational resolution decision.
- **Cleaning Team:** handles the assigned cleaning request, updates progress, and provides completion evidence.

A cleaning team cannot close a report simply by marking its work complete. The operator reviews the completion evidence and either resolves the request or takes further action if the work was not completed properly.

## 4. Summary

| Actor | Entry Point | Main Interaction |
|---|---|---|
| **Citizen** | Citizen Mobile Application | Report and track waste/cleanliness issues. |
| **Operator** | Operations Dashboard | Review, prioritise, assign, monitor, and resolve requests. |
| **Cleaning-Team Member** | Cleaning Workflow / Operations Dashboard | Handle assigned requests, update progress, and provide completion evidence. |

