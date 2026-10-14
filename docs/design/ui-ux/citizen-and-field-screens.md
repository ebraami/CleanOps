# CleanOps --- Citizen & Cleaning Team Mobile UI/UX Specification

**Project:** CleanOps --- An AI-Powered Application for Waste Reporting
& Smart Cleaning Management\
**Work Package:** UI/UX Design System & Figma Prototype\
**Task:** Citizen & Cleaning Team Mobile Figma Prototype\
**Priority:** High\
**Target deadline shown in assignment:** 2026-10-14\
**Required repository path:**
`docs/design/ui-ux/citizen-and-field-screens.md`\
**Role:** UI/UX Design\
**Status:** Design specification and prototype handoff

**Figma prototype:** [Open the CleanOps
prototype](https://www.figma.com/proto/GQvq4wCQCUapmlbzYqGIlT/Untitled?page-id=63%3A125&node-id=87-490&p=f&viewport=352%2C218%2C0.16&t=2r61c0Qyjn5qeKGM-1&scaling=scale-down&content-scaling=fixed&starting-point-node-id=87%3A116)

------------------------------------------------------------------------

## 1. Purpose

This document defines the mobile UX expectations for CleanOps' two
field-facing audiences:

1.  **Citizens**, who submit waste/cleanliness reports and track
    progress.
2.  **Cleaning team members**, who review assigned work, inspect
    report/location details, update task status, and submit completion
    evidence.

It provides the design scope, target screen inventory, user journeys,
interaction behavior, UI states, shared design-system guidance,
accessibility considerations, Figma prototype checks, PNG export
requirements, and acceptance criteria.

The supplied Figma link is the interactive design reference. This
document describes the expected coverage and validation criteria;
reconcile the screen inventory with the actual Figma frames before
claiming each screen is present.

## 1.1 Supplementary mockups added with this revision

The two PNGs below are supplementary visual mockups prepared for the deliverable package: a citizen submission-success screen and a cleaning-team completion-evidence screen. They are **draft mockups**, not direct exports from the linked Figma file. Before marking this task fully complete, import or recreate them in Figma using the project's existing components/tokens, connect their prototype interactions, and export the approved final frames from Figma. Do not present the generated drafts as proof that the linked prototype already contains these frames.

### Citizen — submission success

![CleanOps citizen report submission success mockup](assets/citizen-and-field-screens/citizen-submission-success.png)

### Cleaning team — completion evidence

![CleanOps field completion evidence mockup](assets/citizen-and-field-screens/field-completion-evidence.png)

## 2. Product and UX goals

CleanOps is an AI-powered application for waste reporting and smart
cleaning management. The mobile experience should make reporting and
field execution clear, reliable, and efficient.

-   Make citizen reporting straightforward for first-time users.
-   Capture enough information to identify and locate a waste issue.
-   Make report status and next steps understandable.
-   Help field staff scan assigned jobs and identify the next permitted
    action.
-   Prevent accidental status changes and duplicate submissions.
-   Provide clear loading, empty, validation, permission, error, and
    success states.
-   Reuse consistent components, status labels, and visual tokens across
    both roles.

### Design principles

1.  **Action clarity:** one clear primary action per screen where
    practical.
2.  **Progress visibility:** show current status and the next expected
    step.
3.  **Trust:** explain why location, camera, or photo access is
    requested.
4.  **Error prevention:** validate required fields and confirm
    consequential actions.
5.  **Field usability:** use readable text, clear hierarchy, and
    touch-friendly controls.
6.  **Consistency:** reuse design tokens and components.
7.  **Accessibility:** never communicate status by color alone.

## 3. Scope

### In scope

-   Citizen report submission flow.
-   Citizen confirmation and report tracking.
-   Cleaning-team assigned task list and task details.
-   Work-status updates and completion evidence.
-   Shared navigation, cards, status indicators, forms, dialogs, and
    feedback states.
-   Clickable Figma prototype and high-resolution PNG exports.
-   Design handoff and review checklist.

### Out of scope unless separately approved

-   Backend/API implementation.
-   AI model implementation or claims about model accuracy.
-   Production authentication architecture.
-   Dispatch optimization algorithms.
-   Admin/operations web dashboard.
-   Final legal/privacy policy wording.

## 4. Users and needs

  -----------------------------------------------------------------------
  User                    Need                    Desired UX outcome
  ----------------------- ----------------------- -----------------------
  Citizen                 Report a waste issue    Clear, validated
                          with useful details     submission flow

  Citizen                 Understand what         Visible status and
                          happened after          report details
                          submission              

  Cleaning team member    Identify assigned work  Scannable list with
                                                  location and status

  Cleaning team member    Understand a job at the Clear task details and
                          site                    next permitted action

  Cleaning team member    Record completed work   Evidence flow and
                                                  truthful status
                                                  feedback
  -----------------------------------------------------------------------

## 5. Target screen inventory

The following is the target inventory to use when auditing the Figma
prototype. Keep, rename, or remove entries to match actual frames and
approved product requirements. Do not claim a screen is implemented
until its frame exists.

### 5.1 Citizen screens

  -----------------------------------------------------------------------
  ID                Screen            Expected content  Primary action
  ----------------- ----------------- ----------------- -----------------
  C-01              Citizen home /    Report entry      Start report
                    report entry      point and access  
                                      to existing       
                                      reports if        
                                      supported         

  C-02              Report issue      Category,         Continue
                                      optional          
                                      description,      
                                      photo/evidence    
                                      entry if          
                                      supported         

  C-03              Choose location   Map/location      Confirm location
                                      preview and       
                                      selected position 

  C-04              Review report     Entered details,  Submit report
                                      location,         
                                      evidence,         
                                      validation        

  C-05              Submission        Confirmation and  View report /
                    success           report reference  home
                                      if returned by    
                                      system            

  C-06              My reports        List of reports   Open report
                                      and their current 
                                      statuses          

  C-07              Report details /  Report details    Return to reports
                    tracking          and available     
                                      lifecycle history 
  -----------------------------------------------------------------------

### 5.2 Cleaning-team screens

  -----------------------------------------------------------------------
  ID                Screen            Expected content  Primary action
  ----------------- ----------------- ----------------- -----------------
  F-01              Assigned tasks    Assigned jobs,    Open task
                                      location,         
                                      category, status, 
                                      priority if       
                                      available         

  F-02              Task details      Issue summary,    Take permitted
                                      location,         action
                                      evidence, current 
                                      status            

  F-03              Work in progress  Active task       Update task
                                      context and       
                                      progress action   

  F-04              Completion        Capture/select    Submit evidence
                    evidence          and review        
                                      evidence if       
                                      supported         

  F-05              Completion        Acknowledgement   Return to tasks
                    confirmation      and actual        
                                      resulting task    
                                      state             

  F-06              Task unavailable  Explanation if    Retry / return
                    / error           task changed or   
                                      is no longer      
                                      actionable        
  -----------------------------------------------------------------------

**Lifecycle rule:** UI labels and permitted actions must match the
approved CleanOps lifecycle/backend contract. If evidence review is
required before final resolution, distinguish "work completed/evidence
submitted" from "report resolved." Do not introduce new production
states in the UI.

## 6. Core user journeys

### 6.1 Citizen report journey

``` text
Citizen Home
    ↓
Start Report
    ↓
Enter Issue Details
    ↓
Choose / Confirm Location
    ↓
Review Report
    ↓
Submit
    ↓
Success Confirmation
    ↓
View Report Status
```

Interaction requirements: - Preserve entered information when navigating
between steps where feasible. - Clearly identify required fields and
validate them before submission. - Explain location/camera permission
requests when needed. - If permission is denied, offer a manual
alternative only if supported. - Show loading during submission and
prevent duplicate submits. - Confirm success only after the server
confirms submission. - On failure, preserve input where possible and
offer retry. - Display a report reference only if the system returns
one.

### 6.2 Citizen tracking journey

``` text
My Reports → Select Report → View Details + Current Status → Return
```

Interaction requirements: - Status text must be understandable without
color. - Display only lifecycle events available from the system. -
Distinguish current status from historical events. - If no reports
exist, show a helpful empty state and relevant next action. - If data
fails to load, provide retry instead of a blank screen.

### 6.3 Cleaning-team journey

``` text
Assigned Tasks
    ↓
Open Task
    ↓
Review Issue + Location
    ↓
Start Work (if allowed)
    ↓
Perform Cleaning
    ↓
Record Completion Evidence
    ↓
Submit Evidence / Completion
    ↓
Confirm Actual Resulting State
```

Interaction requirements: - Show only actions permitted for the task's
current state and user role. - Display current task state on list and
details views. - Confirm consequential actions where accidental
activation could cause an operational issue. - If a task was reassigned
or changed elsewhere, explain that it is no longer actionable and
refresh the state. - Do not treat evidence submission as final
resolution unless the approved lifecycle defines it that way. - If
evidence upload fails, preserve selected evidence where possible and
allow retry.

## 7. Shared design system

Use existing Figma design tokens if already established. Do not
introduce conflicting colors, fonts, or spacing values.

  -----------------------------------------------------------------------
  Token group                         Values to document in Figma
  ----------------------------------- -----------------------------------
  Color                               Primary, secondary, background,
                                      surface, text, muted text, border,
                                      success, warning, error,
                                      information

  Typography                          Font family, heading scale, body
                                      sizes, captions, weights, line
                                      heights

  Spacing                             Consistent scale for screen
                                      padding, sections, cards, and
                                      controls

  Shape                               Card/input/button radius and border
                                      widths

  Elevation                           Shadow rules for cards/modals if
                                      used

  Iconography                         Icon family, sizes, stroke/filled
                                      usage

  Interaction                         Default, pressed, focused,
                                      disabled, loading, selected

  Status                              Approved lifecycle labels, icons,
                                      and accessible descriptions
  -----------------------------------------------------------------------

### Reusable components

-   Primary, secondary, text, and destructive buttons.
-   Text input and multiline description input.
-   Category selector.
-   Photo/evidence attachment tile.
-   Location preview/selection component.
-   Report card and assigned-task card.
-   Status chip with text label.
-   Progress indicator where useful.
-   Inline validation message.
-   Loading indicator/skeleton.
-   Empty-state panel and error/retry panel.
-   Confirmation dialog/bottom sheet.
-   Success feedback component.

Every interactive component should define default, pressed/selected,
disabled, focus, and applicable loading/error states.

## 8. Status and feedback states

Status labels must match the backend's canonical state vocabulary. Map
each approved state to a human-readable label, visual treatment, and
accessible text description.

  -----------------------------------------------------------------------
  Condition                           Required UX behavior
  ----------------------------------- -----------------------------------
  Loading                             Show progress and prevent duplicate
                                      action when appropriate

  Empty                               Explain there is no content and
                                      offer a relevant next action

  Validation error                    Put the message near the field and
                                      explain how to fix it

  Network/server error                State that the action did not
                                      complete and offer retry

  Permission denied                   Explain the impact and offer a
                                      supported alternative

  Submission success                  Confirm only after successful
                                      response

  Stale report/task                   Refresh or explain that information
                                      changed

  Disabled action                     Make disabled state clear; explain
                                      why when necessary
  -----------------------------------------------------------------------

Do not rely on green/red alone to communicate success or failure. Pair
color with text and/or a meaningful icon.

## 9. Forms and error prevention

For each form, document: - Required and optional fields. - Accepted
formats and limits, when defined by product requirements. - Validation
timing (on blur, on submit, or both). - Exact error-message wording. -
Behavior after validation failure. - Whether data is preserved when
navigating backward. - Duplicate-submit prevention. - Behavior when
leaving an incomplete flow.

Rules must match the product/backend contract. Do not invent category
lists, file-size limits, image formats, or mandatory fields without
confirmation.

## 10. Location, camera, and evidence UX

-   Request permissions only when the user initiates a feature that
    needs them.
-   Explain the purpose before the operating-system prompt where
    practical.
-   Provide manual location entry only if supported when GPS is
    unavailable/denied.
-   Make the selected location visible before submission.
-   Let users review selected evidence before submission where
    supported.
-   Show upload progress and a clear retry behavior.
-   Never imply an image or report uploaded if the operation failed.
-   Avoid exposing sensitive information in notifications or screenshots
    unless necessary.

## 11. Accessibility and mobile usability

Use WCAG 2.2 AA as a design reference where applicable, subject to the
project's approved accessibility requirements.

-   Maintain sufficient text/background contrast.
-   Use readable text and avoid tiny captions for essential information.
-   Pair status colors with labels/icons.
-   Use clear, action-oriented button labels.
-   Aim for touch targets around 44 × 44 CSS pixels or platform
    equivalent.
-   Support text scaling without clipping essential actions.
-   Use persistent form labels; do not rely on placeholders alone.
-   Give icon-only controls meaningful accessible labels.
-   Associate errors with their relevant fields.
-   Preserve logical focus order and visible focus treatment.
-   Do not make gestures the only way to perform essential actions.

## 12. Responsive/device considerations

-   Respect safe areas and system bars.
-   Keep primary actions visible when the keyboard opens.
-   Prevent horizontal overflow and clipped text.
-   Keep task/report context understandable on small screens.
-   Test long addresses, long category names, missing photos, and empty
    descriptions.
-   Define behavior for slow connections and interrupted uploads.
-   Ensure location/map controls remain usable on small devices.

## 13. Figma prototype requirements

The Figma file should have clearly named frames and working prototype
links for the main journeys.

-   [ ] Citizen can navigate from report entry to submission
    confirmation.
-   [ ] Back navigation preserves entered data where intended.
-   [ ] Required-field validation is represented.
-   [ ] Location selection/confirmation is represented if in scope.
-   [ ] Evidence selection/review is represented if in scope.
-   [ ] Success and failure outcomes are represented.
-   [ ] Citizen can inspect report status if tracking is in scope.
-   [ ] Cleaning-team member can open an assigned task and inspect
    details.
-   [ ] Only valid next actions appear for the task's current state.
-   [ ] Evidence submission and feedback are represented.
-   [ ] Main journeys contain no dead-end prototype links.
-   [ ] Frame names are consistent and the starting frame is
    intentional.
-   [ ] Team Leader has permission to open the prototype.

**Prototype:** [Open CleanOps mobile
prototype](https://www.figma.com/proto/GQvq4wCQCUapmlbzYqGIlT/Untitled?page-id=63%3A125&node-id=87-490&p=f&viewport=352%2C218%2C0.16&t=2r61c0Qyjn5qeKGM-1&scaling=scale-down&content-scaling=fixed&starting-point-node-id=87%3A116)

## 14. High-resolution PNG export requirements

The assignment explicitly requires exported high-resolution PNG mockups.
Export final approved frames from Figma and commit the images with this
document.

### Recommended repository structure

``` text
docs/
└── design/
    └── ui-ux/
        ├── citizen-and-field-screens.md
        └── assets/
            └── citizen-and-field-screens/
                ├── citizen-home.png
                ├── citizen-report-issue.png
                ├── citizen-location.png
                ├── citizen-review-report.png
                ├── citizen-submission-success.png  # supplementary draft included
                ├── citizen-my-reports.png
                ├── citizen-report-details.png
                ├── field-assigned-tasks.png
                ├── field-task-details.png
                ├── field-work-in-progress.png
                ├── field-completion-evidence.png   # supplementary draft included
                └── field-completion-confirmation.png
```

These filenames are a suggested export plan, not proof that those frames
already exist. Export only frames present in the final approved Figma
file and adjust the index to match.

### Export checklist

-   [ ] Export final approved frames, not rough drafts or hidden
    explorations.
-   [ ] Use PNG format at a resolution suitable for high-resolution
    review.
-   [ ] Keep the complete mobile frame visible; do not crop important
    UI.
-   [ ] Use consistent filenames and frame names.
-   [ ] Check text, icons, and edges for clipping or rendering issues.
-   [ ] Confirm every referenced image exists at its committed
    repository path.
-   [ ] Update the index below to match actual exports.

### Exported mockup index

Replace these suggested paths with the actual exported assets and mark
them verified before final submission.

  ----------------------------------------------------------------------------------------------------------------------------------------
  Screen                  Suggested PNG path                                                                       Status
  ----------------------- ---------------------------------------------------------------------------------------- -----------------------
  Citizen home            `docs/design/ui-ux/assets/citizen-and-field-screens/citizen-home.png`                    Pending export

  Citizen report issue    `docs/design/ui-ux/assets/citizen-and-field-screens/citizen-report-issue.png`            Pending export

  Citizen location        `docs/design/ui-ux/assets/citizen-and-field-screens/citizen-location.png`                Pending export

  Citizen review report   `docs/design/ui-ux/assets/citizen-and-field-screens/citizen-review-report.png`           Pending export

  Citizen submission      `docs/design/ui-ux/assets/citizen-and-field-screens/citizen-submission-success.png`      Draft mockup included; verify against Figma
  success                                                                                                          

  Citizen my reports      `docs/design/ui-ux/assets/citizen-and-field-screens/citizen-my-reports.png`              Pending export

  Citizen report details  `docs/design/ui-ux/assets/citizen-and-field-screens/citizen-report-details.png`          Pending export

  Field assigned tasks    `docs/design/ui-ux/assets/citizen-and-field-screens/field-assigned-tasks.png`            Pending export

  Field task details      `docs/design/ui-ux/assets/citizen-and-field-screens/field-task-details.png`              Pending export

  Field work in progress  `docs/design/ui-ux/assets/citizen-and-field-screens/field-work-in-progress.png`          Pending export

  Field completion        `docs/design/ui-ux/assets/citizen-and-field-screens/field-completion-evidence.png`       Draft mockup included; verify against Figma
  evidence                                                                                                         

  Field completion        `docs/design/ui-ux/assets/citizen-and-field-screens/field-completion-confirmation.png`   Pending export
  confirmation                                                                                                     
  ----------------------------------------------------------------------------------------------------------------------------------------

**Before submitting:** do not leave `Pending export` statuses or
nonexistent paths in the final version. Remove rows for screens not in
the approved design and add rows for actual frames.


### Asset verification note

The two PNG assets bundled with this document are design drafts created for review. They have not been verified against the source Figma frames and should not be labelled “Figma exports” until the final approved frames are exported from Figma. The Figma link above is the source prototype; this document does not claim to modify that file.

## 15. Design handoff

The handoff should communicate: - Approved frame names and purpose. -
Primary/secondary actions and navigation destinations. -
Required/optional fields and validation behavior. - Status labels and
their corresponding backend states. - Loading, empty, error, offline,
and success behavior. - Location/camera permission behavior. - Evidence
upload and retry behavior. - Responsive/safe-area considerations. -
Shared tokens and reusable components. - Prototype link and exported PNG
paths.

If a behavior depends on an undecided backend rule, identify it as a
dependency instead of presenting it as confirmed.

## 16. QA checklist

### Visual QA

-   [ ] Consistent typography, spacing, colors, icons, and component
    styles.
-   [ ] No clipped text, overlapping controls, or unintended overflow.
-   [ ] Primary actions are clear.
-   [ ] Status remains understandable without color alone.
-   [ ] Small-screen layout, keyboard, and safe areas have been checked.

### Interaction QA

-   [ ] Main citizen journey is clickable end to end.
-   [ ] Main field-team journey is clickable end to end.
-   [ ] Back/cancel navigation is consistent.
-   [ ] Relevant validation, loading, empty, failure, and success states
    are covered.
-   [ ] Duplicate submission and stale-task scenarios have defined UX.
-   [ ] No dead ends remain in the main prototype paths.

### Handoff QA

-   [ ] Prototype link is accessible to the Team Leader.
-   [ ] PNGs match the final Figma frames.
-   [ ] Every referenced PNG exists in the repository.
-   [ ] No placeholder paths or pending statuses remain.
-   [ ] UI labels match approved lifecycle terminology.
-   [ ] Open product/backend decisions are explicitly listed.

## 17. Acceptance criteria

The task is ready for review when:

1.  This document is committed at
    `docs/design/ui-ux/citizen-and-field-screens.md`.
2.  The Figma prototype link is included and accessible.
3.  The prototype covers the approved citizen reporting journey.
4.  The prototype covers the approved cleaning-team task journey.
5.  Main interactions and relevant UI states are represented and
    navigable.
6.  Both roles use a consistent shared design system.
7.  Lifecycle labels and available actions match approved CleanOps
    workflow rules.
8.  High-resolution PNG mockups are exported from final Figma frames and
    committed.
9.  The asset index contains real paths and no unresolved placeholders.
10. Confirmed behavior is distinguished from proposed recommendations.
11. Visual, interaction, accessibility, and handoff QA are complete.

## 18. Dependencies and assumptions to verify

Confirm the following against the existing CleanOps requirements and
Figma file before final approval:

-   Exact frames currently implemented in Figma.
-   Canonical report/task status labels and allowed transitions.
-   Whether citizens can edit or withdraw reports.
-   Whether manual location selection is supported if GPS permission is
    denied.
-   Supported evidence types and upload constraints.
-   Whether submitted evidence must be reviewed before final resolution.
-   Existing design-token values in the Figma design system.

These are confirmation points, not claims that the functionality already
exists.

## 19. Final handoff summary

CleanOps should provide two connected, role-appropriate mobile
experiences:

-   **Citizen:** report a waste issue, confirm details/location, receive
    a truthful submission result, and track status.
-   **Cleaning team:** review assigned work, understand the
    issue/location, take the permitted next action, submit completion
    evidence, and receive clear feedback about the resulting state.

The clickable Figma prototype demonstrates the journeys, this document
defines design/handoff expectations, and high-resolution PNG exports
provide reviewable visual artifacts. All three should be consistent
before the task is considered complete.
