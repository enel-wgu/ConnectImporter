# Architecture

The exporter moves through three stages: extraction, normalization, and generation.

1. Extraction reads AWS Connect resources by list/describe calls and stores raw objects in the source model.
2. Normalization assigns logical names, classifies resource references, and builds a portable canonical config model.
3. Generation takes the canonical config and produces Terraform plus flow templates for a separate target instance.

The dependency order used by the project is: instance, hours of operation, queue, routing profile, security profile, hierarchy groups, user, quick connect, prompt, contact flow module, contact flow.

Contact flows and flow modules are pre-registered before content resolution so cross-references can be rewritten deterministically without hardcoding source IDs into target Terraform.
