**Required Indexes**

**1\. Spatial Index for Location-Based Queries**

**Index**

SQL

CREATE SPATIAL INDEX idx\_incidents\_location

ON incidents (location);

Show more lines

If latitude and longitude are stored separately, create a geometry/geography column (location) derived from them and index that column.

**Purpose**

Supports:

- Hotspot detection
- Radius searches
- Map clustering
- Geospatial aggregations

**Example Query**

SQL

SELECT \*

FROM incidents

WHERE ST\_DWithin(

location,

ST\_Point(:lng, :lat),

:radius

);

Show more lines

**Expected Benefit**

- Eliminates full table scans for proximity searches.
- Enables efficient geospatial calculations on large datasets.
- Improves map rendering and hotspot analysis performance.

**2\. Composite Spatial + Time Index (Recommended)**

**Index**

SQL

CREATE INDEX idx\_incidents\_location\_created

ON incidents (created\_at);

Show more lines

Used together with the spatial index.

**Purpose**

Supports hotspot analysis within a specified time window.

**Example Query**

SQL

SELECT \*

FROM incidents

WHERE created\_at >= NOW() - INTERVAL '7 days'

AND ST\_DWithin(

location,

ST\_Point(:lng, :lat),

:radius

);

Show more lines

**Expected Benefit**

- Reduces scanned records before spatial calculations.
- Improves performance of recent hotspot dashboards.

**3\. Index on current\_status**

**Index**

SQL

CREATE INDEX idx\_incidents\_current\_status

ON incidents(current\_status);

Show more lines

**Purpose**

Supports dashboard filtering by status.

**Example Query**

SQL

SELECT \*

FROM incidents

WHERE current\_status = 'OPEN';

Show more lines

**Expected Benefit**

- Fast filtering and aggregation by status.
- Improved dashboard response time.

**4\. Index on created\_at**

**Index**

SQL

CREATE INDEX idx\_incidents\_created\_at

ON incidents(created\_at);

Show more lines

**Purpose**

Supports:

- Date range filtering
- Dashboard analytics
- Trend charts
- Periodic reporting

**Example Query**

SQL

SELECT \*

FROM incidents

WHERE created\_at BETWEEN :start\_date AND :end\_date;

Show more lines

**Expected Benefit**

- Efficient time-based filtering.
- Faster reporting queries.

**5\. Composite Index for Dashboard Filters (Recommended)**

**Index**

SQL

CREATE INDEX idx\_incidents\_status\_created

ON incidents(current\_status, created\_at);

Show more lines

**Purpose**

Supports common dashboard scenarios where users filter by both status and date range.

**Example Query**

SQL

SELECT \*

FROM incidents

WHERE current\_status = 'OPEN'

AND created\_at BETWEEN :start\_date AND :end\_date;

Show more lines

**Expected Benefit**

- Avoids multiple index lookups.
- Improves dashboard performance significantly.

**6\. Duplicate Detection Support**

**Index**

If duplicate detection relies on matching location and time proximity:

SQL

CREATE INDEX idx\_incidents\_duplicate\_check

ON incidents(created\_at);

Show more lines

Combined with the spatial index.

**Example Query**

SQL

SELECT \*

FROM incidents

WHERE ST\_DWithin(

location,

:target\_location,

50

)

AND ABS(

EXTRACT(EPOCH FROM (

created\_at - :target\_time

))

) < 3600;

Show more lines

**Expected Benefit**

- Fast identification of potentially duplicated incidents.
- Reduced computational cost during duplicate validation.

**Final Recommendation**

| **Index Name** | **Columns** | **Use Case** |
| --- | --- | --- |
| idx\_incidents\_location | location (Spatial) | Hotspot Detection, Radius Search |
| idx\_incidents\_current\_status | current\_status | Dashboard Filters |
| idx\_incidents\_created\_at | created\_at | Date Filtering & Reporting |
| idx\_incidents\_status\_created | current\_status, created\_at | Dashboard Filters + Analytics |
| Spatial + created\_at combination | location + created\_at | Time-based Hotspot Analysis |
| Spatial + created\_at combination | location + created\_at | Duplicate Detection |

**Conclusion**

The minimum required indexes are:

- **Spatial Index on location (lat/lng)**
- **Index on current\_status**
- **Index on created\_at**

Additionally, implementing the **composite index (current\_status, created\_at)** is strongly recommended to optimize dashboard filtering workloads, while the combination of **spatial and temporal indexing** provides efficient support for hotspot and duplicate detection use cases.
