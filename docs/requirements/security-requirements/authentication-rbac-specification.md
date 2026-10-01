# Authentication and Role-Based Access Control (RBAC) Specification

**Project:** CleanOps  
**Task:** Authentication and Role-Based Access Control (RBAC) Specification  
**Owner:** Ebraam Ibrahim  
**Work Package:** Security Requirements  
**Priority:** High  
**Status:** Draft  
**Date:** 2026-10-01

---

## 1. Purpose

This document defines the security requirements for authentication, session management, token handling, and role-based access control (RBAC) within the CleanOps platform.

The objective is to ensure that users are securely authenticated, sessions are controlled throughout their lifecycle, tokens can be invalidated when required, and every protected operation is restricted according to the user's assigned role.

---

## 2. Authentication Requirements

### 2.1 Authentication Flow

CleanOps shall use Firebase-based authentication as the identity/authentication layer.

After successful authentication:

1. The user authenticates through the configured Firebase authentication mechanism.
2. Firebase establishes the authenticated identity.
3. The resulting authentication credential/token is exchanged or presented to the CleanOps backend.
4. The backend validates the authentication token before allowing access to protected resources.
5. The backend derives the CleanOps user identity and role from trusted server-side data.
6. Authorization is evaluated before performing protected operations.

### 2.2 JWT Validation

For every protected API request, the backend shall validate the supplied JWT before processing the request.

JWT validation shall include, as applicable:

- Signature verification.
- Token expiration (`exp`) validation.
- Issuer (`iss`) validation.
- Audience (`aud`) validation.
- Subject (`sub`) validation.
- Validation that the authenticated identity corresponds to a valid CleanOps user.
- Validation that the session/token has not been revoked where revocation checking is required.

A request with an invalid, expired, malformed, or otherwise unacceptable token shall be rejected.

### 2.3 Authentication Failure

Authentication failures shall not expose sensitive implementation details.

Examples include:

- Missing authentication credentials.
- Invalid credentials.
- Expired JWT.
- Invalid JWT signature.
- Invalid issuer or audience.
- Revoked authentication session.

Protected operations shall not continue after authentication failure.

---

## 3. Session Lifecycle

### 3.1 Session Establishment

A session begins after successful authentication and successful backend validation of the authenticated identity.

The backend shall associate the session with the authenticated CleanOps user.

### 3.2 Session Timeout

Sessions shall have a defined maximum lifetime and/or inactivity timeout according to the platform's configured security policy.

When the applicable timeout is reached:

- The session shall no longer authorize protected operations.
- The user shall be required to authenticate again or establish a valid session.
- Existing authorization state shall not be trusted beyond the session lifetime.

### 3.3 Session Termination

A session shall be terminated when:

- The user explicitly logs out, where logout invalidation is supported.
- The session expires.
- The authentication credential is revoked.
- The account is disabled or otherwise prevented from accessing the platform.

After termination, previously issued session credentials shall not continue to grant access where revocation is required.

---

## 4. Token Revocation

CleanOps shall support token/session invalidation for security-sensitive events.

Revocation shall be possible when:

- A user logs out where server-side revocation is applicable.
- A credential is suspected to be compromised.
- An administrator disables an account.
- A security incident requires invalidating active sessions.
- A user's authorization state requires existing credentials to stop being accepted.

A revoked token/session must not be accepted for protected operations after the revocation state becomes effective.

---

# 5. Role-Based Access Control

CleanOps shall enforce authorization according to the authenticated user's assigned role.

The defined roles are:

1. **Citizen**
2. **Cleaning Team**
3. **Operator**
4. **Administrator**

Authorization shall be enforced server-side. Frontend visibility alone must never be treated as sufficient authorization.

---

## 6. RBAC Permission Matrix

| Capability / Operation | Citizen | Cleaning Team | Operator | Administrator |
|---|---:|---:|---:|---:|
| Authenticate | ✓ | ✓ | ✓ | ✓ |
| Access own profile | ✓ | ✓ | ✓ | ✓ |
| Modify own permitted profile data | ✓ | ✓ | ✓ | ✓ |
| Create citizen report | ✓ | ✗ | ✗ | ✗ |
| View own submitted reports | ✓ | ✗ | ✗ | ✗ |
| Work on assigned cleaning tasks | ✗ | ✓ | ✗ | ✗ |
| Submit cleaning-task evidence | ✗ | ✓ | ✗ | ✗ |
| Review/verify reports | ✗ | ✗ | ✓ | ✓ |
| Manage report lifecycle transitions | ✗ | ✗ | ✓ | ✓ |
| Access operational project data | ✗ | Limited to assigned work | ✓ | ✓ |
| Manage users | ✗ | ✗ | ✗ | ✓ |
| Manage roles/permissions | ✗ | ✗ | ✗ | ✓ |
| Manage system configuration | ✗ | ✗ | ✗ | ✓ |
| Access administrative security controls | ✗ | ✗ | ✗ | ✓ |
| Access audit/security records | ✗ | ✗ | As permitted for operations | ✓ |

**Legend:** ✓ = permitted, ✗ = forbidden, Limited = restricted to the user's assigned scope and authorized records.

---

## 7. Citizen Permissions

A Citizen may:

- Authenticate into CleanOps.
- Access their own permitted profile information.
- Create a report through the supported reporting workflow.
- View reports associated with their own account where permitted.
- Receive permitted status/closure information for their own reports.

A Citizen must not:

- Access another Citizen's private information.
- Modify reports belonging to another user.
- Perform cleaning-team operations.
- Perform operator verification or approval.
- Manage users or roles.
- Modify system configuration.
- Access administrative security controls.

---

## 8. Cleaning Team Permissions

A Cleaning Team member may:

- Authenticate into CleanOps.
- Access their own permitted profile information.
- View cleaning work assigned to them.
- Perform authorized actions on assigned cleaning tasks.
- Submit required cleaning evidence for assigned work.
- Update permitted task/work status according to the workflow.

A Cleaning Team member must not:

- Access unrelated private citizen data beyond what is required for authorized work.
- Approve or administratively close reports unless explicitly authorized by the workflow.
- Manage users or roles.
- Modify system-wide configuration.
- Access administrator-only security controls.
- Modify another team member's assignments without authorization.

---

## 9. Operator Permissions

An Operator may:

- Authenticate into CleanOps.
- Access authorized operational data.
- Review submitted reports.
- Perform authorized verification and evidence review.
- Perform permitted report lifecycle transitions.
- Handle rejection, rework, and resolution workflows according to the defined process.
- Access operational information necessary to perform assigned duties.

An Operator must not:

- Manage system administrator accounts unless explicitly authorized.
- Change system-wide roles or permissions.
- Modify security configuration reserved for Administrators.
- Access information outside the Operator's authorized operational scope.
- Bypass required report lifecycle validation or approval rules.

---

## 10. Administrator Permissions

An Administrator may perform authorized administrative operations, including:

- Manage users.
- Manage role assignments.
- Manage system configuration.
- Manage administrative security settings.
- Access authorized audit/security records.
- Perform administrative actions required to maintain the platform.

Administrator access must still be authenticated, authorized, logged, and subject to the platform's security controls.

An Administrator must not bypass authentication or authorization controls simply because the account has administrative privileges.

---

## 11. Authorization Enforcement

Every protected operation shall follow this sequence:

```text
Request
  ↓
Authenticate user
  ↓
Validate token/session
  ↓
Resolve CleanOps identity
  ↓
Resolve assigned role
  ↓
Check resource scope
  ↓
Check role permission
  ↓
Perform operation
  ↓
Record security-relevant action where required
```

If authentication or authorization fails, the protected operation shall not execute.

Authorization decisions shall be made using trusted server-side information.

---

## 12. Resource-Level Authorization

Role authorization alone is not sufficient for operations involving user-owned or assigned resources.

The backend shall also verify that the authenticated user is authorized to access the specific resource.

Examples:

- A Citizen can access their own permitted reports but not another Citizen's private reports.
- A Cleaning Team member can modify assigned cleaning work but not another member's unrelated assignments.
- An Operator can access reports within their authorized operational scope.
- An Administrator can access administrative resources according to administrator permissions.

---

## 13. Forbidden-Action Principles

The following principles apply to all roles:

1. A frontend-hidden operation is still forbidden if the backend does not authorize it.
2. Changing request parameters must not allow a user to access another user's resources.
3. A user must not be able to change their own role through a normal user operation.
4. A lower-privileged role must not gain access by directly calling protected API endpoints.
5. Authorization must be checked on every protected operation rather than relying only on previous frontend navigation.
6. Role changes must be performed through authorized administrative mechanisms.
7. Sensitive operations should be auditable.

---

## 14. Security Requirements Summary

CleanOps authentication and authorization shall provide:

- Secure authentication through the configured Firebase authentication flow.
- Server-side JWT validation.
- Controlled session lifecycle and expiration.
- Token/session revocation capability.
- Explicit RBAC rules for Citizen, Cleaning Team, Operator, and Administrator.
- Resource-level authorization in addition to role checks.
- Server-side enforcement of all protected permissions.
- Explicit denial of unauthorized operations.
- Security-relevant auditing where required.

---

## 15. Deliverable

This document is the authentication and RBAC specification for the **Security Requirements** Work Package.

**Required submission:** Direct GitHub link to this `.md` document in the CleanOps project repository.
