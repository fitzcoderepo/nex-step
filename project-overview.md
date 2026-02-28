# NexStep — Project Overview

## What Is This Project?

NexStep is a standalone, embeddable decision tree engine that allows businesses to build and deliver interactive, branching flows to their customers or internal teams. While the initial use case is customer-facing troubleshooting guides, the underlying engine is designed to power any sequential, decision-based process — support guides, manufacturing work orders, onboarding checklists, compliance workflows, and more.

Rather than presenting users with static FAQs or walls of documentation, NexStep walks them through a guided, branching experience where their responses at each step determine what comes next.

The tool is designed to be stack-agnostic — businesses do not need to be running any particular framework or backend to use it. They log into a hosted dashboard to build and manage their flows, then embed the end-user experience on their own site with a single script tag.

---

## Core Concepts

**Flow** — A complete decision tree, made up of interconnected nodes. A flow starts at a single root node and branches outward based on user choices. Flows are flexible enough to represent a troubleshooting guide, a work order, an onboarding checklist, or any other sequential branching process.

**Node** — The fundamental unit of a flow. Each node represents a single step: an info display, a question, a troubleshooting instruction, a resolution, or an escalation.

**Option / Choice** — The selectable responses attached to a node. Each option points to the next node it leads to, forming the branches of the tree.

**Resolution** — A terminal node that ends the flow, either because the issue is resolved, the task is complete, or the user needs to be escalated further.

---

## Tech Stack

### Backend
- **Django** — Core application framework, data models, authentication, and multi-tenancy
- **Django REST Framework** — API layer serving flow data to the authoring dashboard and embeddable widget
- **Apps:** `accounts` (users, businesses, invites), `flows` (flows, nodes, options, media)

### Authoring Dashboard (hosted web UI)
- **Next.js** — React-based frontend framework handling routing, server-side rendering, and component architecture
- **Tailwind CSS** — Utility-first styling for a clean, consistent UI
- **React Flow** — Purpose-built library for the visual node-based tree editor, handling canvas rendering, node/edge connections, and interactive authoring
- **TipTap** — Rich text editor for node content, supporting font, size, indentation, bullets, and other formatting tools

### Embeddable Widget (end-user facing)
- **Vanilla JavaScript** — Lightweight, dependency-free script bundled separately from the dashboard that businesses embed on their site with a single script tag
- Communicates with the Django REST API to fetch and render the appropriate flow
- Bundled independently using a tool like **tsup** or a custom webpack config to keep the widget footprint small

---

## How It Will Be Delivered

The project is delivered as a **hosted SaaS-style service** with three distinct touchpoints:

1. **Authoring Dashboard** — A web application hosted on your service. Business authors log in here to create, edit, and publish their flows. No installation required on their end.

2. **REST API** — The backbone of the service. Serves flow data to the embeddable widget and handles all business logic, authentication, and content management.

3. **Embeddable Widget** — A small JavaScript file businesses include on their own website with a single `<script>` tag. The widget handles rendering the flow experience for their end users and communicates with the API. Compatible with any website or web application regardless of the technology stack it runs on.

---

## Core Product Principle

**For NexStep to sell to businesses, it has to work for their customers.**

Businesses are NexStep's customers, but their customers are NexStep's users. If the end-user experience fails, businesses don't get the results they paid for — and they churn. This means NexStep isn't just a tool for building decision trees easily. It's a tool designed to help businesses build decision trees that *actually work*, with guardrails, best practice guidance, and feedback mechanisms baked into the authoring experience itself.

---

## Authoring Experience

The authoring dashboard will feature a **visual tree editor** built with React Flow. Key characteristics:

- Authors see their entire flow laid out as a graphical canvas with nodes and connecting edges
- Each node is represented as a card showing a preview of its content and type
- Clicking a node opens an editing panel for updating content and managing outgoing options
- Node content is edited using TipTap, supporting rich text formatting including font, size, indentation, and bullets
- Node status indicators (e.g. complete, incomplete, dead end) allow authors to audit the flow at a glance
- Orphaned nodes and dead ends are surfaced visually to prevent broken flow experiences
- Flows can be saved as **draft** or **published**, preventing unfinished changes from going live
- **Preview mode** allows authors to walk through their flow as an end user would before publishing, surfacing friction points before they go live
- **Authoring warnings** flag potential problems such as branches with no resolution path, dead ends without a next step, or unusually deep branches — helping businesses build flows that work without being overly restrictive
- **Analytics** (longer term) surface data like drop-off rates per node and resolution rates per flow, giving businesses actionable feedback to continuously improve their content

---

## Data Models

### ✅ Completed

#### `accounts` app

**`Business`**
- UUID primary key
- `name` — business name
- `api_key` — auto-generated on creation using `secrets.token_urlsafe(48)`, unique
- `max_users` — capped at 10 by default
- `max_admins` — capped at 2 by default
- Helper properties: `owner`, `admin_count`, `user_count`, `can_add_user`, `can_add_admin`
- Timestamps: `created_at`, `updated_at`

**`User`** (custom user model, email-based login)
- UUID primary key
- `business` — FK to Business
- `email` — used as the login identifier
- `full_name`
- `role` — choices: `owner`, `admin`, `author`
- `is_active`, `is_staff`
- Helper properties: `can_publish` (owner and admin only), `can_manage_users` (owner and admin only)
- Timestamps: `created_at`, `updated_at`

**`Invite`**
- UUID primary key
- `business` — FK to Business
- `invited_by` — FK to User
- `email` — invitee's email address
- `role` — choices: `admin`, `author` (owner role cannot be invited)
- `token` — UUID used to generate the invite link
- `accepted` — boolean, defaults to False
- `expires_at` — invite expiry datetime
- Unique together: `business` + `email`
- Timestamps: `created_at`

#### `flows` app

**`Flow`**
- UUID primary key
- `business` — FK to Business
- `name`, `description`
- `status` — choices: `draft`, `published`
- `root_node` — OneToOne FK to Node (the entry point of the flow)
- `published_by` — FK to User
- `published_at` — datetime of publication
- `created_by` — FK to User
- Timestamps: `created_at`, `updated_at`

**`Node`**
- UUID primary key
- `flow` — FK to Flow
- `node_type` — choices: `info`, `question`, `instruction`, `resolution`, `escalation`
- `title` — optional short label
- `content` — TextField storing rich text HTML (authored via TipTap)
- `order` — for display sequencing
- Helper properties: `is_terminal` (true for resolution and escalation), `has_options`
- Timestamps: `created_at`, `updated_at`

**`Option`**
- UUID primary key
- `node` — FK to Node (the node this option belongs to)
- `next_node` — FK to Node (the node this option leads to, SET_NULL on delete to avoid cascading)
- `label` — the text the user sees on the button/choice
- `order` — for display sequencing
- Timestamps: `created_at`, `updated_at`

**`NodeMedia`**
- UUID primary key
- `node` — FK to Node
- `media_type` — choices: `image`, `video`, `file`
- `file` — FileField for locally stored uploads (swappable to cloud storage via django-storages)
- `url` — URLField for externally hosted media (e.g. YouTube links)
- `caption` — optional descriptive text
- `order` — for display sequencing
- Validation: must have either `file` or `url`, never both and never neither
- Timestamps: `created_at`

---

## Next Steps

### 2. API Structure
Design the REST API endpoints. Areas to cover:
- Authentication (API keys for widget requests, session auth for the dashboard)
- Endpoints for fetching a published flow by ID
- Endpoints for fetching a single node by ID (for step-by-step traversal)
- CRUD endpoints for the authoring dashboard (flows, nodes, options)
- Multi-tenancy — ensuring businesses can only access their own content

### 3. Multi-Tenancy Design
Decide how business data is isolated:
- Shared database with tenant foreign keys on every model (already in place)
- How API keys are scoped to a specific business/tenant

### 4. Authoring Dashboard Wireframes
Before writing frontend code, sketch the key screens:
- Login / account management
- Flow list view (all flows for a business)
- Visual tree editor canvas
- Node editing panel
- Flow settings (name, status, publish/draft toggle)

### 5. Embeddable Widget Design
Plan the widget's behavior and API contract:
- How the widget is initialized (script tag + config object with API key and flow ID)
- How it fetches and renders nodes
- How user choices are captured and the next node is requested
- Styling / theming options for businesses to match their branding

### 6. Project Scaffold
Set up the initial Django project structure:
- Django project with REST Framework configured ✅
- Initial app structure (`flows`, `accounts`) ✅
- Basic authentication scaffolding
- Frontend asset organization for the dashboard and widget separately

---

## Open Questions

- Should the widget support theming/customization options out of the box, and if so, how configurable should it be?
- Should there be usage analytics — e.g. tracking which paths users take through a flow, drop-off points, resolution rates?
- What does the escalation path look like when a flow can't resolve an issue — email handoff, link to a support form, or something else?
- Should businesses be able to have multiple flows organized into categories or collections?
