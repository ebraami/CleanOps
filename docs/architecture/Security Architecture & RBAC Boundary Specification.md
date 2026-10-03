# Security Architecture & RBAC Boundary Specification

**Project:** CleanOps  
**Task:** Security Architecture & RBAC Boundary Specification  
**Work Package:** System Architecture  
**Owner:** Ebraam Ibrahim  
**Priority:** High  
**Status:** Draft  
**Date:** 2026-10-03

---

## 1. Purpose

This document defines the overarching security architecture of the CleanOps platform.

It establishes the security boundaries between users, the frontend, the Edge Function API gateway, backend services, data services, and external integrations.

The architecture covers:

- Token-based authentication
- JWT lifecycle
- Role-Based Access Control (RBAC)
- API gateway protection
- TLS and CORS enforcement
- External network boundary isolation

---

# 2. Security Architecture Overview

CleanOps follows a layered security model:

```text
                    ┌──────────────────────┐
                    │      End Users       │
                    │ Citizen / Cleaning   │
                    │ Team / Operator /    │
                    │ Administrator        │
                    └──────────┬───────────┘
                               │
                         HTTPS / TLS
                               │
                               ▼
                    ┌──────────────────────┐
                    │   CleanOps Frontend  │
                    │   Cloudflare Pages   │
                    └──────────┬───────────┘
                               │
                         Authenticated API
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Supabase Edge API     │
                    │ Authentication +      │
                    │ Authorization +       │
                    │ Request Validation    │
                    └──────────┬───────────┘
                               │
                     Authorized operations
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
       ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
       │ Supabase DB │  │ Agent/Boss  │  │ External    │
       │             │  │ Gateway     │  │ Services    │
       └─────────────┘  └─────────────┘  └─────────────┘
