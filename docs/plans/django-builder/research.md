# Research
Legacy Next.js serves MDX fetched from an Airtable-backed Django API, including a hard-coded development hostname. Its themes and navigation are useful references; runtime dependencies and executable MDX are not retained in the replacement.

Examined a sibling Django blob implementation: binary contents, content type, byte size, stable identifier and response helpers. New implementation uses MySQL LONGBLOB through Django BinaryField, authenticated draft access and published-reference checks. Already-compressed images are re-encoded rather than compressed twice.

Official references: Django 5.2 deployment checklist; django-allauth Discord provider (identify scope, immutable user ID); Quill 2 documentation; Discord signed HTTP interactions documentation.
