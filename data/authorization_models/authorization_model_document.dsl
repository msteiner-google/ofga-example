model
  schema 1.1

type user

type group
  relations
    define member: [user:*, user, group#member]

type doc
  relations
    define can_read: viewer
    define viewer: [user:*, user, group#member, group]
