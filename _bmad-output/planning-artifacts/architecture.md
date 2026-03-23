---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8]
inputDocuments:
  - _bmad-output/planning-artifacts/prd-draft.md
  - _bmad-output/planning-artifacts/prd-validation-report.md
  - _bmad-output/planning-artifacts/ux-design-specification.md
  - _bmad-output/planning-artifacts/product-brief.md
workflowType: 'architecture'
lastStep: 8
status: 'complete'
completedAt: '2026-03-12'
project_name: 'avatar'
user_name: 'Art'
date: '2026-03-12'
---

# Architecture Decision Document

_This document builds collaboratively through step-by-step discovery. Sections are appended as we work through each architectural decision together._

## Project Context Analysis

### Requirements Overview

**Functional Requirements:**
The product requires a multi-tenant white-label operating model with strict agency/client boundaries, role-scoped access, recurring content workflow management, and a request-centric interaction loop. Core capabilities include branding configuration, pilot client onboarding, content calendar operations, status transitions, request intake, reusable asset linking, manual KPI recording, baseline comparison, and pilot continuation outcome capture.

**Non-Functional Requirements:**
Architecture must enforce tenant isolation and authorization boundaries, meet p95 performance targets for core views/actions, preserve desktop-first usability under defined browser matrix constraints, and satisfy WCAG 2.1 AA expectations for critical flows. It must support extension to additional channels and integrations without redesigning core MVP entities.

**Scale & Complexity:**
The scope is medium-complexity for a web application: not enterprise-scale at MVP, but with important cross-cutting demands (multi-tenancy, RBAC, observability, accessibility, extensibility).

- Primary domain: web_app (B2B multi-tenant workflow platform)
- Complexity level: medium
- Estimated architectural components: 9-12

### Technical Constraints & Dependencies

- MVP constrained to one segment (`media / creators`) and one channel (`Instagram`)
- Desktop-first operation; mobile as fallback, no full parity in MVP
- Manual KPI entry in MVP; no deep analytics integrations
- White-label branding is required but must not reduce operational clarity
- Pilot onboarding templates are part of core product behavior, not documentation-only
- PRD validation passed overall, with minor residual wording refinements (FR9/NFR9)

### Cross-Cutting Concerns Identified

- Tenant isolation and authorization policy consistency
- Role-based access control across agency/client contexts
- Request lifecycle coherence across calendar, status, and summary surfaces
- Performance monitoring against p95 SLA-like targets
- Accessibility compliance (WCAG 2.1 AA) in core workflows
- Future integration and channel extensibility boundaries
- Auditability of manual KPI and continuation decision signals

## Starter Template Evaluation

### Primary Technology Domain

web_app (multi-tenant B2B workflow platform) based on PRD + UX analysis.

### Evaluation Criteria (Weighted)

| Criterion | Weight |
|---|---:|
| Architectural control (tenancy/RBAC/domain boundaries) | 30% |
| MVP speed with low complexity overhead | 25% |
| AI-agent implementation consistency | 20% |
| Maintenance/stability risk | 15% |
| Ecosystem flexibility for post-MVP growth | 10% |

### Comparative Analysis Matrix

| Option | Arch Control (30) | MVP Speed (25) | Agent Consistency (20) | Stability (15) | Flexibility (10) | Weighted Score |
|---|---:|---:|---:|---:|---:|---:|
| `create-next-app` | 9 | 8 | 9 | 10 | 8 | **8.9** |
| `create-t3-app` | 7 | 8 | 7 | 8 | 8 | **7.6** |
| SaaS Boilerplate (3rd-party) | 5 | 6 | 5 | 6 | 7 | **5.7** |

### Selected Starter: create-next-app

**Decision:**
Use `create-next-app` as baseline to maximize architectural clarity and reduce hidden assumptions in multi-tenant MVP.

**Rationale for Selection:**
- Highest score on architectural control and implementation consistency.
- Lowest "implicit architecture" risk for tenancy/RBAC-sensitive product.
- Officially maintained baseline with predictable upgrades and docs.

**Initialization Command:**

```bash
npx create-next-app@latest avatar --typescript --tailwind --eslint --app --src-dir
```

### Architectural Decisions Provided by Starter

**Language & Runtime:**
TypeScript-first Next.js app with App Router baseline.

**Styling Solution:**
Tailwind CSS integrated by default.

**Build Tooling:**
Next.js standard build/runtime pipeline with modern defaults.

**Testing Framework:**
No heavy opinionated stack pre-imposed (lets architecture decisions define tests cleanly).

**Code Organization:**
`src/` + App Router conventions as a neutral, scalable starting point.

**Development Experience:**
Strong default DX (linting + modern tooling) with minimal startup friction.

### Guardrails (to avoid starter drift)

- Keep starter scope minimal; add only architecture-approved dependencies.
- Define tenancy and RBAC as first-class modules before feature expansion.
- Avoid SaaS-kit patterns not required by MVP FR/NFR.
- Treat starter init as implementation story #1 and freeze baseline after initial setup.

## Core Architectural Decisions

### Decision Priority Analysis

**Critical Decisions (Block Implementation):**
- Backend runtime and framework: Python + FastAPI
- Primary database and persistence model: PostgreSQL + SQLAlchemy + Alembic
- Authentication and authorization baseline: Python auth service + tenant-scoped RBAC
- API contract strategy: REST + OpenAPI + Pydantic schema contracts
- Deployment topology: split runtime (Next.js frontend + Python API)

**Important Decisions (Shape Architecture):**
- Frontend state/data sync model (TanStack Query + local UI state)
- Observability baseline (Sentry + structured logs + platform metrics)
- Cross-service boundary and error envelope conventions
- Security middleware policy (rate limits, audit events, session hardening)

**Deferred Decisions (Post-MVP):**
- Redis/distributed caching layer
- Event-driven async integration architecture
- Read replicas and advanced DB partitioning

### Data Architecture

- **Primary DB:** PostgreSQL 18.x
- **ORM:** SQLAlchemy 2.0.48
- **Migrations:** Alembic 1.18.4
- **Validation contracts:** Pydantic 2.12.5
- **Data modeling approach:** tenant-first domain model (`tenant`, `agency_workspace`, `pilot_client`, `content_item`, `content_request`, `asset`, `kpi_snapshot`, `continuation_outcome`)
- **Caching strategy (MVP):** no dedicated distributed cache; prefer query optimization and selective short-lived app caching

### Authentication & Security

- **Auth approach:** Python-side authentication/session management in FastAPI service
- **Authorization:** policy layer enforcing tenant + role scope (agency operator vs client viewer/requester)
- **Session/security defaults:** secure cookies, strict token/session validation, CSRF-safe flows where applicable
- **Security middleware:** rate limiting, standardized audit logging, request correlation IDs
- **Encryption:** TLS in transit + managed database encryption at rest

### API & Communication Patterns

- **API style:** REST via FastAPI
- **Schema/contracts:** Pydantic models for request/response DTOs
- **Documentation:** OpenAPI generated from FastAPI and exposed as source-of-truth contract
- **Error handling:** unified error envelope (`code`, `message`, `details`, `trace_id`)
- **Service communication:** modular monolith boundaries in MVP (no microservices split yet)

### Frontend Architecture

- **Frontend baseline:** Next.js App Router (from starter)
- **Server/client split:** server components by default, client components for interactive request/status workflows
- **Server-state management:** TanStack Query v5
- **UI state:** local component state + scoped shared state only where needed
- **Performance approach:** route/code splitting, skeleton states, optimized list rendering for calendar/request views

### Infrastructure & Deployment

- **Runtime split:** Next.js frontend + Python FastAPI backend
- **Hosting model:** frontend on Vercel; Python API on a managed platform (Render/Fly/Railway class)
- **Database hosting:** managed PostgreSQL
- **CI/CD:** GitHub Actions with separate web/api pipelines and required quality gates (lint/type/test/build)
- **Environment model:** isolated `dev`, `stage`, `prod` stacks with separate secrets and DBs
- **Monitoring:** Sentry + platform-level metrics + structured application logs

### Decision Impact Analysis

**Implementation Sequence:**
1. Initialize frontend via `create-next-app`
2. Scaffold Python API service with FastAPI + core middleware
3. Establish PostgreSQL schema + Alembic migration baseline
4. Implement auth + tenant/RBAC policy layer
5. Build request/status/KPI core APIs and integrate frontend data flows
6. Add observability and security hardening before pilot rollout

**Cross-Component Dependencies:**
- Tenant/RBAC decisions constrain every API and UI data query
- DB schema and migration model define contract stability for frontend integration
- Error envelope and tracing conventions must be shared across frontend/backend for operational debugging

## Implementation Patterns & Consistency Rules

### Pattern Categories Defined

**Critical Conflict Points Identified:**
5 key areas where AI agents could diverge and break consistency.

### Naming Patterns

**Database Naming Conventions:**
- Tables: `snake_case`, plural (e.g., `pilot_clients`, `content_requests`)
- Columns: `snake_case` (e.g., `tenant_id`, `created_at`)
- Foreign keys: `<entity>_id` (e.g., `pilot_client_id`)
- Indexes: `idx_<table>_<column>` (e.g., `idx_content_requests_tenant_id`)

**API Naming Conventions:**
- REST resources: plural nouns (e.g., `/api/pilot-clients`, `/api/content-requests`)
- Path params: `{resource_id}` style (e.g., `/api/content-requests/{request_id}`)
- Query params: `snake_case`
- Headers: standard HTTP header casing; custom headers prefixed with `X-Avatar-`

**Code Naming Conventions:**
- Python modules/files: `snake_case.py`
- Python classes: `PascalCase`
- Python functions/vars: `snake_case`
- TypeScript components: `PascalCase.tsx`
- TypeScript hooks/utils: `camelCase` exports, file names `kebab-case`

### Structure Patterns

**Project Organization:**
- Separate top-level apps:
  - `apps/web` (Next.js)
  - `apps/api` (FastAPI)
- Shared contracts/types in dedicated shared package/folder:
  - `packages/contracts` (OpenAPI-generated client/types or schema artifacts)
- Domain-first organization inside API:
  - `domains/tenant`, `domains/pilot_client`, `domains/request`, `domains/kpi`

**File Structure Patterns:**
- Tests:
  - API: `tests/` (pytest)
  - Web: co-located `*.test.ts(x)` for UI logic
- Migrations only in Alembic directory, no ad-hoc SQL in feature folders
- Environment config centralized per app (`settings.py` / `env.ts`)

### Format Patterns

**API Response Formats:**
- Success envelope:
  - `{ "data": ..., "meta": { ...optional... } }`
- Error envelope:
  - `{ "error": { "code": "...", "message": "...", "details": ... }, "trace_id": "..." }`
- Never mix raw and enveloped responses in same API surface.

**Data Exchange Formats:**
- JSON keys in API payloads: `snake_case` (backend-native consistency)
- Date/time: ISO-8601 UTC strings
- Booleans: strict JSON `true/false`
- Null handling: explicit nullable fields in schema; avoid implicit missing semantics for required fields

### Communication Patterns

**Event System Patterns (MVP-light):**
- Domain events naming: `domain.entity.action` (e.g., `request.status.updated`)
- Event payload minimum:
  - `event_name`, `event_version`, `occurred_at`, `tenant_id`, `entity_id`, `payload`
- Event versioning required once events cross module boundaries.

**State Management Patterns (Frontend):**
- Server state via TanStack Query only
- UI state local-first (component scope), elevate only when shared by sibling flows
- Mutations must invalidate/refetch by explicit query key conventions

### Process Patterns

**Error Handling Patterns:**
- API raises domain-specific exceptions mapped centrally to error envelope
- No raw stack traces in client-facing payloads
- Structured logging includes `trace_id`, `tenant_id`, `user_id` (when available)

**Loading State Patterns:**
- Every async view has explicit loading, empty, error, success states
- Use skeletons for primary list/calendar surfaces
- Disable duplicate submit actions while mutation is in flight

### Enforcement Guidelines

**All AI Agents MUST:**
- Follow naming conventions exactly (DB/API/code)
- Return API envelopes in standardized success/error format
- Respect tenant boundary checks in every query/mutation path
- Add/update schema contracts when changing payload shape
- Include tests for auth scope and cross-tenant denial paths

**Pattern Enforcement:**
- PR checklist includes "pattern compliance" section
- CI gate includes lint + typecheck + tests for both apps
- Violations are fixed in the same PR, not deferred

### Pattern Examples

**Good Examples:**
- `GET /api/content-requests?pilot_client_id=...` -> `{ "data": [...], "meta": { "count": 12 } }`
- DB FK: `content_requests.pilot_client_id`
- Error: `{ "error": { "code": "forbidden", "message": "Access denied" }, "trace_id": "..." }`

**Anti-Patterns:**
- Mixing `camelCase` and `snake_case` in API payloads
- Returning raw arrays in some endpoints and envelopes in others
- Tenant filtering in service A but missing in service B
- Feature code writing direct SQL bypassing shared policy checks

## Project Structure & Boundaries

### Complete Project Directory Structure

```text
avatar/
├── README.md
├── .gitignore
├── .editorconfig
├── .env.example
├── docker-compose.yml
├── Makefile
├── docs/
│   ├── architecture/
│   └── api/
├── .github/
│   └── workflows/
│       ├── ci-web.yml
│       ├── ci-api.yml
│       └── ci-e2e.yml
├── apps/
│   ├── web/
│   │   ├── package.json
│   │   ├── next.config.ts
│   │   ├── tsconfig.json
│   │   ├── postcss.config.js
│   │   ├── tailwind.config.ts
│   │   ├── public/
│   │   ├── src/
│   │   │   ├── app/
│   │   │   │   ├── (agency)/
│   │   │   │   ├── (client)/
│   │   │   │   ├── api/
│   │   │   │   ├── layout.tsx
│   │   │   │   └── page.tsx
│   │   │   ├── components/
│   │   │   │   ├── ui/
│   │   │   │   ├── calendar/
│   │   │   │   ├── requests/
│   │   │   │   ├── kpi/
│   │   │   │   └── auth/
│   │   │   ├── features/
│   │   │   │   ├── tenant/
│   │   │   │   ├── pilot-client/
│   │   │   │   ├── content-item/
│   │   │   │   ├── content-request/
│   │   │   │   ├── asset-library/
│   │   │   │   └── kpi-snapshot/
│   │   │   ├── lib/
│   │   │   │   ├── api-client/
│   │   │   │   ├── query/
│   │   │   │   ├── auth/
│   │   │   │   └── utils/
│   │   │   ├── state/
│   │   │   ├── types/
│   │   │   └── middleware.ts
│   │   └── tests/
│   │       ├── unit/
│   │       ├── integration/
│   │       └── e2e/
│   └── api/
│       ├── pyproject.toml
│       ├── uv.lock / poetry.lock
│       ├── alembic.ini
│       ├── .env.example
│       ├── app/
│       │   ├── main.py
│       │   ├── core/
│       │   │   ├── config.py
│       │   │   ├── security.py
│       │   │   ├── logging.py
│       │   │   ├── exceptions.py
│       │   │   └── middleware.py
│       │   ├── db/
│       │   │   ├── session.py
│       │   │   ├── base.py
│       │   │   └── models/
│       │   ├── api/
│       │   │   ├── deps.py
│       │   │   ├── v1/
│       │   │   │   ├── routes_tenant.py
│       │   │   │   ├── routes_pilot_clients.py
│       │   │   │   ├── routes_content_items.py
│       │   │   │   ├── routes_content_requests.py
│       │   │   │   ├── routes_assets.py
│       │   │   │   ├── routes_kpi_snapshots.py
│       │   │   │   ├── routes_continuation.py
│       │   │   │   └── routes_auth.py
│       │   ├── schemas/
│       │   ├── domains/
│       │   │   ├── tenant/
│       │   │   ├── pilot_client/
│       │   │   ├── content_item/
│       │   │   ├── content_request/
│       │   │   ├── asset/
│       │   │   ├── kpi_snapshot/
│       │   │   └── continuation_outcome/
│       │   ├── services/
│       │   ├── repositories/
│       │   └── policies/
│       ├── alembic/
│       │   ├── env.py
│       │   └── versions/
│       └── tests/
│           ├── unit/
│           ├── integration/
│           └── contract/
└── packages/
    └── contracts/
        ├── openapi/
        ├── generated/
        └── README.md
```

### Architectural Boundaries

**API Boundaries:**
- `apps/api/app/api/v1/*` is the only public backend API surface.
- Tenant context is required for all domain routes.
- Auth boundary: `routes_auth.py` + policy checks in `policies/`.

**Component Boundaries:**
- `apps/web/src/components/ui` for reusable UI primitives only.
- `apps/web/src/features/*` for feature modules without cross-feature business logic.
- `apps/web/src/lib/api-client` as the single HTTP access point.

**UX Component-to-Folder Mapping (Implementation Contract):**
- `Request Composer` -> `apps/web/src/components/requests/RequestComposer.tsx`
- `Status Timeline Strip` -> `apps/web/src/components/requests/StatusTimelineStrip.tsx`
- `Meeting Summary Panel` -> `apps/web/src/components/kpi/MeetingSummaryPanel.tsx`
- `Calendar State Card` -> `apps/web/src/components/calendar/CalendarStateCard.tsx`
- `Role-Scope Badge Set` -> `apps/web/src/components/auth/RoleScopeBadge.tsx`
- Feature orchestration wrappers for these components live in `apps/web/src/features/*`.

**Service Boundaries:**
- `domains/*` hold use cases and domain invariants.
- `repositories/*` handle DB access with no business rules.
- `services/*` orchestrate workflows between domain modules.

**Data Boundaries:**
- SQLAlchemy models live only in `db/models`.
- DB changes are only via `alembic/versions`.
- Pydantic schemas are separate from persistence models.

### Requirements to Structure Mapping

**Feature/Epic Mapping:**
- Agency Launch Foundation -> `domains/tenant`, `domains/pilot_client`, `routes_tenant.py`, `routes_pilot_clients.py`
- Recurring Content Operations -> `domains/content_item`, `domains/content_request`, `domains/asset`
- Pilot Validation -> `domains/kpi_snapshot`, `domains/continuation_outcome`

**Cross-Cutting Concerns:**
- RBAC + tenant isolation -> `policies/`, `api/deps.py`, `core/middleware.py`
- Error envelope + tracing -> `core/exceptions.py`, `core/logging.py`
- Accessibility support metadata remains in web adapters, not backend domain logic.

### Integration Points

**Internal Communication:**
- Web <-> API through typed contract client in `packages/contracts/generated`.
- Domain to repository communication through explicit interfaces.
- Middleware to policy layer for request-scoped authorization.

**External Integrations:**
- Auth provider integration behind `routes_auth.py` and `core/security.py`.
- Monitoring sinks integrated via `core/logging.py`.

**Data Flow:**
- Client action -> Next.js feature module -> API client -> FastAPI route -> domain service -> repository -> PostgreSQL -> standardized API envelope -> UI refresh via TanStack Query.

### File Organization Patterns

**Configuration Files:**
- Runtime/env config is centralized per app (`apps/web`, `apps/api`).
- Shared non-secret defaults live in root `.env.example`.

**Source Organization:**
- Domain-first backend organization.
- Feature-first frontend with shared UI primitives.
- Responsive policy source of truth:
  - MVP desktop requirement baseline: `>=1280px` (authoritative for acceptance).
  - `1280`, `1440`, and `1920` are required validated desktop breakpoints.
  - `1024-1279` is supported as best-effort tablet/compact desktop fallback, not a primary acceptance target.

**Test Organization:**
- API: `unit`, `integration`, `contract`.
- Web: `unit`, `integration`, `e2e`.
- Contract sync checks against OpenAPI-generated clients.

**Asset Organization:**
- Static web assets in `apps/web/public`.
- Non-public generated artifacts in app-local build/temp locations only.

### Development Workflow Integration

**Development Server Structure:**
- Local parallel runs for web + api + postgres (task runner or compose).

**Build Process Structure:**
- Independent build/test pipelines per app.
- Contract generation/check as dependency between API and web CI jobs.

**Deployment Structure:**
- Separate deployment units for web and API.
- Shared release tagging and environment promotion gates.

## Architecture Validation Results

### Coherence Validation ✅

**Decision Compatibility:**
- Stack decisions are compatible: Next.js (web), FastAPI (api), PostgreSQL (data), OpenAPI/Pydantic contracts.
- No contradictory technology choices across sections.
- Implementation patterns align with the selected runtime split and modular-monolith backend.

**Pattern Consistency:**
- Naming, envelope format, and tenant-scope rules are consistent across API/data/code.
- Communication and state patterns support the selected stack (REST + TanStack Query).
- Process patterns (error handling/loading states) match UX and operational requirements.

**Structure Alignment:**
- Project structure supports all core decisions and boundaries.
- API/component/service/data boundaries are explicit and implementable.
- Integration points are clearly mapped between web, api, and contracts package.

### Requirements Coverage Validation ✅

**Epic/Feature Coverage:**
- Agency launch, recurring content operations, and pilot validation features are mapped to concrete modules.
- Cross-feature dependencies are covered via shared contracts and policy layer.

**Functional Requirements Coverage:**
- All core FR categories have architectural support: tenancy, roles, request lifecycle, status tracking, asset reuse, KPI capture, continuation outcomes.

**Non-Functional Requirements Coverage:**
- Security: tenant isolation + RBAC + middleware controls covered.
- Performance: structure supports query optimization, client caching patterns, and route-level optimizations.
- Accessibility and platform constraints: desktop-first + WCAG-oriented implementation guidance is preserved in web architecture.

### Implementation Readiness Validation ✅

**Decision Completeness:**
- Critical decisions are documented with concrete technologies and versions.
- Patterns and consistency rules are explicit and enforceable.

**Structure Completeness:**
- Complete project tree is defined for root, apps, packages, tests, and CI.
- Boundaries and integration paths are implementation-ready.

**Pattern Completeness:**
- Conflict-prone areas are addressed (naming, envelopes, tenant checks, contracts, tests).
- Error, loading, and communication conventions are specified.

### Gap Analysis Results

**Critical Gaps:** None.

**Important Gaps (non-blocking):**
- Formal API version lifecycle policy should be documented (`/api/v1` deprecation strategy).
- CI migration safety checks should explicitly include rollback/checkpoint verification.
- Contract package version pinning policy between web/api should be formalized.

**Nice-to-Have Gaps:**
- Add starter templates for common domain module scaffolding.
- Add concise runbooks for local onboarding and incident triage.

### Validation Issues Addressed

- No blocking issues identified.
- Non-blocking improvements captured for post-MVP hardening backlog.

### Architecture Completeness Checklist

**✅ Requirements Analysis**

- [x] Project context thoroughly analyzed
- [x] Scale and complexity assessed
- [x] Technical constraints identified
- [x] Cross-cutting concerns mapped

**✅ Architectural Decisions**

- [x] Critical decisions documented with versions
- [x] Technology stack fully specified
- [x] Integration patterns defined
- [x] Performance considerations addressed

**✅ Implementation Patterns**

- [x] Naming conventions established
- [x] Structure patterns defined
- [x] Communication patterns specified
- [x] Process patterns documented

**✅ Project Structure**

- [x] Complete directory structure defined
- [x] Component boundaries established
- [x] Integration points mapped
- [x] Requirements to structure mapping complete

### Architecture Readiness Assessment

**Overall Status:** READY FOR IMPLEMENTATION

**Confidence Level:** high

**Key Strengths:**
- Coherent split-runtime architecture with clear boundaries
- Strong consistency guardrails for multi-agent implementation
- Requirements-to-structure traceability

**Areas for Future Enhancement:**
- API lifecycle/versioning policy formalization
- Migration safety automation expansion
- Contract synchronization governance

### Implementation Handoff

**AI Agent Guidelines:**

- Follow architectural decisions and boundaries as documented
- Apply naming, envelope, and tenant-policy rules consistently
- Keep contract schemas synchronized with API changes
- Validate cross-tenant denial paths and role scopes in tests

**First Implementation Priority:**
1. Initialize web app baseline with `create-next-app`
2. Scaffold FastAPI service with core middleware and policy foundation
