## The Critical Role of Access Control Lists (ACLs) in Modern Applications

Fine-grained Access Control Lists (ACLs) are a cornerstone of data security,
ensuring that data is only accessed by authorized entities. This principle becomes even more
critical in contemporary application architectures.

### The AI Agent Amplification

The recent proliferation of AI agents introduces new dimensions to access control challenges.
These agents are often designed to interact with vast quantities of data, either by directly
querying primary data sources or by operating on derived copies, such as text chunks embedded in
vector databases.

This operational paradigm presents significant security considerations:

- **Data Interface:** AI agents serve as the primary interface through which users interact with
  potentially sensitive data via conversational UIs.
- **Permission Propagation:** Ensuring that user-specific permissions are accurately and
  consistently enforced across original and copied data (e.g., document chunks in vector DBs) is paramount.
  Failure to do so can lead to agents inadvertently exposing data beyond a user's authorized scope.

Neglecting robust ACL implementation can have severe consequences.
The Open Web Application Security Project (OWASP) consistently identifies Broken Access Control
as the [top security vulnerability](https://owasp.org/Top10/A01_2021-Broken_Access_Control/),
highlighting the pervasive risk it poses to systems and data integrity.

### ACL Enforcement Strategies

To effectively implement ACLs, particularly in systems interacting with AI agents and diverse data
sources, two primary filtering strategies are commonly employed: pre-filtering and post-filtering.

#### Pre-Filtering (Query-Time Enforcement)

Pre-filtering involves integrating ACL checks directly into the data retrieval query.
This means that before any data is fetched, the system modifies the query
(e.g., by dynamically constructing the `WHERE` clause of a SQL statement) to ensure that only
data the requesting user is authorized to access is considered.

This is the recommended way to do ACL checks on tabular data and I deep dive on the subject
[here](./Authorization model for tabular data.md).

#### Post-Filtering (Results-Time Enforcement)

Post-filtering applies ACL checks after an initial, potentially broader, set of data has been
retrieved. This is particularly relevant in Retrieval Augmented Generation (RAG) applications
where an initial retrieval stage might fetch a larger set of documents or data chunks.
After this retrieval, a secondary filtering step verifies each item against the user's
permissions before it's used by the language model or presented to the user.

This is usually the preferred way to use in, for instance, a RAG system where the first retrieval
step generates a tractable number (`O(10s)`) of candidate documents/items
