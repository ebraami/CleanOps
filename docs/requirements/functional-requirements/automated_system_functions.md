# **Automated System Functions** 

This section defines the functionality that the CleanStreet AI backend performs automatically, without any manual action by a citizen or an operator. Each function is described by what starts it, what it takes as input, what it does, what it produces, how it behaves when it fails, and the condition under which it is considered correctly implemented. 

## **Execution Model** 

The automated functions are not all executed at the same moment. They are divided into three execution modes, because a citizen submitting a report should not wait for image analysis, scoring, and duplicate checking to finish before receiving a confirmation. 

|**Mode**|**Meaning**||**Functions**|
|---|---|---|---|
|Immediate|Executed inside the<br>submission request;<br>the citizen waits for<br>the result|F-01,<br>(initia|F-02, F-07<br>l entry)|
|Background<br>Scheduled|Executed after the<br>report has been<br>successfully saved<br>Executed<br>periodically,<br>independently of any<br>single report|F-03,<br>F-08|F-04, F-05, F-06|



The separation matters for two reasons. First, response time: submission stays fast because only saving is done immediately. Second, reliability: if the AI service is unavailable, the report is still saved and remains visible to operators, rather than the whole submission failing. 

## **F-01 — Saving Reports** 

**Trigger:** A citizen submits a new report from the mobile application. 

**Inputs:** User identifier, category, latitude and longitude, optional description, and one image. 

**Processing:** The system validates that the required fields are present and that the coordinates are within a valid range. It then creates a new record in the REPORTS table with the initial status SUBMITTED and an empty priority score. Saving the report and its image record is performed as a single database transaction, so a report is never stored without its image reference. 

**Output:** A saved report with a generated report_id, returned to the mobile application. 

**Failure handling:** If validation fails, the report is rejected with a clear message identifying the invalid field. If the database operation fails at any point, the entire transaction is rolled back and no partial record remains. 

**Acceptance condition:** A valid submission always produces exactly one report record with status SUBMITTED and a returned report_id. An invalid submission produces no record at all, and no report ever exists in the database without a corresponding image record. 

## **F-02 — Storing Images** 

**Trigger:** An image is received as part of report submission (citizen evidence) or as part of task completion (cleaning team evidence). 

**Inputs:** The image file, the related report_id, and the image type (BEFORE or AFTER). 

**Processing:** The system checks the file type and size against defined limits, uploads the file to Object Storage, and then writes a record in the IMAGES table containing the returned storage URL, the image type, and the upload timestamp. The image file itself is never stored inside the database; only its link is stored. 

**Output:** An IMAGES record linked to the report, containing a valid storage_url. 

**Failure handling:** If the file type or size is not accepted, the upload is rejected before any storage operation occurs. If the upload to Object Storage fails, no IMAGES record is created, so the database never points to a file that does not exist. 

**Acceptance condition:** Every storage_url stored in the IMAGES table resolves to a file that actually exists in Object Storage, and a single report can hold both a BEFORE and an AFTER image without conflict. 

## **F-03 — Triggering AI Analysis** 

**Trigger:** Successful completion of F-01. The analysis starts only after the report has been committed to the database. 

**Inputs:** The report_id and the storage_url of the citizen’s image. 

**Processing:** The system sets the report’s ai_status to PROCESSING and sends the image reference to the AI service. The service returns the detected waste objects with their material categories and confidence values. The result is written back into the report record, and ai_status is set to COMPLETED. 

**Output:** Detection and classification results stored on the report, and an updated ai_status. 

**Failure handling:** If the AI service does not respond or returns an error, the system retries a limited number of times with an increasing delay. If all attempts fail, ai_status is set to FAILED. The report remains fully visible to operators and is handled manually, rather than being hidden or lost. 

**Acceptance condition:** Every report reaches a final ai_status of either COMPLETED or FAILED within a defined time limit, and no report remains in PROCESSING indefinitely. Unavailability of the AI service never prevents a report from being saved or displayed. 

## **F-04 — Calculating Severity and Priority** 

**Trigger:** Successful completion of F-03 for a given report. 

**Inputs:** For severity — the detected waste objects and their material categories. For priority — the calculated severity, the report age, the number of repeated reports at the same location, and the density of reports in the surrounding area. 

**Processing:** Severity is calculated as a weighted sum over the detected objects, where each material category carries a configurable weight stored in a database table rather than written into the code. Priority is then calculated by normalising each contributing factor to a common scale and combining them using configurable weights, so that no single factor dominates simply because it has a larger numeric range. Both values are calculated by a transparent formula, not by a trained model, because no available dataset provides ground-truth severity labels. 

**Output:** A severity_score and a priority_score stored on the report record. 

**Failure handling:** If AI analysis failed and no detections are available, the report receives a defined default priority and is marked as requiring manual assessment, so that it still appears in the operator’s queue. 

**Acceptance condition:** The same inputs always produce the same scores, the weight values can be changed without modifying application code, and every report displayed in the operator dashboard carries a priority score. For any given report, the individual factor values that produced the score can be retrieved, so an operator can see why a report was ranked as it was. 

## **F-05 — Detecting Duplicate Reports** 

**Trigger:** Successful completion of F-03 for a newly submitted report. 

**Inputs:** The new report’s coordinates, submission time, and image feature representation. 

**Processing:** The system first performs a spatial and temporal query to retrieve only reports located within a defined distance and submitted within a defined time window. Only this reduced set of candidates is then compared by image similarity. This two-stage approach avoids comparing each new report against the entire historical record. Any candidate exceeding the similarity threshold is stored as a suggested link between the two reports. 

**Output:** Zero or more suggested duplicate links, each marked with status SUGGESTED. 

**Failure handling:** If the comparison cannot be completed, the report is processed as a normal independent report. No link is created. 

**Acceptance condition:** Duplicate reports are never merged or closed automatically. Each suggestion is presented to the operator, who confirms or rejects it, and the final decision is recorded. Identical reports submitted at the same location within the defined window are reliably surfaced as suggestions. 

## **F-06 — Sending Notifications** 

**Trigger:** A report’s status changes, a report is assigned to a cleaning team, or completion evidence is uploaded. 

**Inputs:** The report_id, the new status, and the identifier of the recipient. 

**Processing:** The system builds a message appropriate to the event and sends it through the push notification service to the relevant recipient — the reporting citizen for status changes, or the assigned team for new assignments. 

**Output:** A delivered notification and a stored record of the send attempt and its outcome. 

**Failure handling:** Notification failure is logged but never affects the status change itself. The status update remains valid and visible in the application even if the notification was not delivered. 

**Acceptance condition:** Every status change visible to a citizen generates exactly one notification attempt, no duplicate notifications are sent for a single event, and a failed notification does not roll back or block the underlying status change. 

## **F-07 — Maintaining Status History** 

**Trigger:** Any change to a report’s status, including the initial status assigned at creation. 

**Inputs:** The report_id, the new status, the identifier of the actor responsible for the change, and the timestamp. 

**Processing:** The system validates that the requested transition is permitted according to the defined status flow, then writes a new record into the STATUS_HISTORY table and updates the current_status field on the report. Both operations occur within a single transaction. All status changes pass through a single point in the system, so that no status can be modified without being recorded. 

**Output:** A new STATUS_HISTORY record and an updated current_status on the report. 

**Failure handling:** A transition that is not permitted by the defined flow is rejected and the current status remains unchanged. If writing the history record fails, the status update is rolled back with it. 

**Acceptance condition:** Every status a report has ever held appears in STATUS_HISTORY with its timestamp, the current_status field always matches the most recent history record, and there is no execution path that changes a status without creating a history entry. 

## **F-08 — Updating Analytics** 

**Trigger:** A scheduled job executed at a defined interval, independently of individual reports. 

**Inputs:** The REPORTS, STATUS_HISTORY, and ASSIGNMENTS tables. 

**Processing:** The system recalculates the aggregated operational indicators: report counts by area and category, spatial clustering to identify recurring hotspot locations, area burden scores, resolution rates, average resolution times, current open workload per cleaning team, and flags for reports that have remained unresolved beyond the 

threshold defined for their priority tier. Results are stored in summary form so that the dashboard reads pre-calculated values rather than recomputing them on every request. 

**Output:** Updated analytics records serving the operations dashboard. 

**Failure handling:** If a run fails, the previously stored results remain available and are displayed with their last-updated timestamp, so the dashboard degrades to slightly outdated data rather than to no data. 

**Acceptance condition:** Analytics values are consistent with the underlying report data at the time of the last successful run, the dashboard displays when the figures were last updated, and dashboard response time does not increase as the total number of stored reports grows. 

## **Summary** 

|**ID**|**Function**|**Mode**|**Primary output**|
|---|---|---|---|
|F-01|Saving reports|Immediate|Report record<br>withreport_id|
|F-02|Storing images|Immediate|IMAGES record<br>withstorage_url|
|F-03|Triggering AI<br>analysis|Background|Detection results<br>andai_status|
|F-04|Calculating<br>severity and<br>priority|Background|severity_score,<br>priority_score|
|F-05|Detecting<br>duplicate<br>reports|Background|Suggested<br>duplicate links|
|F-06|Sending<br>notifications|Background|Delivered<br>notification|
|F-07|Maintaining<br>status history|Immediate|STATUS_HISTORY<br>record|
|F-08|Updating<br>analytics|Scheduled|Aggregated<br>dashboard<br>indicators|



Across all eight functions, one principle is applied consistently: automation prepares information and never makes a final operational decision. Reports are scored but not closed automatically, duplicates are suggested but not merged automatically, and analytics are calculated for operator review. The responsible human operator remains the decision point throughout. 

