# API Protection and Rate Limiting Requirements

### CleanStreet AI — Security Requirements

**Scope:** Define security requirements protecting the CleanStreet AI API layer through request verification, service-role key isolation, signed-token validation, authentication and authorization, endpoint rate limiting, secret/API-key lifecycle management, payload and file validation, SQL injection prevention, XSS protection, secure error handling, HTTPS/TLS, and security logging.

**Dependencies:**

- `T_85ab37 — Authentication & RBAC Specification`
- `ADR-007 — Service-Role Key Isolation`

---

## 0. Dependency and Assumption Notice

This specification depends on two architecture/security artifacts:

- **`T_85ab37 — Authentication & RBAC Specification`** — defines authentication, user identity, roles, token/session issuance, and role-based authorization.
- **`ADR-007 — Service-Role Key Isolation`** — defines the authoritative architecture for privileged service credentials.

Where either document is unavailable or has not yet been finalized, this specification uses proposed implementation defaults.

Any technical choice concerning token format, token claims, role names, service credentials, secret-management technology, or exact security thresholds is therefore a **proposed implementation requirement** until reconciled with the authoritative dependency.

The proposal establishes the general security principles of authentication, RBAC, secure API communication, secure image storage, access control, protection of location/account information, audit logging, and data minimization/retention. It does not define exact API rate limits, token-validation mechanisms, service-role-key handling, secret rotation intervals, or detailed input-validation rules.

Therefore, all such detailed mechanisms and numerical thresholds in this document are explicitly treated as **proposed implementation requirements**.

---

# 1. Purpose and Security Objectives

The purpose of this specification is to establish a security boundary around the CleanStreet AI API and prevent unauthorized access, credential abuse, data manipulation, and malicious or malformed input.

The API security layer shall protect against:

1. Unauthenticated API access.
2. Invalid, malformed, expired, or incorrectly issued authentication tokens.
3. Privilege escalation and role misuse.
4. Unauthorized access to another citizen's reports or private information.
5. Exposure or misuse of service-role credentials.
6. Brute-force authentication attempts.
7. Request flooding and API abuse.
8. Accidental overload caused by malfunctioning clients.
9. Malformed or oversized payloads.
10. Excessive image/file uploads.
11. SQL injection.
12. Cross-site scripting (XSS).
13. Information leakage through API errors.
14. Unauthorized manipulation of report status or operational data.
15. Exposure of sensitive credentials, location data, account data, and uploaded images.

Security controls shall protect the system without unnecessarily preventing legitimate citizen reporting or authorized operator workflows.

---

# 2. Source and Implementation Boundary

The CleanStreet AI proposal establishes the following security principles:

- Authentication is required for protected functionality.
- Citizens and operators have different permissions.
- API communication must be secure.
- User/account and location information requires protection.
- Uploaded images require secure storage and access control.
- Important report status changes require audit logging.
- Data minimization and retention principles apply to sensitive information.

The proposal does **not** explicitly define:

- Exact rate-limit thresholds.
- Exact token claims.
- Exact token-validation implementation.
- Service-role credential architecture.
- Secret-management technology.
- API-key rotation periods.
- Exact payload size/type limits.
- Exact SQL injection implementation.
- Exact XSS implementation.

Accordingly, this specification separates **proposal-derived requirements** from **proposed implementation controls**.

---

# 3. Dependency — Authentication and RBAC

`T_85ab37 — Authentication & RBAC Specification` is the authoritative source for:

- User authentication.
- User identity.
- User roles.
- Session/token issuance.
- Authentication lifecycle.
- Role-based authorization.
- Permission definitions.

This document defines how authenticated credentials are verified and protected at the API layer.

## 3.1 Expected Roles

The current project model identifies at minimum:

- **Citizen**
- **Operator**

Any additional administrative or service roles introduced by `T_85ab37` shall follow the principle of least privilege.

The API must not assume that a user is authorized simply because the Flutter interface exposes a particular action.

---

# 4. API Request Verification

Every protected API request shall pass the appropriate security checks before the protected business operation is executed.

## 4.1 Request Verification Flow

```
Client Request
      |
      v
HTTPS / Transport Validation
      |
      v
Rate Limit Check
      |
      v
Token Extraction
      |
      v
Signature Verification
      |
      v
Token Expiration / Claim Validation
      |
      v
Role / Permission Check
      |
      v
Resource Authorization
      |
      v
Payload / File Validation
      |
      v
Sanitization / Safe Query Handling
      |
      v
Business Operation
      |
      v
Audit Logging where required
      |
      v
Response
```

A request failing an earlier security stage shall not proceed to the protected business operation.

Rate limiting should be implemented at the gateway or middleware layer where possible so rejected requests do not unnecessarily reach business logic, the database, or the AI service.

---

# 5. Signed Token Validation

For protected endpoints, the API shall validate the authentication credential before processing the request.

Where `T_85ab37` specifies signed JWT/Firebase-style tokens, validation shall include:

- Token presence.
- Signature validity.
- Token expiration (`exp`).
- Issuer (`iss`), where applicable.
- Audience (`aud`), where applicable.
- Subject/user identifier (`sub`), where applicable.
- Expected token type.
- Required role/permission claims.
- Token integrity and structure.

The client shall transmit the token through the standard authorization mechanism:

```
Authorization: Bearer <token>
```

The token should not be supplied through URLs or query parameters because URLs may be exposed through logs, browser history, analytics, or intermediary systems.

## 5.1 Failure Handling

The API shall distinguish authentication failures from authorization failures:

- **401 Unauthorized** — missing, malformed, invalid, expired, revoked, or otherwise unacceptable authentication credentials.
- **403 Forbidden** — authenticated user lacks permission to perform the requested action.

These conditions shall not be conflated.

## 5.2 Token Revocation

Where the authentication architecture supports token revocation, revoked credentials must no longer authorize protected operations even if their signature and expiration remain technically valid.

Logout, password-reset, account-security events, and other revocation mechanisms shall follow `T_85ab37`.

## 5.3 Dependency Rule

If `T_85ab37` defines an opaque session-token mechanism instead of signed JWT-style tokens, this section shall be adapted to that mechanism. The authoritative authentication specification takes precedence.

---

# 6. Authorization and Role Isolation

Authentication establishes **who** is making a request.

Authorization establishes **whether that user may perform the requested operation**.

Authorization shall be enforced independently from authentication.

## 6.1 Citizen Authorization

A citizen may access operations associated with their own account and authorized resources, including where supported:

- Creating a report.
- Viewing their own report.
- Viewing report history.
- Tracking report status.
- Confirming resolution.

A citizen must not access another citizen's private report by modifying an identifier in:

- URL parameters.
- Request body.
- Query parameters.
- Client-side state.

The backend shall verify ownership or explicit authorization server-side.

## 6.2 Operator Authorization

An operator may perform operational functions defined by the RBAC specification, including:

- Reviewing incoming reports.
- Viewing operational report information.
- Reviewing AI analysis and priority.
- Assigning reports where authorized.
- Updating report status.
- Reviewing completion evidence.
- Resolving or taking further action on reports where permitted.

## 6.3 Server-Side Enforcement

Hiding a button or screen in Flutter is not an authorization mechanism.

The API must independently reject unauthorized requests.

---

# 7. Role Re-Verification for Sensitive Operations

For high-impact operations, the backend should not rely solely on a potentially stale role claim contained in an access token.

For sensitive actions such as:

- Assigning a report.
- Changing report status.
- Marking a report resolved.
- Managing operational assignments.
- Accessing privileged operational information.

The backend should re-check the user's current authorization against the authoritative user/role source defined by `T_85ab37`, such as the `USERS.role` field.

This prevents a previously issued token from continuing to grant elevated privileges after the user's role has been changed.

---

# 8. Service-Role Key Isolation — ADR-007

A service-role key is a privileged credential capable of performing operations beyond ordinary user permissions.

The exact implementation shall follow `ADR-007`.

## 8.1 Client Applications

The Flutter application must never contain or expose a service-role credential.

Service-role credentials must not be:

- Hard-coded in Dart source code.
- Stored in Flutter public configuration.
- Included in mobile assets.
- Returned through API responses.
- Embedded in URLs.
- Exposed through client logs.
- Committed to Git repositories.
- Included in build artifacts.

## 8.2 Backend Isolation

Privileged credentials shall exist only within trusted server-side components that require them.

```
Flutter Client
      |
      | Authenticated HTTPS Request
      v
Public Backend/API
      |
      | Controlled server-side access
      v
Trusted Worker / Service
      |
      | Privileged Credential
      v
Database / Storage / Trusted Service
```

The client must never communicate directly using the privileged service-role credential.

## 8.3 Least Privilege

A service-role credential shall be scoped to only the operations it requires.

Examples may include:

- Writing AI analysis results.
- Running trusted aggregation jobs.
- Performing controlled backend maintenance.

The service-role credential shall not be used as a general-purpose credential for ordinary client requests.

## 8.4 Environment Isolation

Where supported, development, staging, and production shall use separate privileged credentials.

A credential valid for one environment must not provide access to another environment.

## 8.5 Logging

Use of privileged credentials should be auditable without recording the credential itself.

The exact implementation is governed by `ADR-007`.

---

# 9. Secret and API-Key Lifecycle Management

This section applies to:

- Service-role credentials.
- Database credentials.
- Firebase credentials.
- Google Maps API keys.
- OpenWeather API keys.
- Token-signing secrets.
- Storage credentials.
- Other privileged application secrets.

## 9.1 Creation

Secrets shall be generated through an approved secure mechanism.

They must not be created as hard-coded constants inside application source code.

## 9.2 Storage

Secrets shall be stored in protected server-side configuration or a dedicated secrets-management mechanism.

They must not be stored in:

- Public repositories.
- Flutter source code.
- Client-side configuration accessible to users.
- Public build artifacts.
- Logs.
- Error messages.
- URLs.

A committed secret must be treated as potentially compromised.

## 9.3 Environment Separation

Development, staging, and production shall use separate credentials wherever practical.

A development credential must not grant production access.

## 9.4 Least Privilege

Each secret shall provide only the permissions required for its intended function.

For example, an external maps API key should not automatically have unnecessary administrative or billing permissions.

## 9.5 Rotation

A proposed initial policy is:

- Rotate long-lived secrets periodically, with **90 days** as an initial calibration target where applicable.
- Rotate immediately after suspected compromise.
- Support replacement without requiring client application modification.
- Where technically supported, allow runtime configuration refresh without a complete application redeployment.

The 90-day value is a **proposed implementation policy**, not a proposal-derived requirement.

## 9.6 Rotation Procedure

A controlled rotation should:

1. Generate a replacement credential.
2. Store the replacement securely.
3. Update backend configuration.
4. Verify the new credential.
5. Revoke or disable the old credential.
6. Confirm that the old credential is no longer accepted.
7. Verify that the client does not contain the old credential.

## 9.7 Revocation

A compromised credential shall be revoked immediately.

Replacing a secret in configuration is insufficient if the old credential remains technically valid at the provider.

---

# 10. Rate Limiting

Rate limiting protects against:

- Brute-force attempts.
- Request flooding.
- Automated abuse.
- Excessive report submission.
- Excessive image uploads.
- Accidental client retry loops.
- Unintentional API overload.

Rate limiting shall be independent of normal authentication and authorization controls.

## 10.1 Rate-Limit Dimensions

Limits may be applied using a combination of:

- Client IP address.
- Authenticated user identity.
- User role.
- Endpoint.
- Endpoint sensitivity.
- Account identifier where appropriate.

For authenticated requests, user-based limits should supplement IP-based limits because many legitimate users may share a single IP address.

---

# 11. Proposed Initial Rate Limits

The following values are proposed starting points for calibration:

| Endpoint / Operation            | Citizen                    | Operator             | Unauthenticated / IP          |
| ------------------------------- | -------------------------- | -------------------- | ----------------------------- |
| Login                           | —                          | —                    | **10 attempts / 15 min / IP** |
| Password Reset Request          | —                          | —                    | **5 requests / hour / IP**    |
| General Authenticated API       | **120 req/min/user**       | **180 req/min/user** | —                             |
| Create Report                   | **10 req/15 min/user**     | N/A                  | —                             |
| Report Image Upload             | **10 uploads/15 min/user** | As required          | —                             |
| View Own Reports                | **60 req/min/user**        | —                    | —                             |
| Operator Report Queries         | —                          | **120 req/min/user** | —                             |
| Status Update                   | —                          | **30 req/min/user**  | —                             |
| General Unauthenticated API     | —                          | —                    | **60 req/min/IP**             |
| Default / Unclassified Endpoint | **Configurable**           | **Configurable**     | **100 req/min/IP**            |

These are **proposed initial calibration values**.

They should be adjusted using:

- Performance testing.
- Expected user behavior.
- Production telemetry.
- AI/storage workload.
- Abuse observations.
- Availability targets.

No rate limit should be treated as a permanently fixed architectural value without operational validation.

---

# 12. Rate-Limit Response

When a configured rate limit is exceeded, the API shall return:

```
HTTP 429 Too Many Requests
```

Where appropriate, the response should include:

```
Retry-After: <seconds>
```

Example response:

```
{
  "error": "rate_limit_exceeded",
  "message": "Too many requests. Please try again later."
}
```

The Flutter application should handle `429` responses gracefully and avoid immediate repeated retries.

## 12.1 Logging

Rate-limit violations should record:

- Endpoint.
- Timestamp.
- Relevant client/user identifier.
- IP or network identifier where appropriate.
- Applied rate-limit category.

Logs must not contain passwords, tokens, secret keys, or complete sensitive request bodies.

---

# 13. Brute-Force Protection

Authentication endpoints shall receive stricter protection than ordinary read endpoints.

The system shall:

- Apply IP-based throttling.
- Apply account/user-based throttling where supported.
- Avoid revealing whether an account exists.
- Avoid returning overly detailed authentication failure reasons.
- Record repeated security-relevant failures where appropriate.

For example, password-reset requests should use a generic response rather than revealing whether an email address belongs to an account.

The exact authentication workflow remains governed by `T_85ab37`.

---

# 14. Payload Validation Standards

All API payloads shall be validated server-side.

Flutter-side validation is useful for user experience but is **not a security boundary**.

Validation shall cover:

- Required fields.
- Data types.
- String lengths.
- Numeric ranges.
- Enumerated values.
- Object structure.
- Array sizes.
- File size.
- File type.
- File content.
- Coordinate ranges.
- Content constraints.
- Unexpected fields.

Invalid payloads shall be rejected before reaching protected database or business operations.

---

# 15. General Payload Validation

Every endpoint shall define an explicit input schema.

The API shall validate:

### Required Fields

Required properties must be present.

### Data Types

Values must match their expected types.

### String Length

Free-text fields must have explicit maximum lengths.

### Numeric Ranges

Values such as coordinates and pagination parameters must remain within valid ranges.

### Enumerated Values

Fields such as report category and status must use controlled values.

### Unexpected Fields

Unexpected fields shall either be explicitly rejected or safely ignored according to the endpoint schema.

They must never be blindly merged into database models.

This prevents mass-assignment-style vulnerabilities.

---

# 16. Report Payload Validation

A report request may contain:

```
category
description
latitude
longitude
image
```

## 16.1 Category

The category must:

- Match an authorized category.
- Correspond to a valid `CATEGORIES` record where applicable.
- Not accept arbitrary database identifiers without authorization.
- Reject unknown categories.

## 16.2 Description

The description:

- May be optional where defined by the reporting workflow.
- Must have a maximum length.
- Must not be interpreted as trusted HTML.
- Should reject or normalize inappropriate control characters.
- Must be rendered safely as text.

## 16.3 Latitude

Valid range:

```
-90 to +90
```

## 16.4 Longitude

Valid range:

```
-180 to +180
```

Values outside these ranges shall be rejected.

---

# 17. Image and File Upload Validation

Images are a core component of the CleanStreet AI reporting workflow and therefore require dedicated security controls.

The API shall validate:

- Authentication.
- Authorization.
- File size.
- Declared MIME type.
- Actual file signature/content type.
- Supported image formats.
- Maximum image dimensions where appropriate.
- Number of uploads.
- Storage destination.
- Generated file identifier/name.

A client-provided filename shall never be treated as a trusted storage path.

Uploaded files should receive server-generated identifiers/names.

The system should also enforce the project's secure image-storage and retention requirements.

---

# 18. SQL Injection Prevention

All database access shall use safe query mechanisms.

The API shall use:

- Parameterized queries.
- Prepared statements.
- A trusted ORM/query builder with parameterization.
- Strict validation for identifiers and enumerated values.

The following pattern is prohibited:

```
"SELECT * FROM reports WHERE id = " + userInput
```

User-controlled values must never be concatenated directly into SQL.

## 18.1 Scope

Protection applies to:

- Report IDs.
- User IDs.
- Categories.
- Search terms.
- Filters.
- Sorting parameters.
- Pagination parameters.
- Location parameters.
- Spatial queries.
- PostGIS function parameters.

Spatial operations such as:

```
ST_Contains
ST_ClusterDBSCAN
```

must also receive validated and parameterized values.

## 18.2 Database Least Privilege

The application database account should not possess unnecessary administrative privileges such as unrestricted schema modification or destructive operations.

This provides defense in depth in case an application-level vulnerability occurs.

---

# 19. XSS Protection

All user-controlled content shall be treated as untrusted data.

The primary example is the report `description` field.

The system shall:

- Avoid rendering user input as raw HTML.
- Apply output encoding where content is displayed.
- Reject or sanitize unnecessary HTML/script content.
- Store data separately from executable markup.
- Enforce content-length limits.
- Use safe text rendering in Flutter.
- Apply an appropriate Content Security Policy to any web-based operator dashboard.

For example, script content submitted in a report description must never execute when displayed to an operator.

The preferred approach is to render report descriptions as ordinary text rather than allowing arbitrary HTML.

---

# 20. Input Validation vs. Sanitization

Validation and sanitization have different purposes.

### Validation

Determines whether input is acceptable.

Example:

```
latitude must be between -90 and +90
```

### Sanitization

Removes or neutralizes unwanted content where the application explicitly permits the underlying data.

The system should generally prefer **rejecting invalid input** rather than attempting to transform potentially dangerous input into an ambiguous valid form.

Recommended sequence:

```
Receive Input
      ↓
Validate Structure
      ↓
Validate Type / Range
      ↓
Reject Invalid Input
      ↓
Sanitize Where Necessary
      ↓
Parameterized Database Operation
      ↓
Safe Output Encoding
```

---

# 21. Error Handling and Information Disclosure

API errors shall provide enough information for the client to respond correctly without exposing internal implementation details.

The API must not expose:

- Database connection strings.
- SQL statements.
- Stack traces.
- Internal file paths.
- Secret values.
- Service-role credentials.
- Passwords.
- Access tokens.
- Internal infrastructure details.

## 21.1 Recommended Error Categories

```
400 Bad Request
401 Unauthorized
403 Forbidden
404 Not Found
409 Conflict
413 Payload Too Large
415 Unsupported Media Type
422 Unprocessable Entity
429 Too Many Requests
500 Internal Server Error
```

The final API should use a consistent error schema across endpoints.

Validation failures should provide field-level information where safe, without leaking internal implementation details.

---

# 22. HTTPS and Transport Protection

All production API communication shall use secure HTTPS/TLS transport.

The following information must not be transmitted over unencrypted HTTP:

- Authentication credentials.
- Access tokens.
- Account information.
- Location data.
- Report data.
- Uploaded-image access information.
- Other sensitive API data.

The Flutter application shall communicate with the configured secure backend endpoint.

---

# 23. Security Logging and Audit Trail

Security-relevant events should be logged for monitoring and investigation.

Examples include:

- Repeated failed authentication attempts.
- Rate-limit violations.
- Authorization failures.
- Privileged operations.
- Important report status changes.
- Administrative/security configuration changes.
- Credential rotation.
- Credential revocation.

The proposal identifies important report status changes as auditable events, with `STATUS_HISTORY` serving as the report-status audit mechanism.

## 23.1 Sensitive Data Exclusion

Logs must not contain:

- Passwords.
- Access tokens.
- Service-role keys.
- API secrets.
- Complete sensitive request bodies.

Logging should follow data-minimization principles.

---

# 24. API Endpoint Security Matrix

| Endpoint Category   | Authentication | Authorization       | Rate Limit      | Validation      |
| ------------------- | -------------- | ------------------- | --------------- | --------------- |
| Login               | No             | No                  | Strict IP       | Yes             |
| Password Reset      | No             | No                  | Strict IP       | Yes             |
| User Profile        | Yes            | User/Owner          | User            | Yes             |
| Create Report       | Yes            | Citizen             | Strict user     | Yes             |
| Upload Image        | Yes            | Authorized user     | Strict user     | File validation |
| View Own Reports    | Yes            | Citizen/Owner       | User            | Yes             |
| Operator Reports    | Yes            | Operator            | Operator        | Yes             |
| Status Update       | Yes            | Authorized Operator | Strict operator | Yes             |
| Completion Evidence | Yes            | Authorized Operator | User/Role       | File validation |
| Notifications       | Yes            | Authorized User     | User            | Yes             |

This matrix is a proposed implementation mapping and shall be reconciled with the final endpoint list in `T_85ab37`.

---

# 25. Security Rules for the Citizen Workflow

The security layer shall preserve the intended citizen workflow:

```
Register / Login
      ↓
Create Report
      ↓
Add Image + Location + Category + Description
      ↓
Review
      ↓
Submit
      ↓
AI Analysis
      ↓
Track Status
      ↓
Completion Evidence
      ↓
Confirm Resolution
```

At each protected stage:

- User identity must be verified.
- User authorization must be verified.
- Resource ownership must be checked.
- Payloads must be validated.
- File uploads must be validated.
- Rate limits must be respected.
- Sensitive operations must be logged where appropriate.

A citizen may access only reports and resources for which the API confirms authorization.

---

# 26. Security Rules for the Operator Workflow

The operator workflow includes:

```
Operator Login
      ↓
Access Dashboard
      ↓
Review Incoming Reports
      ↓
Review AI Analysis / Priority
      ↓
Assign Cleaning Team
      ↓
Update Status
      ↓
Review Completion Evidence
      ↓
Resolve / Take Further Action
```

The API shall enforce operator permissions independently of the Flutter interface.

The Flutter application may hide unavailable actions, but a direct unauthorized API request must still be rejected.

---

# 27. Secret Exposure Prevention Checklist

Before deployment:

- [ ] No service-role key exists in Flutter source.
- [ ] No privileged secret exists in client-side build artifacts.
- [ ] No real secret exists in public documentation examples.
- [ ] No privileged secret exists in public Git history.
- [ ] Backend secrets are stored using protected configuration.
- [ ] Secrets are excluded from logs.
- [ ] Development and production credentials are separated.
- [ ] Secret rotation procedure is documented.
- [ ] Secret revocation procedure is documented.
- [ ] Compromised credentials can be replaced without modifying the client application.
- [ ] Public/client credentials are separated from privileged service credentials.

---

# 28. Proposed Initial Security Configuration

| Security Control            | Initial Requirement                                            |
| --------------------------- | -------------------------------------------------------------- |
| Transport                   | HTTPS/TLS                                                      |
| Authentication              | Signed authentication token or mechanism defined by `T_85ab37` |
| Token Checks                | Signature, expiry, issuer/audience where applicable            |
| Authorization               | Server-side RBAC                                               |
| Resource Ownership          | Server-side verification                                       |
| Sensitive Role Verification | Re-check authoritative role where required                     |
| Service-Role Key            | Backend/trusted-worker only                                    |
| Login Limit                 | 10 attempts / 15 min / IP                                      |
| Password Reset              | 5 requests / hour / IP                                         |
| Citizen General API         | 120 req/min/user                                               |
| Operator General API        | 180 req/min/user                                               |
| Create Report               | 10 req/15 min/user                                             |
| Image Upload                | 10 uploads/15 min/user                                         |
| Rate-Limit Response         | HTTP 429                                                       |
| Retry Guidance              | `Retry-After` where appropriate                                |
| SQL Injection               | Parameterized queries / prepared statements                    |
| XSS                         | Safe text rendering + output encoding                          |
| File Upload                 | Type, size and content validation                              |
| Error Handling              | No sensitive implementation details                            |
| Transport                   | HTTPS/TLS                                                      |
| Audit                       | Security events + important report status changes              |
| Secrets                     | Server-side protected storage                                  |
| Rotation                    | Controlled replacement and revocation                          |

All numerical thresholds are **proposed initial values** and should be calibrated during testing.

---

# 29. Acceptance Conditions

## AC-01 — Authentication Verification

Protected API endpoints reject requests without valid authentication credentials.

## AC-02 — Signed Token Validation

Invalid, malformed, tampered, or expired signed tokens are rejected.

## AC-03 — Token Claims

Issuer, audience, subject, token type, and required claims are validated where applicable.

## AC-04 — Server-Side Authorization

The API enforces role and resource permissions independently of the Flutter UI.

## AC-05 — Citizen Resource Isolation

A citizen cannot access another citizen's private report by modifying an identifier.

## AC-06 — Role Re-Verification

Sensitive privileged operations verify the current role against the authoritative user/authorization source rather than relying solely on a potentially stale token claim.

## AC-07 — Service-Role Isolation

Service-role credentials are never distributed to or stored in the Flutter client.

## AC-08 — Service-Role Scope

Privileged credentials are used only by authorized backend/trusted processes for approved operations.

## AC-09 — Secret Protection

Privileged secrets are not hard-coded, logged, exposed through API responses, or committed to source control.

## AC-10 — Secret Lifecycle

Secret creation, rotation, expiration where supported, and revocation procedures are documented.

## AC-11 — Rate Limiting

Configured endpoints enforce limits by IP, authenticated user, role, or endpoint as appropriate.

## AC-12 — Rate-Limit Response

Requests exceeding configured limits return:

```
HTTP 429 Too Many Requests
```

and provide `Retry-After` where appropriate.

## AC-13 — Brute-Force Protection

Login and password-reset endpoints apply stricter throttling than normal API endpoints.

## AC-14 — Payload Validation

Invalid types, missing required fields, invalid ranges, oversized payloads, unsupported values, and unauthorized fields are rejected.

## AC-15 — Image Validation

Uploaded images are validated for authentication, authorization, allowed type, actual content, size, and upload constraints.

## AC-16 — SQL Injection Protection

All database operations use parameterized queries, prepared statements, or equivalent safe mechanisms.

## AC-17 — XSS Protection

User-controlled content cannot execute as HTML/JavaScript when displayed.

## AC-18 — Error Safety

API errors do not expose secrets, SQL statements, stack traces, internal paths, or sensitive infrastructure details.

## AC-19 — HTTPS

Production API communication uses HTTPS/TLS.

## AC-20 — Security Logging

Relevant authentication, authorization, rate-limit, credential, and security events are logged without exposing credentials.

## AC-21 — Workflow Compatibility

Security controls do not prevent an authorized citizen from completing the reporting workflow or an authorized operator from completing required operational actions.

## AC-22 — Configuration

Rate limits and other tunable security thresholds can be modified through configuration without changing the fundamental authorization and validation logic.

## AC-23 — Environment Isolation

Development, staging, and production privileged credentials are separated so that compromise of one environment does not automatically grant access to another.

---

# 30. Delivered Means

Delivered means the project contains a complete API security specification covering:

- Protected API request verification.
- Authentication and signed-token validation.
- Server-side authorization.
- Citizen/operator role separation.
- Resource ownership validation.
- Sensitive-operation role re-verification.
- Service-role key isolation under `ADR-007`.
- Secret and API-key lifecycle management.
- Proposed rate-limiting thresholds by IP, user, role, and endpoint.
- Brute-force protection.
- Payload validation.
- Image/file upload validation.
- SQL injection prevention.
- XSS prevention.
- Error and information-disclosure controls.
- HTTPS/TLS requirements.
- Security logging and audit requirements.
- Endpoint security mapping.
- Citizen workflow security.
- Operator workflow security.
- Security deployment checklist.
- Measurable acceptance conditions.
- Clear separation between proposal-derived requirements and proposed implementation values.

---

# 31. Final Security Boundary

The CleanStreet AI API shall follow this security boundary:

```
                         UNTRUSTED
                            |
                            v
                   +----------------+
                   | Flutter Client |
                   +----------------+
                            |
                       HTTPS/TLS
                            |
                            v
                   +----------------+
                   | Rate Limiting |
                   +----------------+
                            |
                            v
                   +----------------+
                   | Token Verify   |
                   +----------------+
                            |
                            v
                   +----------------+
                   | RBAC / Access  |
                   +----------------+
                            |
                            v
                   +----------------+
                   | Resource       |
                   | Ownership      |
                   +----------------+
                            |
                            v
                   +----------------+
                   | Payload/File   |
                   | Validation     |
                   +----------------+
                            |
                            v
                   +----------------+
                   | Safe DB / File |
                   | Operations     |
                   +----------------+
                            |
                            v
                   +----------------+
                   | Audit Logging  |
                   +----------------+
                            |
                            v
                         TRUSTED
                      Backend Layer
```

## Core Security Principle

**No client-provided value, role, identifier, file, token, or credential is trusted until it has passed the appropriate server-side security checks.**

---

# 32. Reconciliation Requirements

Before this specification is considered final for implementation, the following items shall be reconciled with the dependent artifacts:

### With `T_85ab37`

- Final authentication mechanism.
- Token/session format.
- Token claims.
- Role names.
- Permission model.
- Revocation behavior.
- Final protected endpoint list.

### With `ADR-007`

- Exact service-role credential architecture.
- Credential storage mechanism.
- Trusted service boundaries.
- Allowed service-role operations.
- Environment separation.
- Privileged-operation auditing.

### During Security Testing

- Rate-limit calibration.
- Maximum payload sizes.
- Maximum image sizes.
- Supported file formats.
- Authentication throttling behavior.
- XSS test cases.
- SQL injection test cases.
- API error behavior.
- Secret-rotation testing.

Until these dependencies are reconciled, this document should be treated as the **proposed API security baseline**, rather than the final implementation authority.

---

*End of API Protection and Rate Limiting Requirements.*