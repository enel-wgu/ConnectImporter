# Amazon Connect Configuration Exporter and Terraform Generator

This project exports Amazon Connect configuration from a source instance, normalizes it into a portable canonical model, and generates Terraform for a separate target instance. It intentionally treats the source and target Connect instances as different AWS objects and never copies source IDs into generated Terraform.

## Installation

pip install -e .

## AWS permissions

The exporter only needs read-only Amazon Connect permissions such as `connect:List*`, `connect:Describe*`, and `connect:Get*` for the configuration it reads. Terraform apply on the target instance requires separate target-side permissions to create/update Connect configuration; this project does not own AWS instance provisioning.

## CLI commands

connect-config export --instance-id ID --profile NAME --region REGION --output ./config
connect-config validate --config ./config
connect-config generate --config ./config --output ./terraform
connect-config inspect --config ./config

The export command writes a canonical YAML bundle plus raw flow JSON snapshots. The generate command reads the exported config, validates it, and writes Terraform files and flow templates for a target Connect instance. The CLI is intentionally idempotent and deterministic for repeated exports of the same source configuration.

## Troubleshooting unresolved references

Unresolved IDs remain visible in the generated flow JSON so a human can see the exact place to fix the target mapping before deployment. Validation treats those as errors and blocks generation until they are resolved.
