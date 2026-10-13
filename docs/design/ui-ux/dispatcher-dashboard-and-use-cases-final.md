# Operations Dispatch Dashboard & UML Use Case Diagram

## Project
**CleanOps — Smart Reporting, Efficient Dispatch, Cleaner Tomorrow**

## Figma Design
[Open the UML Use Case Diagram in Figma](https://www.figma.com/design/GQvq4wCQCUapmlbzYqGIlT/Untitled?node-id=42-1536&t=FmoC52kmBpgszV23-1)

## Diagram Export
The UML Use Case Diagram export is included in this submission as `UML Use Case Diagram.png`.

> When uploading to GitHub, place the PNG in the same directory as this Markdown file, or update the image path below to match where you store it.

![CleanOps UML Use Case Diagram](UML%20Use%20Case%20Diagram.png)

## 1. System Boundary and Functional Areas

The diagram defines the **CleanOps System** boundary and groups use cases into four functional areas:

- **Citizen Services**
- **Dispatcher / Operator Operations**
- **System & AI Services**
- **Cleaning Team Operations**

## 2. Actors

### Citizen
The Citizen (Resident) interacts with citizen-facing functions:
- Register / Login
- Submit Cleaning Report
- Track Report Status
- View Notifications
- View Completion Evidence
- Confirm Resolution

### Operator
The Operator (Municipal Dispatcher) interacts with operational and dispatch functions:
- Login
- View Reports
- Review Report
- View Map / Hotspots
- Assign Cleaning Team
- Monitor Cleaning Tasks
- Review Completion Evidence
- Update Report Status

### Cleaning Team
The Cleaning Team (Field Crew) interacts with field-work functions:
- Login
- View Assigned Tasks
- View Task Details
- Start Cleaning Task
- Update Task Progress
- Upload Completion Evidence

## 3. Use Cases and Relationships

### Citizen Services
- **Submit Cleaning Report** includes **Upload Image**.
- **Submit Cleaning Report** includes **Provide Location**.
- Other citizen use cases shown are Register / Login, Track Report Status, View Notifications, View Completion Evidence, and Confirm Resolution.

### Dispatcher / Operator Operations
- **Review Report** includes **View AI Analysis**.
- **Review Report** includes **View Priority Score**.
- Other operator use cases shown are Login, View Reports, View Map / Hotspots, Assign Cleaning Team, Monitor Cleaning Tasks, Review Completion Evidence, and Update Report Status.

### System & AI Services
- Run AI Analysis
- Determine Priority Score
- Detect Location Hotspots
- Generate Reports
- Send Notifications

The diagram shows **Run AI Analysis** with an `<<extend>>` relationship to **Determine Priority Score** and an `<<include>>` relationship to **Detect Location Hotspots**.

### Cleaning Team Operations
- **Upload Completion Evidence** includes **Submit Completion Evidence**.
- Other cleaning-team use cases shown are Login, View Assigned Tasks, View Task Details, Start Cleaning Task, and Update Task Progress.

## 4. Main Workflow Summary

1. A citizen registers or logs in and submits a cleaning report, including an image and location.
2. The operator views and reviews reports, using AI analysis and the priority score to help assess them.
3. The operator assigns a cleaning team and monitors cleaning tasks.
4. The cleaning team views assigned tasks, opens task details, starts work, updates progress, and uploads completion evidence.
5. The operator reviews completion evidence and updates the report status.
6. The citizen can track the report, view notifications and completion evidence, and confirm resolution.

## 5. Notes

- The diagram separates citizen, operator, AI/system, and cleaning-team use cases into clearly labeled areas within the CleanOps System boundary.
- The PNG is a visual export of the diagram; the Figma link above points to the editable design.
- This document describes the use cases visible in the supplied diagram. The separate dispatcher dashboard screens should be documented or linked when available.
