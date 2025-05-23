# Fine-Grained ACL Architecture for AI-Served Documents

## 1. Introduction: The ACL Challenge for AI Document Serving

Our AI agent serves documents, and a critical requirement is to ensure users only access information they are authorized to view. Access Control Lists (ACLs) for these documents are dynamic, with permissions potentially changing frequently. This dynamism precludes aggressive caching of ACL data itself for authorization decisions.

When the AI agent receives a request related to a document, it must consult an ACL system to verify the requesting user's permissions. This check must be performed with low latency to maintain a responsive user experience, as it lies in the critical path for generating answers.

This document evaluates three architectural approaches for implementing and enforcing these fine-grained ACLs. A key consideration throughout this evaluation is the argument against building custom ACL logic when robust open-source solutions are readily available.

We will evaluate:

1.  ACLs managed and checked via BigQuery.
2.  ACLs managed and checked via PostgreSQL or Cloud Spanner.
3.  ACLs managed and checked via a specialized tool (e.g., OpenFGA), backed by PostgreSQL or Cloud Spanner.

---

## Why Specialized ACL Tools Often Outweigh Custom Solutions

While developing custom solutions is often feasible, implementing fine-grained, dynamic access control can introduce significant complexity and long-term maintenance burdens. Before "rolling your own" ACL logic, it's crucial to consider that specialized, battle-tested open-source tools exist. These tools are designed to handle the intricacies of authorization, potentially saving considerable development effort and reducing the risk of security flaws.

Let's explore the architectural options considered:

---

## 2. Architectural Approaches

### 2.1. Approach 1: ACL Access via BigQuery

**Description:**
In this model, ACL information (e.g., `user_id`, `document_id`, `permission_type`, `group_id`, `role`) would be stored in BigQuery tables. The AI agent would construct and execute SQL queries against BigQuery for authorization checks.

**Example Table Structure (Simplified):**

```sql
-- document_permissions (user_id STRING, document_id STRING, permission STRING)
-- group_memberships (user_id STRING, group_id STRING)
-- group_permissions (group_id STRING, document_id STRING, permission STRING)
```

**Potential Advantages:**

- **Scalability for Data Storage:** BigQuery can store massive amounts of ACL data.
- **Leverage Existing Infrastructure:** If BigQuery is already a core part of the data stack, tooling and expertise may exist.
- **Powerful Analytics:** Suitable for complex analytical queries on ACL data for auditing (though not the primary use case for real-time checks).

**Disadvantages for Real-time ACL Checks:**

- **High Latency for Point Lookups:** BigQuery is optimized for analytical queries over large datasets, not for low-latency point lookups required for real-time authorization.
- **Expensive for Real-time Checks:** BigQuery's pricing (based on bytes processed) can lead to high costs with frequent ACL checks, especially those involving joins.
- **Not Designed for Transactional Workloads:** Updating individual ACLs is less efficient compared to transactional databases.
- **No Caching of ACL Tables:** Given the dynamic nature of ACLs, caching permission tables is not feasible, meaning each check incurs full query cost and latency.
- **Complexity for Rich ACL Models:** Implementing hierarchical or attribute-based permissions can result in highly complex and potentially slow SQL queries.

**Conclusion for Approach 1:** Not recommended for this use case due to latency, cost, and operational characteristics for real-time checks.

### 2.2. Approach 2: ACL Access via PostgreSQL or Cloud Spanner (Direct)

**Description:**
ACL data would be stored in a relational database like PostgreSQL or Cloud Spanner. The AI agent would query this database using standard SQL to verify permissions.

**Example Table Structure (RDBMS with Indexes):**

```sql
-- document_permissions (user_id UUID, document_id UUID, permission VARCHAR(50), PRIMARY KEY (user_id, document_id, permission))
-- group_memberships (user_id UUID, group_id UUID, PRIMARY KEY (user_id, group_id))
-- (Indexes on foreign keys and frequently queried columns are critical.)
```

**Advantages over BigQuery for this Use Case:**

- **Faster Lookups:** Relational databases with proper indexing are optimized for low-latency point lookups and transactional workloads.
- **Cost-Effective for Lookups:** Pricing (typically instance-based) is generally more predictable and cost-effective for frequent, small queries.
- **Mature Technology:** Well-understood, with robust tooling and client libraries.
- **Transactional Integrity:** ACID properties ensure consistency when updating ACLs.
- **Cloud Spanner Advantages:** Offers horizontal scalability, strong global consistency, and high availability if required.

**However, this approach has notable drawbacks:**

- **Complexity for Rich ACL Models (in SQL):** While faster than BigQuery, modeling and querying complex ACL scenarios (e.g., deep hierarchies, conditional access based on multiple attributes or inherited group memberships) can still lead to intricate and difficult-to-maintain SQL (e.g., recursive CTEs, multiple JOINs). Performance can also degrade with query complexity.
- **Application-Level Logic Overhead:** A significant amount of authorization logic might need to be implemented and maintained within the application or as complex stored procedures. This intertwines authorization logic with business logic, reducing modularity.
- **Scalability of Complex Queries:** While the database itself can scale, the performance of highly complex ACL evaluation queries might not scale linearly.
- **Schema Management Overhead:** Changes to the ACL model (e.g., adding new relationship types or attributes) require schema migrations and careful management.

**Conclusion for Approach 2:** A viable alternative, but with caveats. If the ACL model is relatively simple and not expected to evolve significantly, this can be a solution. However, as complexity grows, so does the burden of managing ACL logic in SQL and application code, effectively requiring the development of a custom, and potentially less robust, authorization system.

---

### 2.3. Approach 3: Specialized Tool (e.g., OpenFGA) backed by PostgreSQL/Spanner

**Description:**
This approach involves using a dedicated authorization service like [OpenFGA](https://openfga.dev/) (an open-source implementation of Google's Zanzibar).

1.  **Model Definition:** An authorization model is defined using OpenFGA's Domain Specific Language (DSL). This model describes object types (e.g., document, folder), relations (e.g., viewer, editor, parent, member), and how these relations grant permissions.
2.  **Tuple Storage:** Relationship tuples (e.g., "user:alice is a viewer of document:report123") are stored in OpenFGA. OpenFGA uses a backend datastore, which can be PostgreSQL or Cloud Spanner.
3.  **Authorization Check:** The AI agent makes a simple API call to the OpenFGA service (e.g., "Can user:alice view document:report123?"). OpenFGA resolves this request based on the defined model and stored tuples, performing efficient graph traversal.

**Key Advantages:**

- **Optimized Performance:** Leverages the fast lookup capabilities of its backend (PostgreSQL/Spanner) for storing tuples. OpenFGA is specifically optimized for low-latency authorization checks, often outperforming handwritten complex SQL for equivalent checks.
- **Robust Support for Complex Authorization Models:** Natively supports Role-Based Access Control (RBAC), Attribute-Based Access Control (ABAC), and especially Relationship-Based Access Control (ReBAC). Hierarchies, group memberships, and indirect permissions are handled effectively. The model is explicit and auditable.
- **Decoupling & Centralization:** Authorization logic is decoupled from the AI agent's core business logic and centralized in the OpenFGA service, leading to cleaner application code.
- **Reduced Development Effort for ACL Logic:** Developers define the authorization model and write relationship tuples, rather than implementing complex SQL queries or application logic for permission checks.
- **Standardization & Interoperability:** Employs a standardized approach to authorization, with SDKs available for various languages.
- **Improved Evolvability:** Easier to evolve the authorization model without requiring extensive rewrites of application code.
- **Enhanced Auditability:** Features like "ListObjects" and "Expand" APIs can help determine _why_ a user has (or does not have) access to a resource.

**Considerations:**

- **New System Component:** Introduces an additional service (OpenFGA server) to deploy, manage, monitor, and scale.
- **Learning Curve:** Developers need to learn OpenFGA's modeling language and concepts, though it is generally considered intuitive for its purpose.
- **Data Synchronization:** While OpenFGA stores relationship tuples, the entities themselves (users, documents) might originate elsewhere. A strategy for ensuring consistency or hydrating OpenFGA with relevant relationship data is necessary. (Applications typically write tuples to OpenFGA as relationships are formed or modified).
- **Dependency on Backend Datastore:** Reliant on the chosen backend (PostgreSQL/Spanner) for performance, scalability, and reliability of tuple storage.

**Conclusion for Approach 3:** Highly recommended. This approach offers the best combination of performance, flexibility, and maintainability for complex, fine-grained ACLs.

---

## 3. Comparative Summary

| Feature                  | BigQuery                       | PostgreSQL/Spanner (Direct)      | OpenFGA (backed by PSQL/Spanner)         |
| :----------------------- | :----------------------------- | :------------------------------- | :--------------------------------------- |
| **Check Latency**        | High                           | Low to Medium                    | Very Low to Low                          |
| **Cost (Frequent Ops)**  | High (per-byte scanned)        | Medium (instance/IOPS based)     | Medium (instance/IOPS + OpenFGA)         |
| **Model Flexibility**    | Low (complex SQL for models)   | Low (complex SQL for models)     | High (DSL designed for rich models)      |
| **Dev Effort (ACLs)**    | Potentially High (complex SQL) | Medium to High (SQL/app logic)   | Low (model definition, tuple writing)    |
| **Ops Overhead**         | Medium (if already using BQ)   | Medium                           | Medium to High (new component + backend) |
| **Scalability (Checks)** | Poor for real-time             | Good (complex queries can limit) | Excellent                                |
| **Caching ACL Tables**   | Not feasible (dynamic ACLs)    | Not feasible (dynamic ACLs)      | Optimized caching within OpenFGA server  |
| **Ease of Audit**        | SQL queries                    | SQL queries                      | Built-in APIs (ListObjects, Expand)      |

---

## 4. Recommendation

Considering the requirements for fine-grained ACLs, dynamic updates, low-latency checks, and future flexibility, **Option 3 (OpenFGA backed by PostgreSQL/Spanner) is the recommended approach.**

This approach offers the best balance of:

- **Performance:** Leverages efficient underlying datastores and specialized authorization logic.
- **Flexibility:** Natively supports diverse and evolving access control patterns (RBAC, ABAC, ReBAC), which is a significant advantage for future-proofing the system.
- **Maintainability:** Decouples authorization logic from core application code and centralizes it within a dedicated service.

OpenFGA is designed for real-time checks against its current tuple set, which can be updated frequently, effectively addressing the "dynamic ACLs" requirement.

**Regarding other options:**

- **Option 2 (PostgreSQL/Cloud Spanner Direct):** A viable alternative. This is a significant improvement over BigQuery. If the ACL model is relatively simple and not expected to become overly complex, this can be a good solution. However, as complexity grows, so does the burden of managing ACL logic in SQL and application code, potentially leading to the development of a less robust or more error-prone custom solution compared to what OpenFGA provides.
- **Option 1 (BigQuery):** Not recommended for this use case. BigQuery's latency and cost model make it unsuitable for real-time, frequent ACL checks where ACL data itself cannot be cached.

Utilizing specialized tools like OpenFGA can prevent the significant overhead and potential pitfalls associated with developing and maintaining complex, custom ACL solutions, allowing development teams to focus on core business logic.

```

```
