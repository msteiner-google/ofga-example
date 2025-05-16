<!--
With tabular data things differ slightly.

In fact for each table there could be a lot of rows and our goal is to minimize the number
of `tuples` we insert in OpenFGA according to our own.

Additionally, while for documents we could interrogate our ACL server for each document retrieved,
this is not possible with tabular data. This is because the set of documents we need to investigate
in a RAG context is `O(10s)`, while a table can have `0(millions)` rows.

Therefore, the methods use will change. Instead of retrieving the set of documents through RAG
and then further filter based on ACLs, the ACL system helps us constructing the query. Specifically
the `WHERE` clause of the query.

```sql
SELECT entry.important_values
FROM table AS entry
WHERE entry.id IN ("results", "from", "ACL", "here")
-- entry.id NOT IN (...) also works, more on that later.
```

Basically, we are not asking _"can the user read rows 1,2,3,..."_, but, instead,
_"which rows can the user see?"_ or _"which rows the user can't read?"_.

OpenFGA offers an [API](https://openfga.dev/docs/concepts#what-is-a-list-objects-request) exactly for this.
This method returns the objects of a particular type the the user has a relationship with.

## Using `IN (...)` vs `NOT IN (...)`

This is a subject that goes a bit by taste and if you want to use both
depending on the table your clients need to be aware.

I call these two ways of doing things **explicit** and **implicit** permissions respectively.
The first answers the question "Which rows can the user see", the second
"Since the user can see most of the rows, which one he/she is forbidden to see?"

In case, I provided here a suggestion on how to model the authorization for tabular data:

![decison_tree](./imgs/decision_tree_tabular.svg)
[1] A yes in this case means that the table resemble an HR table, where each user can see its own row
and potentially few others (like a manager being able to see his/her reportee data).
A no, instead, is a table that contain financial data. Only few rows of such tables must be
guarded. Continuing with the financial metaphor, only the current quarter data access is
restricted due to regulatory reasons (i.e. avoid insider trading).
-->

## Fine-Grained Access Control for Tabular Data with OpenFGA

Applying fine-grained access control to tabular data presents unique challenges compared to individual documents or resources. This guide explores how OpenFGA can be leveraged to efficiently manage permissions at the row level.

### The Challenge: Scaling ACL Checks for Large Tables

When dealing with documents in a system like a Retrieval Augmented Generation (RAG) pipeline, it's often feasible to first retrieve a small set of candidate documents (e.g., `O(10s)`) and then check permissions for each one against an ACL server.

However, this approach doesn't scale for tabular data. A single table can easily contain millions of rows (`O(millions)`). Performing an individual permission check for each row before displaying it to a user would be prohibitively slow and resource-intensive.

Our goal is also to be mindful of the OpenFGA model itself. We aim to minimize the number of relationship `tuples` (e.g., `user:anne can_read report:Q4_financials`) we need to define and store in OpenFGA, optimizing both performance and manageability of the authorization model.

### The Solution: ACL-Driven Query Modification

Instead of asking "Can the user access row X, row Y, row Z...?" for potentially millions of rows, we shift the paradigm. The ACL system helps us answer:

1.  **"Which specific rows _can_ the user access?"**
2.  **"Which specific rows is the user _forbidden_ from accessing?"** (implying they can access most others)

The answers to these questions allow us to directly modify the database query, typically by injecting conditions into the `WHERE` clause.

```sql
-- Scenario 1: User can only see specific rows
SELECT entry.important_values
FROM table AS entry
WHERE entry.id IN ('id_1', 'id_2', 'id_3'); -- IDs provided by OpenFGA

-- Scenario 2: User is denied access to specific rows
SELECT entry.important_values
FROM table AS entry
WHERE entry.id NOT IN ('id_x', 'id_y', 'id_z'); -- IDs provided by OpenFGA
```

This strategy pre-filters data at the source, ensuring only authorized data is retrieved and processed.

### Leveraging OpenFGA's `ListObjects` API

OpenFGA provides the [`ListObjects` API](https://openfga.dev/docs/concepts#what-is-a-list-objects-request), which is perfectly suited for this task. This API endpoint returns a list of object IDs of a specific type that a user has a particular relationship (permission) with.

For example, a call to `ListObjects` for `user:anne` with relation `can_read` on type `row` would return all row IDs Anne is permitted to read. This list of IDs can then be directly injected into the `IN` clause of our SQL query. Conversely, if modeling "denied" rows, `ListObjects` could return IDs the user _cannot_ access, for use with `NOT IN`.

## Strategy: `IN` (Allow List) vs. `NOT IN` (Deny List)

Choosing between an `IN` clause (an "allow list" approach) and a `NOT IN` clause (a "deny list" approach) depends on the nature of your data and access patterns. Consider these two primary models:

1.  **Explicit Permission (Default Deny):**

    - **Question:** "Which rows _can_ the user see?"
    - **SQL:** `WHERE entry.id IN (...)`
    - **Use Case:** Users can, by default, see very few rows, or access is highly restricted. You explicitly grant access to specific rows. This is common for sensitive data where most data is private.

2.  **Implicit Permission (Default Allow with Explicit Deny):**
    - **Question:** "Which rows is the user _forbidden_ from seeing?" (assuming they can see most others)
    - **SQL:** `WHERE entry.id NOT IN (...)`
    - **Use Case:** Users can, by default, see most rows in a table, but specific rows are restricted for certain users or roles. This is useful when most data is broadly accessible, with only a few exceptions.

Your client applications need to be aware of which strategy is in use for a given table, as the interpretation of the ID list from OpenFGA changes.

### Decision Guidance for `IN` vs. `NOT IN`

The following decision tree can help guide your choice:

![Decision tree for choosing between IN and NOT IN strategies for tabular data ACLs](./imgs/decision_tree_tabular.svg)
[1] A yes in this case means that the table resemble an HR table, where each user can see its own row
and potentially few others (like a manager being able to see his/her reportee data).
A no, instead, is a table that contain financial data. Only few rows of such tables must be
guarded. Continuing with the financial metaphor, only the current quarter data access is
restricted due to regulatory reasons (i.e. avoid insider trading).
