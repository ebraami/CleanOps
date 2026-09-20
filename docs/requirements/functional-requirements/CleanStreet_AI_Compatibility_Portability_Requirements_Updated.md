# CleanStreet AI
## Compatibility & Portability Requirements

**Work Package:** Non-Functional Requirements  
**Task:** Compatibility & Portability Requirements  
**Project:** CleanStreet AI — A Smart Citizen-Requested Street Cleaning and Waste Management Platform  
**Proposal Basis:** Updated Graduation Project Proposal

---

## 1. Purpose

This document defines the Compatibility and Portability Requirements for the CleanStreet AI platform.

The requirements are derived from the **Updated CleanStreet AI Graduation Project Proposal**, especially the proposed mobile application, operations dashboard, REST backend, PostgreSQL/PostGIS database, object image storage, AI service, mapping and notification integrations, standalone MVP approach, deployment/testing plan, and future municipal integration.

The requirements are written so that they can be verified during the project's testing and evaluation phases.

> **Technology note:** The updated proposal keeps some implementation choices configurable. The mobile application may use Flutter or native Android, and the mapping solution may use Google Maps Platform or OpenStreetMap-based services. Therefore, the requirements below do not unnecessarily lock the project to one alternative.

---

## 2. Scope

These requirements cover compatibility and portability of:

- Citizen mobile application
- Operations dashboard
- Backend REST APIs
- PostgreSQL/PostGIS database
- Object storage for uploaded images
- AI/computer-vision service
- Mapping and spatial-analysis services
- Authentication and notification services
- Standalone MVP/test deployment
- Development, testing, and pilot environments

---

## 3. Compatibility Requirements

| ID | Requirement | Priority | Verification |
|---|---|---|---|
| **CPR-01** | The citizen application shall provide its implemented core functions, including registration/login, report creation, photo upload, location capture, category selection, report submission, status tracking, and viewing completion evidence, on all device/OS configurations officially selected as supported by the final implementation. | High | Execute functional compatibility tests on every defined supported mobile configuration. |
| **CPR-02** | The operations dashboard shall correctly display and manage the report information required by the implemented workflow, including location, images, category, priority, status, assignment, and completion evidence, on the officially selected dashboard environment(s). | High | Execute dashboard compatibility tests using representative reports and completion records. |
| **CPR-03** | The mobile application, backend REST APIs, database, object storage, AI service, and operations dashboard shall exchange report data without unintended loss, corruption, or modification of supported fields. | High | Perform end-to-end integration tests from report submission through AI analysis and operator resolution. |
| **CPR-04** | Report information shall remain consistent across the citizen application and operations dashboard, including GPS coordinates, category, description, timestamps, status, priority score, assignment information, and image references. | High | Submit test reports and compare stored and displayed values across system components. |
| **CPR-05** | Uploaded report images and completion-evidence images shall remain accessible through the implemented workflow after being stored in the selected object-storage solution, without breaking their associated report records. | High | Upload before/after images, retrieve them from both relevant workflows, and verify their report associations. |
| **CPR-06** | The system shall maintain compatible communication with the selected authentication and notification services when these services are included in the MVP, so that authentication and report-status notifications function correctly. | Medium | Perform integration tests for login/authentication and notification delivery. |
| **CPR-07** | The map-based request visualization shall remain compatible with the mapping solution selected for the implementation, so that report locations, spatial views, and implemented map functions continue to operate correctly. | Medium | Perform map integration tests using reports with valid GPS coordinates. |
| **CPR-08** | Spatial operations required by hotspot detection and duplicate/related-report detection shall remain compatible with the selected PostgreSQL/PostGIS implementation and its supported spatial queries. | Medium | Execute representative nearby-report, clustering, and duplicate-candidate queries and verify expected results. |
| **CPR-09** | The AI service shall accept the image format(s) produced by the citizen-reporting workflow and return analysis results in a format that the backend can store with the corresponding report record. | High | Submit representative images through the complete pipeline and verify that detection/classification results are stored against the correct report. |

---

## 4. Portability Requirements

| ID | Requirement | Priority | Verification |
|---|---|---|---|
| **CPR-10** | The CleanStreet AI MVP shall be deployable as a standalone platform without requiring integration with a real municipal system. | High | Deploy and execute the complete report-to-resolution workflow in a defined test/pilot environment without municipal API integration. |
| **CPR-11** | Environment-specific configuration, including service endpoints, credentials, storage configuration, and other deployment settings, shall be kept separate from core application logic so that the system can be moved between development, testing, and pilot environments primarily through configuration changes. | High | Deploy the system in at least two defined environments using environment-specific configuration values. |
| **CPR-12** | The architecture shall keep the citizen application, backend, database/image storage, AI service, and operations dashboard sufficiently separated so that a component can be replaced, upgraded, or migrated with limited impact on the core report-to-resolution workflow. | Medium | Review the architecture and perform a representative component replacement or migration test where applicable. |
| **CPR-13** | The mapping integration shall be isolated from the core report-management workflow so that the selected mapping solution can be changed without redesigning the core reporting, status-tracking, and assignment logic. | Medium | Replace or reconfigure the mapping integration in a test environment and verify that core report functions remain operational. |
| **CPR-14** | The MVP shall support deployment in a defined local test area when a full municipal pilot is unavailable, with the deployment configuration and limitation documented in the final evaluation. | High | Demonstrate the end-to-end workflow in a defined local test area and document the deployment conditions and limitations. |
| **CPR-15** | The structured report data shall remain deployable using the PostgreSQL/PostGIS database architecture defined by the proposal, while image files shall remain deployable through the selected object-storage solution without requiring changes to the report-management workflow. | Medium | Perform a test deployment using the selected database and object-storage configuration and verify report/image retrieval. |
| **CPR-16** | The system shall be deployable without dependence on future municipal-system integration, large-scale fleet management, or physical waste-collection infrastructure, since these are outside the initial version scope. | High | Demonstrate the MVP using its own reporting, dashboard, assignment, status, and verification workflow. |
| **CPR-17** | The implementation shall allow the mapping, authentication, notification, and object-storage providers to be configured according to the final selected services, without embedding provider-specific assumptions into unrelated core workflow logic where practical. | Medium | Review configuration and integration boundaries and verify that provider-specific settings are isolated from core report-management logic. |

---

## 5. Traceability to the Updated Proposal

| Requirement Area | Updated Proposal Basis |
|---|---|
| Mobile compatibility | Section 9 includes the citizen mobile application; Section 14 specifies Flutter or native Android subject to final technology selection. |
| Dashboard compatibility | Sections 9, 10, 15, and 16 define the cleaning-operations dashboard and its report-management workflow. |
| Backend/API interoperability | Section 14 specifies REST APIs for authentication, report management, AI integration, and analytics. |
| Database/spatial compatibility | Sections 14 and 15 specify PostgreSQL with PostGIS for structured and spatially queryable data. |
| Image-storage compatibility | Section 15 specifies Object Storage for images and a `storage_url` reference in the database. |
| AI pipeline compatibility | Sections 11, 14, and 15 define the image-analysis pipeline and the storage of AI results with the report record. |
| Mapping compatibility | Sections 13 and 14 identify Google Maps Routes API and OpenStreetMap-based services as mapping options. |
| Authentication/notification compatibility | Section 13 identifies Firebase Authentication and Firebase Cloud Messaging as potential services. |
| Standalone portability | Section 19 states that the MVP shall operate as a standalone platform with its own dashboard, with municipal API integration treated as a future-phase enhancement. |
| Local test deployment | Sections 18 and 23 state that a defined local test area can be used when a full municipal pilot cannot be arranged. |
| Environment portability | The proposal defines separate research, requirements/design, MVP, AI, testing, and finalisation phases and describes a deployment/evaluation process. |
| Future integration | Section 22 identifies municipal-system integration and existing complaint-system integration as future expansion, supporting separation from the initial MVP. |

---

## 6. Acceptance Notes

1. The final supported mobile devices and operating-system versions shall be defined during the requirements/design stage before compatibility testing.
2. The final dashboard environment and supported browser/platform configurations shall be defined according to the actual dashboard implementation before compatibility testing.
3. The final mapping, authentication, notification, and image-storage providers shall be recorded once the technology selection is completed.
4. Compatibility claims shall be limited to configurations that are actually selected and tested.
5. Portability testing shall document the source environment, target environment, configuration changes, and any known limitations.
6. The compatibility and portability results shall be included in the project's testing documentation.
7. Requirements that depend on a service not included in the final MVP shall be marked as not applicable rather than treated as failed compatibility requirements.

---

## 7. Relationship to the Updated Proposal

These requirements directly support the updated proposal's architecture and implementation approach:

- **Citizen reporting:** photo, GPS location, category, description, status tracking, and completion evidence.
- **Operations workflow:** report review, AI results, priority scoring, hotspot/repeated-report review, team assignment, monitoring, and verification.
- **AI pipeline:** TACO-based YOLOv8 detection, classification using Garbage Classification v2 with RealWaste validation, and rule-based severity/priority scoring.
- **Spatial functionality:** PostgreSQL/PostGIS, hotspot detection, and duplicate/related-report candidate detection.
- **External services:** mapping, authentication, notifications, and object storage.
- **Standalone MVP:** operation without real municipal API integration.
- **Testing:** functional, security, AI, usability, and end-to-end workflow evaluation.

The updated proposal also explicitly keeps AI as decision support rather than an autonomous operational decision-maker. Compatibility and portability requirements therefore preserve the workflow in which AI outputs are consumed by the backend and reviewed by the human operator.

---

## 8. Source Sections

The main source sections used for this document are:

- **Section 6 — Proposed Solution**
- **Section 9 — Scope**
- **Section 10 — Key Features and Requirements**
- **Section 11 — AI and Intelligent Components**
- **Section 13 — Data Sources and Requirements**
- **Section 14 — Proposed Technology and Methodology**
- **Section 15 — Data Architecture**
- **Section 16 — System Workflow**
- **Section 17 — Security and Privacy Considerations**
- **Section 18 — Feasibility**
- **Section 19 — Risks and Challenges**
- **Section 20 — Expected Outcomes and Deliverables**
- **Section 21 — Development Plan**
- **Section 22 — Future Expansion**
- **Section 23 — Success Criteria**

---

**Document Status:** Updated for the latest CleanStreet AI proposal.
