# CleanStreet AI
## Core Entities Schema — Users & Categories

**Work Package:** Analytics Requirements  
**Task:** Core Entities Schema — Users & Categories  
**Project:** CleanStreet AI — Smart Citizen-Requested Street Cleaning and Waste Management Platform

---

## 1. Purpose

This document defines the field-level database requirements for the `USERS` and `CATEGORIES` tables.

The CleanStreet AI proposal identifies `USERS` as registered users who submit reports, `CATEGORIES` as fixed waste/issue types, and `REPORTS` as the central table referencing both entities.

---

## 2. USERS Table

### 2.1 Purpose

The `USERS` table stores registered system users who submit reports or operate the cleaning-service workflow.

The proposal identifies `id`, `name`, `email`, and `role` as the key columns.

### 2.2 Field-Level Requirements

| Column | Data Type | Constraints | Purpose |
|---|---|---|---|
| `id` | `BIGSERIAL` / `BIGINT` | Primary Key, NOT NULL | Unique identifier for each user. |
| `name` | `VARCHAR(100)` | NOT NULL | User's display/full name. |
| `email` | `VARCHAR(255)` | NOT NULL, UNIQUE | Login/contact email; prevents duplicate accounts. |
| `role` | `VARCHAR(30)` | NOT NULL; restricted to supported roles | Identifies the authorization role, such as `citizen` or `operator`. |
| `password_hash` | `VARCHAR(255)` | NOT NULL | Stores a secure password hash, never a plaintext password. |
| `created_at` | `TIMESTAMPTZ` | NOT NULL; default current timestamp | Records account creation time. |

### 2.3 USERS Constraints and Rules

1. `id` shall uniquely identify every user.
2. `email` shall be unique and NOT NULL.
3. Passwords shall never be stored as plaintext.
4. `role` shall be restricted to roles supported by the implemented authorization model.
5. At minimum, the initial workflow shall support:
   - `citizen` — submits and tracks waste reports.
   - `operator` — reviews reports, assigns work, updates status, and records completion.
6. `created_at` shall be generated automatically when the account is created.

---

## 3. CATEGORIES Table

### 3.1 Purpose

The `CATEGORIES` table stores the fixed waste/issue categories used to classify reports.

The proposal identifies `id` and `name` as the key columns and describes categories such as plastic, paper, glass, metal, and other waste.

### 3.2 Field-Level Requirements

| Column | Data Type | Constraints | Purpose |
|---|---|---|---|
| `id` | `SERIAL` / `INTEGER` | Primary Key, NOT NULL | Unique identifier for each category. |
| `name` | `VARCHAR(50)` | NOT NULL, UNIQUE | Category name used when classifying reports. |
| `description` | `VARCHAR(255)` | NULL allowed | Optional explanation of the category. |
| `is_active` | `BOOLEAN` | NOT NULL; default TRUE | Indicates whether the category is available for new reports. |

### 3.3 Initial Fixed Category List

The initial category set shall be controlled rather than allowing arbitrary category names.

| Category | Meaning |
|---|---|
| `plastic` | Plastic waste or plastic litter. |
| `paper` | Paper or cardboard-type waste. |
| `glass` | Glass waste. |
| `metal` | Metal waste. |
| `other` | Waste that does not fit the primary supported categories. |

The final category list may be refined during requirements/design based on the selected datasets and implemented classification model.

---

## 4. Relationship to REPORTS

`REPORTS` is the central report entity. Each report references:

- `user_id` → `USERS.id`
- `category_id` → `CATEGORIES.id`

| Relationship | Cardinality | Description |
|---|---|---|
| `USERS` → `REPORTS` | One-to-Many | One user can submit multiple reports; each report belongs to one submitting user. |
| `CATEGORIES` → `REPORTS` | One-to-Many | One category can be assigned to multiple reports; each report references one category. |

### 4.1 Foreign Keys

```text
REPORTS.user_id
    REFERENCES USERS(id)

REPORTS.category_id
    REFERENCES CATEGORIES(id)
```

Foreign keys shall prevent reports from referencing non-existent users or categories.

For historical report integrity, referenced users/categories should not be physically deleted; deactivation should be preferred where appropriate.

---

## 5. Analytics and Reporting Use

### USERS

User data supports:

- associating reports with their submitters;
- authentication and authorization;
- role-based citizen/operator access;
- tracking report activity by user where required.

### CATEGORIES

Category data supports:

- grouping reports by waste/issue type;
- category-based filtering in the operations dashboard;
- category-level counts and trends;
- supporting AI-assisted waste classification;
- analysing the distribution of reported waste types.

---

## 6. Indexing Requirements

| Table | Index | Purpose |
|---|---|---|
| `USERS` | Unique index on `email` | Fast login lookup and unique-email enforcement. |
| `USERS` | Index on `role` | Supports role-based filtering where required. |
| `CATEGORIES` | Unique index on `name` | Prevents duplicate category names and supports lookup. |
| `REPORTS` | Index on `user_id` | Supports retrieving reports submitted by a user. |
| `REPORTS` | Index on `category_id` | Supports category filtering and analytics. |

---

## 7. Data Integrity Rules

1. Primary keys shall be unique and non-null.
2. Required fields shall not accept NULL values.
3. User email addresses shall be unique.
4. Category names shall be unique.
5. Reports shall reference valid existing users and categories.
6. The category list shall be controlled by the system.
7. User roles shall be controlled by the authorization model.
8. User passwords shall be stored only as secure hashes.
9. Category deactivation shall be preferred over deleting categories already referenced by historical reports.

---

## 8. Traceability to the Project Proposal

| Schema Requirement | Proposal Basis |
|---|---|
| `USERS` entity | Section 15.2 identifies `USERS` as registered citizens who submit reports, with key columns `id`, `name`, `email`, and `role`. |
| `CATEGORIES` entity | Section 15.2 identifies `CATEGORIES` as fixed waste/issue types, with key columns `id` and `name`. |
| User-report relationship | Section 15.2 identifies `REPORTS.user_id` as a foreign key to `USERS`. |
| Category-report relationship | Section 15.2 identifies `REPORTS.category_id` as a foreign key to `CATEGORIES`. |
| Authentication and authorization | The proposal includes registration/login and authentication/authorization in scope. |
| Waste categories | The proposal describes plastic, paper, glass, metal, and other waste categories. |
| Analytics | The proposal includes report density, recurring locations, response times, unresolved requests, and cleaning trends. |
| Database technology | Section 14 specifies PostgreSQL with PostGIS for structured and spatially queryable data. |

---

## 9. Acceptance Notes

- The `USERS` and `CATEGORIES` tables are defined at field level with column names, data types, constraints, and purposes.
- Their relationships to `REPORTS` are explicitly defined through foreign keys.
- The initial category list is controlled and based on categories described in the proposal.
- Exact PostgreSQL identity/sequence syntax may be finalized during implementation.
- Any additional roles or categories introduced later shall be documented in the requirements/design update.
