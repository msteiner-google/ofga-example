### Very basic example

The terraform defined here sets up 3 things.

1. The cloud sql instance (running Postgres) that will host the permissions.
2. The migration script (as a Cloud Run Job) that prepares the DB created at step 1.
3. The actual OpenFGA server (as a Cloud Run Service). Since Cloud Run services
   can only expose one port, you need to decide whether to use HTTP(s) or GRPC
   as the connection mechanism with open fga.
