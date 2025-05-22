// In this model everything is forbidden unless there is a user is directly or
// indirectly a reader of an item.
model
  schema 1.1

type user

type group
  relations
    define member: [user:*, user, group#member]

type item
  relations
    define can_read: reader
    define reader: [user, group#member, group]

