# Scalability Requirements

**Project:** CleanOps\
**Phase:** P01 --- Project Foundation & Requirements\
**Work Package:** Non-Functional Requirements\
**Requirement Area:** Scalability\
**Status:** Draft

------------------------------------------------------------------------

## 1. Purpose

This document defines the scalability targets for the CleanOps
MVP/pilot.

The purpose is to establish a realistic baseline for the first working
version of the system and provide clear targets that can later be
validated through performance and load testing.

These figures are planning targets for the graduation-project MVP, not
claims about the capacity of a future city-wide production deployment.

------------------------------------------------------------------------

## 2. MVP / Pilot Capacity Targets

  Area                                                Target
  ------------------------------ ---------------------------
  Registered citizens                          Up to **500**
  Registered operational users                  Up to **25**
  Total registered users                       Up to **525**
  Concurrent citizens                           Up to **50**
  Concurrent operational users                  Up to **15**
  Total concurrent users                        Up to **65**
  Reports submitted per day                    Up to **300**
  Peak report submissions          Up to **30 reports/hour**
  Report images                     Up to **300 images/day**

These figures are initial assumptions for the pilot. They should be
reviewed if real pilot data becomes available.

------------------------------------------------------------------------

## 3. Concurrent User Requirements

### 3.1 Citizens

CleanOps should support up to **50 citizens using the system
concurrently**.

Concurrent activity may include:

-   Opening the reporting interface
-   Creating and submitting reports
-   Uploading images
-   Viewing report details
-   Checking report status
-   Viewing updates

### 3.2 Operational Users

CleanOps should support up to **15 operational users concurrently**.

Operational activity may include:

-   Reviewing incoming reports
-   Viewing AI analysis results
-   Managing priorities
-   Assigning cases
-   Updating case status
-   Reviewing completion evidence
-   Monitoring operational information

### 3.3 Combined Usage

The initial target is therefore **65 concurrent users** across citizen
and operational functions.

The system should continue to provide its core functions at this level
of concurrent usage.

------------------------------------------------------------------------

## 4. Report Volume Requirements

The MVP should be designed around a target of up to **300 submitted
reports per day**.

A report may contain:

-   Category
-   Description
-   Location
-   Timestamp
-   Image or other supporting evidence

### Peak Activity

The system should be planned for short periods of increased activity of
approximately **30 report submissions per hour**.

The peak figure is higher than the daily average because user activity
is not expected to be evenly distributed throughout the day.

------------------------------------------------------------------------

## 5. Image Upload Requirements

Because reports may include photographic evidence, image handling must
be considered as part of scalability.

The MVP should support approximately **300 report images per day** under
the pilot target.

The system should be designed so that:

-   Image processing does not unnecessarily block report submission.
-   Image storage can grow independently from normal application data.
-   Image access does not unnecessarily degrade core application
    operations.
-   AI processing can be separated from the immediate reporting flow
    where appropriate.

------------------------------------------------------------------------

## 6. Growth Requirement

The MVP should not depend on fixed limits that make future growth
impractical.

The architecture should allow capacity to be increased as the number of
users and reports grows, without requiring a complete redesign of the
system.

As an initial future-growth assumption, the architecture should be
capable of accommodating approximately **3× the pilot report volume** in
a later iteration:

-   Approximately **900 reports/day**
-   Approximately **90 reports/hour during peak periods**

These are future planning targets and do not need to be fully
demonstrated by the MVP.

------------------------------------------------------------------------

## 7. Scalability Considerations

The system design should consider scalability across the following
areas:

### Application Services

Application capacity should be extendable as concurrent usage increases.

### Database

The database should support continued growth of users, reports,
assignments, status history, and other operational records without
unnecessary structural limitations.

### Image Storage

Uploaded evidence should be stored in a way that allows storage capacity
to grow independently from the main application data.

### AI Processing

Increasing report volume should not prevent users from submitting and
managing reports. AI processing should be separated from time-sensitive
user actions where appropriate.

### Analytics

Historical data should be able to grow while remaining usable for
dashboards, reports, and operational analysis.

### Background Processing

Operations that do not need to block a user's request should be suitable
for asynchronous processing where appropriate.

------------------------------------------------------------------------

## 8. Assumptions and Rationale

The targets in this document are **project assumptions**, not measured
production limits.

They are intentionally sized for a controlled graduation-project pilot
rather than a full municipal deployment.

The assumptions are:

-   The first evaluation will involve a relatively small citizen
    population.
-   Only a limited number of operational users will work with cases at
    the same time.
-   Report submissions will be unevenly distributed throughout the day.
-   Many reports may contain images.
-   AI analysis may require more processing than ordinary report
    creation or viewing.
-   Historical reports will accumulate and remain relevant for
    analytics.
-   Future versions may serve more users, so the architecture should
    avoid unnecessary hard limits.

These assumptions should be revisited if the project obtains real usage
or performance data.

------------------------------------------------------------------------

## 9. Requirement Summary

For the MVP/pilot, CleanOps shall be planned to support:

-   **65 concurrent users**
-   **50 concurrent citizens**
-   **15 concurrent operational users**
-   **300 reports per day**
-   **30 report submissions per hour during peak periods**
-   **300 report images per day**
-   A future growth path toward approximately **900 reports per day**

These targets should be considered when making architecture decisions
and should later be validated through performance/load testing.

------------------------------------------------------------------------
