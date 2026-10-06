# Reference resolution

The flow resolver inspects only `Actions[].Parameters` and never rewrites `Identifier` or transition IDs. This keeps flow-internal action graph metadata intact while still substituting target resource references.

A parameter key is classified into one of three categories:

- Translated: a resource ID that maps to a logical name and becomes a `${name}` placeholder in the generated template.
- External dependency: a Lambda ARN, Lex bot, or similar environment-specific value that remains explicit and is surfaced as a Terraform variable.
- Environment specific: a phone number or dialable phone number that must be reviewed manually before deployment.

Contact flow `Metadata` blocks are stripped deliberately from the resolved JSON. They are visual layout metadata, not runtime flow logic, and can drift across Connect instances. The resolved template therefore stays stable and deterministic.

Unresolved translated references are intentionally left in place as literal source IDs so the generated configuration still shows the exact place a human must fix before `apply`.
