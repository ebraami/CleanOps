Indexing & Spatial Query Requirements

Objective: Define required database indexes for hotspot detection, duplicate/related report detection, and dashboard filtering & analytics.

| Index Name | Table | Column(s) | Index Type | Supported Use Case |
| --- | --- | --- | --- | --- |
| idx\_incidents\_location | incidents | location | GiST Spatial | Hotspot Detection, Duplicate Candidate Search |
| idx\_incidents\_created\_at | incidents | created\_at | B-Tree | Date Filtering, Reporting |
| idx\_incidents\_current\_status | incidents | current\_status | B-Tree | Dashboard Status Filtering |
| idx\_incidents\_status\_created | incidents | current\_status, created\_at | Composite B-Tree | Dashboard Filtering & Analytics |
