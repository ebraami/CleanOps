# Data Privacy, Anonymization, and Storage Access Policy

**Work Package:** Security Requirements  
**Task:** Data Privacy, Anonymization, and Storage Access Policy  
**Project:** CleanStreet AI — Smart Citizen-Requested Street Cleaning and Waste Management Platform

---

## 1. Purpose

This document defines the privacy, anonymization, data-minimisation, retention, and storage-access requirements for the CleanStreet AI platform.

The requirements are based on the updated project proposal, especially its Security and Privacy Considerations and the identified privacy risk concerning uploaded images that may contain identifiable people, vehicles, or addresses.

---

## 2. Privacy Scope

The policy applies to:

- Citizen account information.
- Report information submitted by citizens.
- GPS/location information associated with reports.
- Uploaded waste/report images.
- Cleaning completion evidence images.
- Status and workflow information.
- Operator access to citizen and report data.
- Image/object storage used by the platform.
- Audit information for important status changes.

The proposal identifies location data and uploaded images as potentially sensitive contextual information because they may contain identifiable people, vehicles, or addresses.

---

## 3. Data Minimisation

The system shall collect and retain only the data necessary for the intended functions of the platform.

Examples include:

- Account information required for authentication and user management.
- Report image required for waste/issue analysis.
- Location required to identify the reported problem.
- Waste category and optional description required to describe the report.
- Status information required to track the request.
- Completion evidence required to verify that cleaning was performed.

The system shall avoid collecting additional personal or contextual information when it is not required for the intended workflow.

---

## 4. Image Privacy and Anonymization

Uploaded images may contain identifiable people, vehicle details, or addresses.

### 4.1 Automated Blurring

Where feasible, the system should apply automated anonymization to identifiable visual information.

The proposal specifically identifies:

- Face blurring.
- License-plate blurring.

The anonymization process should reduce unnecessary exposure of identifiable information while preserving the image information needed for waste detection, classification, and report verification.

### 4.2 Raw Image Access

Raw uploaded images shall not be publicly accessible.

Access to raw images shall be restricted to authorised operator accounts and other system components that require the images for an approved project function.

### 4.3 Completion Evidence

Cleaning-team completion evidence is also report evidence and shall follow the same access-control and privacy principles as report images.

---

## 5. Storage Access Policy

The platform uses object image storage for uploaded images and completion evidence.

| Data / Resource | Access Requirement |
|---|---|
| Citizen account data | Authorised application functions and user access only |
| Citizen report data | According to user role and report workflow |
| GPS/location information | Authorised functions and users only |
| Raw report images | Authorised operator accounts and required system processing |
| Completion evidence | Authorised users/components involved in verification and tracking |
| Status history | Authorised workflow tracking and audit purposes |
| Object image storage | Must not be exposed as unrestricted public storage |

The system shall enforce access control rather than relying only on the secrecy of storage URLs.

---

## 6. Authentication and Authorisation

The proposal requires:

- Authentication.
- Role-based authorisation.
- Access control for citizen and operator data.

The system shall verify a user's identity before allowing access to protected application resources.

Access permissions shall depend on the user's role and the function being performed.

At minimum, the system distinguishes between citizen-facing access and operator-facing access.

Operators may access the report information and evidence required to review, prioritise, assign, monitor, and verify reports.

Citizens shall only access information that belongs to them or is intentionally exposed through the citizen workflow.

---

## 7. Secure Communication

The proposal identifies secure API communication as a security requirement.

Protected data exchanged between the mobile application, backend services, operations dashboard, and related services shall use secure communication mechanisms.

API access shall be authenticated and authorised according to the user's role and requested operation.

---

## 8. Location Privacy

Location information is necessary because reports are associated with geographic locations and the operations workflow uses location information for report management and hotspot/repeated-report analysis.

Therefore:

1. Location data shall be collected only when required for the report workflow.
2. Access shall be restricted to authorised application functions and users.
3. Location information shall not be exposed publicly without a defined project requirement.
4. Location data shall be handled according to the project's retention and deletion policy.

---

## 9. Retention and Deletion

The proposal requires a defined retention period and deletion policy.

The system shall define a retention period for non-essential image data.

After the defined retention period:

- Non-essential image data shall be deleted.
- Data that must remain for an explicitly required project function may be retained according to the approved retention policy.
- Stored image data and its active application references should be removed where applicable.

**Implementation note:** The proposal requires a defined retention period but does not specify an exact number of days. The final duration must therefore be agreed and documented before implementation/testing rather than invented in this document.

---

## 10. Audit Logging

Important status changes shall be recorded for auditability.

The proposal identifies the `STATUS_HISTORY` table for this purpose.

The audit trail should support tracking of:

- Report status changes.
- When the change occurred.
- The progression of a report through the workflow.

---

## 11. Privacy Requirements

| ID | Requirement | Priority |
|---|---|---|
| DPR-01 | Collect and retain only data necessary for intended platform functions. | High |
| DPR-02 | Treat uploaded images as potentially sensitive because they may contain identifiable people, vehicles, or addresses. | High |
| DPR-03 | Apply automated face and license-plate blurring where feasible. | High |
| DPR-04 | Restrict raw image access to authorised operator accounts and required system processing. | High |
| DPR-05 | Enforce role-based authorisation for protected data. | High |
| DPR-06 | Protect location information from unauthorised access. | High |
| DPR-07 | Protect user account information from unauthorised access. | High |
| DPR-08 | Use secure API communication for protected application communication. | High |
| DPR-09 | Establish a defined retention period for non-essential image data. | High |
| DPR-10 | Delete non-essential image data after the approved retention period. | High |
| DPR-11 | Record important status changes through the project's audit mechanism. | Medium |
| DPR-12 | Apply the same access-control and privacy principles to completion evidence. | High |
| DPR-13 | Do not expose object image storage as unrestricted public storage. | High |

---

## 12. Access-Control Matrix

| Resource | Citizen | Operator | System / Processing |
|---|---|---|---|
| Own account information | Allowed | As required by authorised role | Required application functions |
| Own submitted reports | Allowed | Allowed for operational review | Required |
| Other citizens' account information | Not allowed | Only when required by authorised function | Only when required |
| Raw report images | Through authorised application workflow | Allowed for authorised operational review | Required for approved processing |
| Completion evidence | Allowed for the relevant report | Allowed for verification | Required for approved processing |
| GPS/location information | Allowed for own relevant reports | Allowed for authorised operational functions | Required for spatial functions |
| Status history | Relevant status through application | Operational/audit functions | Workflow tracking |
| Object storage directly | Not publicly exposed | Not publicly exposed; authorised access | Controlled system access |

---

## 13. Privacy-Aware Workflow

```text
Citizen Creates Report
        |
        v
Image + Location + Category + Description
        |
        v
Privacy / Access Controls
        |
        +----> Image anonymization where feasible
        |
        v
Secure Storage / Processing
        |
        v
AI Analysis
        |
        v
Operator Review
        |
        v
Cleaning Team Assignment
        |
        v
Completion Evidence
        |
        v
Authorised Evidence Review
        |
        v
Resolution / Further Action
        |
        v
Retention Policy Applied
        |
        v
Deletion of Non-Essential Image Data
        |
        v
Audit / Status History Maintained
```

---

## 14. Security Testing and Acceptance

The project's success criteria require authentication, authorisation, and data-protection controls to pass functional and security testing with no critical findings outstanding.

Testing should verify at least:

1. Unauthorised users cannot access protected report or account information.
2. Citizens cannot access another citizen's protected information through normal application functions.
3. Raw image access is restricted according to the defined authorisation rules.
4. Operator access works according to the defined role.
5. Location information is protected from unauthorised access.
6. Secure API communication is used for protected communication.
7. Face/plate anonymization works where the implemented feature supports it.
8. Retention and deletion rules are correctly applied once the final retention period is defined.
9. Important status changes are recorded in the audit trail.
10. Completion evidence follows the defined access-control rules.

---

## 15. Items Requiring Final Project Decision

The updated proposal establishes the privacy principles but leaves some implementation details to be finalised.

The following must be explicitly defined before final implementation:

- Exact retention duration for non-essential images.
- Final image-storage provider/configuration.
- Exact anonymization technology and its supported detection cases.
- Final role/permission mapping in the implemented system.
- Exact deletion mechanism for stored objects and associated references.

These items should not be treated as already implemented unless confirmed by the project team.

---

## 16. Traceability to the Updated Proposal

This policy is based on the project's Security and Privacy Considerations and related proposal content:

- Authentication.
- Role-based authorisation.
- Secure API communication.
- Secure image storage.
- Access control for citizen and operator data.
- Protection of location information.
- Protection of user account information.
- Audit logging for important status changes through `STATUS_HISTORY`.
- Data minimisation and retention policies.
- Protection of images that may contain identifiable people, vehicles, or addresses.
- Automated face/plate blurring where feasible.
- Restricted raw image access to authorised operator accounts.
- Defined retention and deletion policy.

The proposal also identifies security and testing documentation as a project deliverable and requires the security/privacy controls to pass functional and security testing.

---

## 17. Source Basis

Primary source: **CleanStreet AI — Updated Graduation Project Proposal**

Relevant proposal areas include:

- Security and Privacy Considerations.
- Data Architecture / `STATUS_HISTORY`.
- System Workflow.
- Risks and Challenges — Privacy.
- Expected Outcomes and Deliverables.
- Success Criteria — Security and Privacy.
