---
stepsCompleted: []
inputDocuments:
  - _bmad-output/planning-artifacts/prd-draft.md
---

# avatar - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for `avatar`, decomposing the MVP requirements from the PRD into implementable stories. The sequence is intentionally narrow and follows the validated MVP path: enable one agency to launch one branded pilot client experience, run recurring content operations through a white-label portal, and measure pilot outcomes with a minimal validation stack.

## Requirements Inventory

### Functional Requirements

- FR1: Agency can brand its workspace with its own identity.
- FR2: System provides a client-facing portal under the agency brand.
- FR3: Delivery does not expose the platform as a third-party tool in the core client experience.
- FR4: System separates one agency's clients from another agency's clients.
- FR5: System supports role distinctions between agency operators and client viewers/requesters.
- FR6: Content calendar is the default operating screen for client delivery.
- FR7: System shows production status for current content items.
- FR8: Clients can request new content units.
- FR9: System exposes a library of reusable avatar assets.
- FR10: Agency teams can associate content items with target channels.
- FR11: Agency teams can mark deadlines or scheduled publishing windows.
- FR12: System exposes manually maintained KPI or result snapshots associated with published content.
- FR13: System supports pilot measurement for content-output throughput over a fixed time period.
- FR14: Agency teams can compare pilot output against a baseline or prior period.
- FR15: System distinguishes completed, in-progress, and upcoming work clearly for the client.
- FR16: Platform includes or supports deliverables templates for fast project setup.
- FR17: Platform supports a minimal onboarding kit for first agency launches.
- FR18: Platform supports a repeatable setup flow for a new pilot client.

### NonFunctional Requirements

- NFR1: Core calendar and portal views load fast enough for daily operational use.
- NFR2: MVP recurring workflows do not create blocking workflow friction for production teams.
- NFR3: Core workflows are simple enough to learn within a short agency onboarding window.
- NFR4: Client access is scoped so agencies can separate one client account from another.
- NFR5: Agency branding and client data remain isolated across accounts.
- NFR6: Architecture supports expansion from a single-channel pilot to broader recurring agency usage.
- NFR7: Product structure can add more agencies and clients without changing the core entity model.
- NFR8: Main portal views remain readable and usable for standard desktop workflows.
- NFR9: Future channel integrations can be added without redefining the core delivery model.

### Additional Requirements

- MVP is constrained to one agency-led pilot, one primary end-client segment, and one initial channel: `Instagram`.
- The launch motion is `bundled enhancement` inside `creative production / studio services`.
- KPI and results in MVP are manually maintained, not integration-derived.
- Multi-market localization, automated KPI ingestion, pricing-plan tooling, certification, and in-product case-study generation are explicitly deferred from MVP.

### FR Coverage Map

- FR1-FR5, FR16-FR18 -> Epic 1
- FR6-FR11, FR15 -> Epic 2
- FR12-FR14, FR19 -> Epic 3
- NFR1-NFR5 -> Epic 1 and Epic 2
- NFR6-NFR9 -> Epic 3, with architecture implications across all epics

## Epic List

### Epic 1: Agency Launch Foundation
Enable an agency Product Lead and delivery team to configure a branded pilot environment, onboard one client, and launch the service without custom operational setup.

### Epic 2: Client-Facing Recurring Content Operations
Enable the pilot client to experience the service as an ongoing branded system through a content calendar, production visibility, requests, and reusable content assets.

### Epic 3: Pilot Validation and Expansion Readiness
Enable the agency to record manual KPI evidence, compare pilot output to a baseline, and decide whether the pilot is strong enough to continue, renew, or scale.

### Epic 0: Foundation Setup
Establish the runnable monorepo, local environment, and CI quality gates required for reliable implementation of all user-facing epics.

## Foundation Setup Stories (Pre-Epic, required before 1.1)

These setup stories are mandatory for this greenfield implementation and must be completed before Epic 1 feature stories.

### Story 0.1: Initialize Monorepo and App Skeletons

As a developer,  
I want to bootstrap the repository structure and base apps,  
So that all feature work starts from a consistent, runnable baseline.

**Acceptance Criteria:**

**Given** an empty project workspace  
**When** setup starts  
**Then** the repository includes `apps/web`, `apps/api`, and `packages/contracts` baseline folders  
**And** both web and api services can start locally with placeholder health routes/pages.

**Given** the baseline scaffold exists  
**When** the team runs bootstrap commands  
**Then** dependency installation succeeds without manual patching  
**And** baseline scripts for lint/typecheck/test/build are available.

### Story 0.2: Configure Local Development Environment

As a developer,  
I want a standard local environment setup,  
So that every contributor can run the same stack reliably.

**Acceptance Criteria:**

**Given** the repo scaffold from Story 0.1  
**When** a new contributor follows setup docs  
**Then** they can run web, api, and database locally with one documented workflow  
**And** required environment variables are listed in `.env.example` files.

**Given** local services are running  
**When** health checks are executed  
**Then** app-level health endpoints and database connectivity checks pass  
**And** logs are readable with trace context.

### Story 0.3: Establish CI Quality Gates for Web/API/Contracts

As a team lead,  
I want baseline CI gates for all app surfaces,  
So that feature stories are built on a stable integration pipeline.

**Acceptance Criteria:**

**Given** repo and local setup are complete  
**When** a pull request is opened  
**Then** CI runs lint/typecheck/test/build for web and api  
**And** contract validation (OpenAPI/client sync check) runs as part of required checks.

**Given** CI gate failures occur  
**When** developers inspect the run  
**Then** failure output identifies the failing app/check clearly  
**And** merge blocking behavior is enforced until checks pass.

## Ready for Dev Pass

### Story Size Estimation

Size scale:
- `S` = usually fits one focused dev session
- `M` = likely 1-2 sessions
- `L` = likely needs split or multi-session execution

| Story | Size | Notes |
|---|---|---|
| 0.1 | M | Monorepo/app skeleton bootstrap and baseline scripts |
| 0.2 | S | Local env standardization and health checks |
| 0.3 | S | Baseline CI quality gates and contract checks |
| 1.1 | M | Branding plus consistent application in agency/client surfaces |
| 1.2 | S | Pilot client entity creation and setup state |
| 1.3 | M | Role assignment and access-scope enforcement |
| 1.4 | S | Guided setup flow definition for MVP |
| 1.5 | M | Template-based launch and usable delivery starting point |
| 2.1 | M | Content item CRUD fields plus schedule/channel/status behavior |
| 2.2 | M | Calendar default view and state rendering for client |
| 2.3 | M | Request capture and request visibility loop |
| 2.4 | S | Asset library linking and reuse behavior |
| 3.1 | M | Manual baseline/KPI capture model and editing path |
| 3.2 | S | Baseline comparison presentation |
| 3.3 | S | Continuation signal recording |
| 3.4 | S | Go/no-go summary view |

### Recommended Sprint 1 Execution Order

Goal: ship one thin end-to-end pilot path with minimum blockers.

1. `0.1` Initialize Monorepo and App Skeletons  
2. `0.2` Configure Local Development Environment  
3. `0.3` Establish CI Quality Gates for Web/API/Contracts  
4. `1.1` Create a Branded Agency Workspace  
5. `1.2` Add a Pilot Client Account  
6. `1.3` Assign Scoped Access Roles for Pilot Client  
7. `1.4` Define a Repeatable Pilot Client Setup Flow  
8. `1.5` Launch the Pilot from Deliverable Templates  
9. `2.1` Manage Recurring Content Items with Status, Channel, and Schedule  
10. `2.2` View the Branded Client Portal Through a Content Calendar  
11. `2.3` Submit and Track New Content Requests  
12. `2.4` Reuse Avatar Assets Across Pilot Content Work  
13. `3.1` Record Baseline and Manual KPI Snapshots for the Pilot  
14. `3.2` Compare Pilot Throughput Against the Baseline  
15. `3.3` Record Pilot Continuation Signals  
16. `3.4` Review a Pilot Go/No-Go Summary

### Delivery Guardrails

- Keep KPI and results manual in MVP; avoid accidental reporting-system expansion.
- Do not expand to localization or pricing-plan tooling in Sprint 1.
- If any `M` story grows during implementation, split by capability boundary before coding the second half.
- Preserve strict story order where access, data model, and client views depend on prior setup.

### Definition of Done (NFR Gate for Every Story)

- Performance: user-facing actions introduced by the story meet relevant p95 targets (or include measured baseline and follow-up task when not yet enforceable in isolation).
- Security: tenant and role scope checks are covered by tests for allow + deny paths.
- Accessibility: keyboard navigation, focus visibility, and contrast checks are verified for changed UI surfaces.
- Reliability: error states and loading states are implemented and testable.
- Contract integrity: API/schema changes include contract updates and consumer compatibility check.

## Dev-Task Breakdown for M Stories

### Story 1.1 - Create a Branded Agency Workspace (`M`)

- [ ] Define workspace branding domain model (name, logo, basic theme fields).
- [ ] Add API/handler for create/update branding settings.
- [ ] Implement agency-side branding settings UI.
- [ ] Apply branding tokens in agency workspace shell.
- [ ] Apply branding tokens in client-facing shell.
- [ ] Add fallback behavior when branding is incomplete (safe defaults).
- [ ] Add authorization checks so only agency admins can edit branding.
- [ ] Add tests for branding persistence and cross-surface rendering.

### Story 1.3 - Assign Scoped Access Roles for Pilot Client (`M`)

- [ ] Define role model for agency operator vs client viewer/requester.
- [ ] Add membership mapping between user, pilot client, and role.
- [ ] Implement role-assignment API/handler for pilot client context.
- [ ] Implement role-assignment UI in pilot client settings.
- [ ] Enforce role-based authorization on pilot client resources.
- [ ] Enforce tenant/client isolation guards in request middleware/policy layer.
- [ ] Add tests for positive access paths by role.
- [ ] Add tests for cross-client/cross-agency access denial.

### Story 1.5 - Launch the Pilot from Deliverable Templates (`M`)

- [ ] Define template schema for initial recurring service structure.
- [ ] Create seed template set for MVP pilot launch.
- [ ] Implement "apply template to pilot client" service/use case.
- [ ] Add launch action in UI for agency delivery lead.
- [ ] Ensure idempotent behavior (no duplicate structures on accidental re-run).
- [ ] Persist linkage between pilot client and applied template version.
- [ ] Add validation for required setup-state preconditions.
- [ ] Add tests for template application success and failure paths.

### Story 2.1 - Manage Recurring Content Items with Status, Channel, and Schedule (`M`)

- [ ] Define content-item model fields (status, channel, deadline/schedule window).
- [ ] Implement content-item create/update endpoints.
- [ ] Implement agency UI for create/edit content items.
- [ ] Add status transition rules for MVP states.
- [ ] Add channel assignment constraint (MVP includes Instagram path).
- [ ] Add date/time validation for deadlines and schedule windows.
- [ ] Surface content items in data layer consumed by calendar view.
- [ ] Add tests for CRUD, state transitions, and validation errors.

### Story 2.2 - View the Branded Client Portal Through a Content Calendar (`M`)

- [ ] Implement client portal entry route with default redirect to calendar.
- [ ] Build calendar view component for upcoming/in-progress/completed states.
- [ ] Map content-item data into calendar state buckets.
- [ ] Apply agency branding in portal header/navigation/calendar shell.
- [ ] Implement empty-state UX when no content items exist.
- [ ] Optimize calendar query to keep operational load acceptable.
- [ ] Add read-access enforcement for client scope only.
- [ ] Add tests for default landing behavior, state rendering, and access scope.

### Story 2.3 - Submit and Track New Content Requests (`M`)

- [ ] Define content-request model and relation to pilot client.
- [ ] Implement request submission endpoint/handler.
- [ ] Implement client-side request form in portal.
- [ ] Add agency-side list/view of incoming requests in pilot context.
- [ ] Link request records to recurring workflow context (not standalone notes).
- [ ] Show request visibility/status back to client in portal.
- [ ] Add validation (required fields, payload limits, sanitization).
- [ ] Add tests for request submission, persistence, visibility, and authz.

### Story 3.1 - Record Baseline and Manual KPI Snapshots for the Pilot (`M`)

- [ ] Define baseline and manual KPI snapshot data model for pilot context.
- [ ] Implement create/update endpoints for baseline and KPI entries.
- [ ] Implement Product Lead UI for entering/editing baseline values.
- [ ] Implement Product Lead UI for entering/editing manual KPI snapshots.
- [ ] Add clear labeling that values are manually entered in MVP.
- [ ] Persist audit metadata (who/when changed) for entries.
- [ ] Prevent dependency on external analytics integrations in this story.
- [ ] Add tests for manual entry flows, persistence, edit behavior, and visibility.

## Epic 1: Agency Launch Foundation

Enable an agency Product Lead and delivery team to configure a branded pilot environment, onboard one client, and launch the service without custom operational setup.

### Story 1.1: Create a Branded Agency Workspace

As an agency Product Lead,  
I want to configure a branded agency workspace,  
So that the service feels like part of my agency's own offering.

**Acceptance Criteria:**

**Given** an authenticated agency admin  
**When** they create or edit their workspace branding  
**Then** they can set agency name, logo, and basic visual identity  
**And** the branded identity is applied consistently in agency-facing screens.

**Given** a branded workspace exists  
**When** the agency team accesses the client-facing area  
**Then** the client experience reflects agency branding rather than a third-party product brand  
**And** no default platform branding is shown in core pilot flows.

### Story 1.2: Add a Pilot Client Account

As an agency operator,  
I want to create one pilot client account,  
So that I can onboard a real pilot customer inside my agency workspace.

**Acceptance Criteria:**

**Given** an agency workspace exists  
**When** the operator adds a pilot client  
**Then** the client is associated only with that agency workspace  
**And** the client can be managed independently from other clients in that workspace.

**Given** the pilot client is created  
**When** the operator reviews pilot client settings  
**Then** the client is marked as available for access setup  
**And** the setup state is ready for role assignment in a follow-up step.

### Story 1.3: Assign Scoped Access Roles for Pilot Client

As an agency operator,  
I want to assign scoped roles for the pilot client,  
So that agency and client responsibilities are separated securely.

**Acceptance Criteria:**

**Given** a pilot client account exists  
**When** the operator assigns access roles  
**Then** agency users and client users have distinct role types  
**And** role assignment is stored for that pilot client context.

**Given** client users have been assigned  
**When** they access the pilot experience  
**Then** they can only view or request content for their own pilot account  
**And** they cannot access data belonging to other clients or agencies.

### Story 1.4: Define a Repeatable Pilot Client Setup Flow

As an agency Product Lead,  
I want a repeatable pilot setup flow,  
So that I can launch a new pilot client without reinventing the process each time.

**Acceptance Criteria:**

**Given** a pilot client has been created  
**When** the operator starts client setup  
**Then** the system guides them through the minimum required setup steps for the pilot  
**And** the flow covers branding readiness, client access readiness, and the minimum information required before delivery setup begins.

**Given** the setup flow is completed  
**When** the agency reviews the pilot client  
**Then** the client is marked ready for pilot delivery setup  
**And** the same setup flow can be repeated for future pilot clients.

### Story 1.5: Launch the Pilot from Deliverable Templates

As an agency delivery lead,  
I want to start the pilot using built-in templates,  
So that I can begin delivery quickly without building the service structure from scratch.

**Acceptance Criteria:**

**Given** a pilot client is ready  
**When** the agency starts a new pilot from templates  
**Then** the system provides predefined deliverable structure for the initial recurring service  
**And** the team can use that structure without custom manual setup.

**Given** templates are applied  
**When** the pilot workspace is reviewed  
**Then** the team has a usable starting point for recurring content planning and delivery  
**And** the workspace is ready for the first content items to be added.

## Epic 2: Client-Facing Recurring Content Operations

Enable the pilot client to experience the service as an ongoing branded system through a content calendar, production visibility, requests, and reusable content assets.

### Story 2.1: Manage Recurring Content Items with Status, Channel, and Schedule

As an agency operator,  
I want to manage recurring content items with status, channel, and schedule data,  
So that the client sees an operational system rather than disconnected deliverables.

**Acceptance Criteria:**

**Given** the pilot workspace is active  
**When** the agency creates or updates a content item  
**Then** the item includes a production status  
**And** the item can be associated with a target channel such as Instagram.

**Given** a content item exists  
**When** the agency sets timing information  
**Then** the item can include a deadline or scheduled publishing window  
**And** the content calendar reflects that timing.

### Story 2.2: View the Branded Client Portal Through a Content Calendar

As a pilot client,  
I want the content calendar to be my default portal view,  
So that I can understand the ongoing flow of planned and active work.

**Acceptance Criteria:**

**Given** the pilot client signs into the portal  
**When** they land on the main portal view  
**Then** the default screen is the content calendar  
**And** the calendar clearly reflects the agency's branding.

**Given** there are content items in the pilot  
**When** the client reviews the calendar  
**Then** they can distinguish upcoming, in-progress, and completed work  
**And** the view is readable for standard desktop use.

### Story 2.3: Submit and Track New Content Requests

As a pilot client,  
I want to request new content units from inside the portal,  
So that the recurring service feels active and operationally convenient.

**Acceptance Criteria:**

**Given** the client is in the portal  
**When** they submit a new content request  
**Then** the request is captured inside the pilot workspace  
**And** the agency can act on it without leaving the product workflow.

**Given** a request has been submitted  
**When** the client returns to the portal  
**Then** they can see that the request exists in the current operating context  
**And** it is connected to the broader recurring service rather than hidden in side communication.

### Story 2.4: Reuse Avatar Assets Across Pilot Content Work

As an agency operator,  
I want a reusable avatar asset library connected to content items,  
So that I can scale recurring delivery without recreating core assets each time.

**Acceptance Criteria:**

**Given** the pilot workspace is active  
**When** the agency adds avatar assets to the library  
**Then** those assets are stored in a reusable library for the pilot  
**And** the team can associate them with content items.

**Given** content items use shared avatar assets  
**When** the agency links those assets to content items  
**Then** linked assets are visible in the corresponding item context  
**And** the same asset can be reused across multiple content items without duplication.

## Epic 3: Pilot Validation and Expansion Readiness

Enable the agency to record manual KPI evidence, compare pilot output to a baseline, and decide whether the pilot is strong enough to continue, renew, or scale.

### Story 3.1: Record Baseline and Manual KPI Snapshots for the Pilot

As an agency Product Lead,  
I want to record a baseline and manual KPI snapshots for the pilot,  
So that I can evaluate whether the service is creating operational and product value.

**Acceptance Criteria:**

**Given** a pilot client has been launched  
**When** the agency defines the pilot baseline  
**Then** the system stores a baseline for throughput comparison  
**And** the baseline is tied to the pilot client context.

**Given** pilot delivery is underway  
**When** the agency records KPI or result snapshots  
**Then** those values can be entered manually  
**And** they are visible in the pilot context without requiring external integrations or automated ingestion.

**Given** KPI snapshots are recorded  
**When** the Product Lead edits or saves the baseline/KPI entries  
**Then** only manual values are expected in MVP  
**And** no advanced reporting logic is required for story completion.

### Story 3.2: Compare Pilot Throughput Against the Baseline

As an agency Product Lead,  
I want to compare pilot output against a baseline period,  
So that I can determine whether the pilot improves production throughput.

**Acceptance Criteria:**

**Given** baseline and pilot period data exist  
**When** the agency reviews pilot performance  
**Then** the system shows whether more content units were produced in the same time period  
**And** the comparison is easy to understand without additional calculation.

**Given** pilot throughput is being reviewed  
**When** the agency examines the results  
**Then** the output comparison is presented within the pilot workflow  
**And** it can be used as part of the pilot go/no-go decision.

### Story 3.3: Record Pilot Continuation Signals

As an agency Product Lead,  
I want to record whether the client continues to use and value the service,  
So that I can judge whether the pilot should be renewed, expanded, or stopped.

**Acceptance Criteria:**

**Given** the pilot has produced usage and outcome observations  
**When** the agency evaluates the pilot  
**Then** it can record whether the client is actively using the portal as an operating surface  
**And** it can record whether the client continues, renews, or expands after the pilot.

**Given** continuation signals have been recorded  
**When** the Product Lead saves the evaluation  
**Then** the operational, product, and commercial signals are stored in the pilot context  
**And** they remain available for later decision review.

### Story 3.4: Review a Pilot Go/No-Go Summary

As an agency Product Lead,  
I want to review a single pilot summary,  
So that I can decide whether the pilot is ready for broader rollout.

**Acceptance Criteria:**

**Given** baseline comparison and continuation signals have been recorded  
**When** the Product Lead reviews the pilot summary  
**Then** the summary includes operational, product, and commercial validation signals  
**And** it supports a decision on whether the pilot is ready for broader rollout.
