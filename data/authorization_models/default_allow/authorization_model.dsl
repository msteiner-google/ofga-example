// In this model, instead, everything is visible unless
// a user is, directly or indirectly, marked as exclude
// on an item.
model
  schema 1.1

type user

type group
  relations
    define member: [user:*, user, group#member]

type item
  relations
    define cannot_read: excluded
    define excluded: [user, group#member, group]
