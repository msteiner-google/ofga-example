model
  schema 1.1

type user

type group
  relations
    define member: [user:*, user, group#member]

type row
  relations
    define cant_read: excluded
    define excluded: [user, group#member, group]
