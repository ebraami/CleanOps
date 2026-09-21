# CleanStreet AI – Usability Checklist

## 1. Report Submission

| ID | Checklist Item | Measurable Acceptance Criteria | Result |
|---|---|---|---|
| RS-01 | Start a Report | The user can start a new report within **2 taps** from the home screen. | ☐ |
| RS-02 | Report Steps | A complete report can be submitted in **no more than 5 main steps**. | ☐ |
| RS-03 | Photo | The user can add **at least 1 photo** before submitting the report. | ☐ |
| RS-04 | Location | The report displays a **location** that the user can review before submission. | ☐ |
| RS-05 | Category | The user can select **1 category** before submitting the report. | ☐ |
| RS-06 | Description | The user can add an **optional description** without preventing submission when it is empty. | ☐ |
| RS-07 | Validation | If a required field is missing, the system **prevents submission and identifies the missing information**. | ☐ |
| RS-08 | Review | The user can review the **photo, location, and category** before final submission. | ☐ |
| RS-09 | Submission Feedback | After successful submission, the system displays a **clear confirmation message**. | ☐ |

## 2. Status Indicators

| ID | Checklist Item | Measurable Acceptance Criteria | Result |
|---|---|---|---|
| SI-01 | Current Status | **100% of submitted reports** display their current status. | ☐ |
| SI-02 | Status Labels | Each report uses a clear text status such as **Acknowledged, In Progress, or Resolved**. | ☐ |
| SI-03 | Status Update | When the report status changes, the **new status is displayed** to the citizen. | ☐ |
| SI-04 | Status Consistency | The status shown in the citizen app matches the **current status stored by the system**. | ☐ |
| SI-05 | Progress Visibility | The citizen can access the current status of a submitted report from the report/history section. | ☐ |
| SI-06 | Resolution Evidence | A report marked **Resolved** provides access to the available completion evidence. | ☐ |

## 3. Accessibility

> **Note: **The project proposal specifies basic accessibility, especially text size and contrast. The measurable criteria below are proposed checklist criteria for usability testing, based on WCAG 2.1 Level AA (contrast) and Material Design guidelines (text size and touch targets).

| ID | Checklist Item | Measurable Acceptance Criteria | Result |
|---|---|---|---|
| AC-01 |   Text Size |  **100% of body text** is displayed at **16sp or larger** at the default text size. | ☐ |
| AC-02 | Text Contrast |   **100% of primary text** has a contrast ratio of **at least 4.5:1** with its background (**3:1** for large text). | ☐ |
| AC-03 | Button Visibility |  **100% of primary action buttons** have a visible text label and a touch target of **at least 48×48 dp**.  | ☐ |
| AC-04 | Status Accessibility | Report status can be understood from **text labels and not color alone**. | ☐ |
| AC-05 | Error Messages | **100% of validation errors** provide a clear text explanation of the problem. | ☐ |
| AC-06 | Consistent Interface | The same action uses the **same label/icon** throughout the application. | ☐ |

## 4. Operator Dashboard

| ID | Checklist Item | Measurable Acceptance Criteria | Result |
|---|---|---|---|
| OD-01 | Report Visibility | **100% of incoming reports** are available in the operator dashboard. | ☐ |
| OD-02 | Report Information | Each report displays its **status, category, location, and priority**. | ☐ |
| OD-03 | Filtering | The operator can filter reports by **status, category, and priority**. | ☐ |
| OD-04 | AI Results | The operator can view the **AI analysis results** for reports that have been analysed. | ☐ |
| OD-05 | Priority | Each active report has a **priority score/level** available to the operator. | ☐ |
| OD-06 | Repeated Reports | The dashboard provides access to information about **repeated reports/hotspots**. | ☐ |
| OD-07 | Team Assignment | The operator can assign an active report to **1 cleaning team**. | ☐ |
| OD-08 | Status Update | The operator can update the status of an assigned report. | ☐ |
| OD-09 | Completion Evidence | The operator can review the **completion evidence** submitted by the cleaning team. | ☐ |
| OD-10 | Final Resolution | A report cannot be finally resolved without **reviewing the completion evidence**. | ☐ |

## Acceptance Rule

> **A checklist item is considered satisfied only when its measurable acceptance criterion is successfully demonstrated during usability testing.**

### Result Legend

- ☐ Not tested
- ✅ Satisfied
- ❌ Not satisfied
