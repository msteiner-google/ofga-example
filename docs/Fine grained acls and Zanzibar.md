This document provides an overview of Fine-Grained Access Control Lists (ACLs) and explains the
core concepts behind Google's Zanzibar, our tool to handle that.

### 1. What are Fine-Grained ACLs?

**Access Control Lists (ACLs)** are lists of permissions attached to an object. They specify which
users or system processes are granted access to objects, as well as what operations are allowed on given objects.

**Fine-Grained ACLs** take this concept further by allowing for highly specific and nuanced
permissioning. Instead of broad roles (e.g., "admin," "user"), fine-grained ACLs allow you to
define permissions at a very detailed level, often involving relationships between objects and subjects.

**Key characteristics of Fine-Grained ACLs:**

- **Specificity:** Permissions can be defined for individual resources, parts of resources, or
  specific actions on those resources.
  - _Example:_ User Alice can `edit` `document:budget_q4` but only `comment`
    on `document:project_plan`.
- **Relationship-Based:** Access can depend on relationships between users and objects, or
  even objects and other objects.
  - _Example:_ A user can `view` a photo if they are in the `group` that `owns` the `album`
    containing the photo.
- **Scalability Challenge:** Implementing and managing fine-grained ACLs at scale is complex,
  requiring efficient storage, quick evaluation, and consistency.

**Why are they important?**
Modern applications often require complex sharing models (e.g., Google Docs, GitHub repositories,
SaaS platforms with team features). Coarse-grained access control (e.g., RBAC with a few predefined roles)
is often insufficient to model these rich permissioning requirements.
Fine-grained ACLs provide the necessary flexibility and security.

### 2. Introducing Zanzibar: Google's Solution

Zanzibar is Google's global authorization system. It's designed to handle fine-grained access
control for billions of objects and trillions of ACLs across many Google services (like YouTube,
Drive, Calendar, Cloud).

**Key Design Goals & Achievements of Zanzibar:**

- **Scalability:** Handles immense scale in terms of objects, users, and relationships.
- **Low Latency:** Authorization checks must be extremely fast to not impact user experience.
- **High Availability:** The system must be fault-tolerant and always available.
- **Flexibility:** Supports a wide range of access control policies through a configurable namespace model.
- **Strong Consistency (External Consistency):** Ensures that permission changes are reflected
  globally in a consistent manner, preventing stale reads that could lead to incorrect access
  decisions.

### 3. Core Concepts of Zanzibar

Zanzibar's power comes from a few core concepts:

**a. Relationship Tuples (ACLs):**
The fundamental unit of data in Zanzibar is a "relationship tuple" (or simply "tuple"). It
represents a single piece of access control information in the format:

`object#relation@user`

- **`object`**: The resource being protected. It's represented as `namespace:object_id`.
  - _Example:_ `doc:document123`, `folder:folder_xyz`
- **`relation`**: The relationship the `user` has with the `object`.
  - _Example:_ `owner`, `editor`, `viewer`, `member`
- **`user`**: The subject seeking access. This can be:
  - A direct user ID: `user:alice@example.com`
  - A "userset": `object#relation` (e.g., `group:engineering#member`). This means any user who has
    the `member` relation on the `group:engineering` object. This allows for powerful indirect and
    recursive definitions.
  - A public wildcard (e.g. `*` for all users, or `*@type` for all users of a certain type).

**Examples of Tuples:**

- `doc:budget_q4#editor@user:bob@example.com` (Bob is an editor of doc:budget_q4)
- `doc:budget_q4#viewer@group:finance_team#member` (Any member of the finance_team group is a
  viewer of doc:budget_q4)
- `folder:reports#parent@doc:budget_q4` (doc:budget_q4 is a child of folder:reports - this is an
  object-to-object relationship used for inheritance)

### 4. How Zanzibar Works (High-Level Flow for a Check)

1.  **Client Request:** An application service (e.g., Google Drive) needs to authorize an action.
    It sends a `Check(user:alice, relation:view, object:doc:mydoc)` request to Zanzibar.
2.  **Zanzibar Server:**
    - Parses the request.
    - Retrieves the configuration for `doc`.
    - Evaluates the `view` relation for `doc:mydoc` according to the rules in the config:
      - Does `user:alice` have a direct `doc:mydoc#view@user:alice` tuple?
      - Is `view` defined as `editor + direct_viewer`? If so, check if `user:alice` is an `editor`
        or a `direct_viewer`. This check is recursive.
      - Does the `doc` inherit permissions from a parent `folder`? If so, check if `user:alice` has
        `view` permission on the parent `folder`. This involves another recursive) check.
3.  **Data Storage:** Tuples are stored in a relational database (like Google's Spanner) optimized
    for low-latency reads and strong consistency.
4.  **Response:** Zanzibar returns `true` or `false`.

The evaluation can be visualized as a graph traversal. Zanzibar employs various optimizations
(caching, batching, parallel lookups) to ensure low latency.

### 5. Why is Zanzibar Significant?

- **Proven at Scale:** It demonstrates that fine-grained, globally consistent authorization is
  achievable at massive scale.
- **Influential Design:** The Zanzibar paper (OSDI 2019) has become highly influential, inspiring
  open-source implementations and commercial products like OpenFGA, Authzed SpiceDB, Ory Keto, and
  others. These systems adopt similar concepts of relationship tuples and schema-defined rewrites.
- **Decoupling:** It decouples authorization logic from application business logic, leading to
  cleaner, more maintainable services.
