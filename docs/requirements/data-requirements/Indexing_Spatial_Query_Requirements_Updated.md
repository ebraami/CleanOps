Indexing & Spatial Query Requirements

**Work Package: Data Requirements
**Status: Updated per Team Lead Feedback
Data Model: REPORTS

# Objective

Define the required database indexes needed to support Hotspot Detection, Duplicate / Related Report Detection, and Dashboard Filtering & Analytics.

# Index Summary

idx\_reports\_location (GiST Spatial), idx\_reports\_created\_at (B-Tree), idx\_reports\_current\_status (B-Tree), idx\_reports\_status\_created (Composite B-Tree).

# Spatial Location Index

Table: reports. Column: location. Index Type: GiST Spatial Index. Supported Query: SELECT \* FROM reports WHERE ST\_DWithin(location, :target\_location, 500); Supported Use Cases: Hotspot Detection, Nearby Report Search, Duplicate Candidate Search.

# Created Date Index

Table: reports. Column: created\_at. Index Type: B-Tree. Supported Query: SELECT \* FROM reports WHERE created\_at BETWEEN :start\_date AND :end\_date; or recent-report filtering using created\_at >= NOW() - INTERVAL 24 HOURS. Supported Use Cases: Date Filtering, Reporting, Duplicate Time Filtering.

# Current Status Index

Table: reports. Column: current\_status. Index Type: B-Tree. Supported Query: SELECT \* FROM reports WHERE current\_status = OPEN. Supported Use Cases: Status Filtering, Dashboard Monitoring, Reporting.

# Composite Status-Date Index

Table: reports. Columns: current\_status, created\_at. Index Type: Composite B-Tree. Supported Query: SELECT \* FROM reports WHERE current\_status = OPEN AND created\_at BETWEEN :start\_date AND :end\_date. Supported Use Cases: Dashboard Filtering and Analytics.

# Duplicate / Related Report Detection Support

Spatial and temporal indexes are used to retrieve candidate reports before embedding similarity comparison. Matches are surfaced as recommendations only and are never automatically merged.

# Recommendation

Required indexes: idx\_reports\_location, idx\_reports\_created\_at, idx\_reports\_current\_status. Recommended additional index: idx\_reports\_status\_created.

# Conclusion

The indexing strategy supports hotspot detection, nearby-report searches, duplicate candidate retrieval, dashboard filtering, reporting, and analytics while remaining aligned with the CleanOps REPORTS data model.
