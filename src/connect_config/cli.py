from __future__ import annotations

import json
from pathlib import Path

import click
import yaml

from connect_config.aws.client import DebuggableClient, build_session
from connect_config.extraction.pipeline import run_export
from connect_config.generation.artifacts.flows import generate_flow_artifacts
from connect_config.generation.terraform.render import generate_terraform
from connect_config.models.config_bundle import CanonicalConfig
from connect_config.reporting.summary import format_summary
from connect_config.validation.validator import validate_config


@click.group()
def cli():
    """Amazon Connect configuration exporter and Terraform generator."""


@cli.command()
@click.option("--instance-id", required=True)
@click.option("--profile", default=None)
@click.option("--region", default="us-east-1")
@click.option("--output", required=True, type=click.Path(file_okay=False, path_type=Path))
@click.option("--debug-output", default=None, type=click.Path(dir_okay=False, path_type=Path))
def export(instance_id: str, profile: str | None, region: str, output: Path, debug_output: Path | None):
    session = build_session(profile=profile, region=region)
    client = session.client("connect", region_name=region)
    if debug_output is not None:
        client = DebuggableClient(client, debug_output)
    config = run_export(client, instance_id)
    output.mkdir(parents=True, exist_ok=True)
    for flow in config.contact_flows:
        dest = output / "flows"
        dest.mkdir(parents=True, exist_ok=True)
        (dest / f"{flow.logical_name}.json").write_text(json.dumps(flow.content or {}, indent=2, sort_keys=True))
    for flow in config.contact_flow_modules:
        dest = output / "flow_modules"
        dest.mkdir(parents=True, exist_ok=True)
        (dest / f"{flow.logical_name}.json").write_text(json.dumps(flow.content or {}, indent=2, sort_keys=True))
    for resource_type in [
        "hours_of_operation",
        "queues",
        "routing_profiles",
        "security_profiles",
        "hierarchy_groups",
        "users",
        "quick_connects",
        "contact_flows",
        "contact_flow_modules",
        "prompts",
    ]:
        data = getattr(config, resource_type, [])
        file_path = output / f"{resource_type}.yaml"
        file_path.write_text(yaml.safe_dump([item.model_dump() for item in data], sort_keys=True, default_flow_style=False))
    migration = output / "migration-map.yaml"
    migration.write_text(yaml.safe_dump({"migration_map": {}}, sort_keys=True))
    issues = validate_config(config)
    click.echo(format_summary(config, issues))


@cli.command()
@click.option("--config", required=True, type=click.Path(exists=True, file_okay=False, path_type=Path))
def validate(config: Path):
    cfg = _load_config(config)
    issues = validate_config(cfg)
    for issue in issues:
        click.echo(f"{issue.severity}: {issue.resource_type}:{issue.logical_name}:{issue.message}")
    if any(issue.severity == "ERROR" for issue in issues):
        raise SystemExit(1)


@cli.command()
@click.option("--config", required=True, type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option("--output", required=True, type=click.Path(file_okay=False, path_type=Path))
def generate(config: Path, output: Path):
    cfg = _load_config(config)
    issues = validate_config(cfg)
    if any(issue.severity == "ERROR" for issue in issues):
        for issue in issues:
            click.echo(f"{issue.severity}: {issue.resource_type}:{issue.logical_name}:{issue.message}")
        raise SystemExit(1)
    output.mkdir(parents=True, exist_ok=True)
    tf_files = generate_terraform(cfg)
    artifact_files = generate_flow_artifacts(cfg)
    for name, content in tf_files.items():
        (output / name).write_text(content)
    for name, content in artifact_files.items():
        path = output / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    click.echo(f"Generated {len(tf_files)} Terraform files and {len(artifact_files)} flow artifacts.")


@cli.command()
@click.option("--config", required=True, type=click.Path(exists=True, file_okay=False, path_type=Path))
def inspect(config: Path):
    cfg = _load_config(config)
    click.echo(json.dumps(cfg.model_dump(), indent=2, sort_keys=True))


def _load_config(config_root: Path) -> CanonicalConfig:
    config = CanonicalConfig()
    for name in [
        "hours_of_operation.yaml",
        "queues.yaml",
        "routing_profiles.yaml",
        "security_profiles.yaml",
        "hierarchy_groups.yaml",
        "users.yaml",
        "quick_connects.yaml",
        "contact_flows.yaml",
        "contact_flow_modules.yaml",
        "prompts.yaml",
    ]:
        path = config_root / name
        if path.exists():
            payload = yaml.safe_load(path.read_text()) or []
            setattr(config, name.replace(".yaml", ""), [__import__("pydantic").BaseModel.model_validate(item, type_="dict") for item in payload])
    return config


if __name__ == "__main__":
    cli()
