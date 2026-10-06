import json

from connect_config.generation.terraform.render import generate_terraform
from connect_config.extraction.pipeline import run_export
from connect_config.validation.validator import validate_config
from tests.fake_connect_client import FakeConnectClient


def test_acceptance_pipeline_and_generation():
    client = FakeConnectClient()
    config = run_export(client, "instance-1")

    assert config.hours_of_operation[0].logical_name == "business_hours"
    assert config.queues[0].logical_name == "customer_service"
    assert config.queues[0].hours_of_operation_ref == "business_hours"
    assert config.quick_connects[0].logical_name == "agent_transfer"
    assert config.contact_flows[0].logical_name == "main_inbound"

    issues = validate_config(config)
    assert any(issue.severity == "ERROR" for issue in issues)

    tf_files = generate_terraform(config)
    artifact_files = {}
    for flow in config.contact_flows:
        artifact_files[f"flows/{flow.logical_name}.json.tftpl"] = json.dumps(flow.resolved_json, indent=2, sort_keys=True)

    full_output = "\n".join(tf_files.values()) + "\n".join(artifact_files.values())
    for leaked_source_id in ("hoo-1", "q-1", "rp-1", "sp-1", "hg-1", "qq-1", "cf-1", "cf-2", "cfm-1", "pr-1"):
        assert f'"{leaked_source_id}"' not in full_output
    assert "cf-UNKNOWN" in full_output

    assert any("lambda" in key for key in tf_files)
    assert any("main_inbound" in key for key in tf_files)


def test_logical_name_collision_safe():
    from connect_config.normalization.naming import LogicalNameAllocator

    allocator = LogicalNameAllocator("queue")
    assert allocator.allocate("Customer Service") == "customer_service"
    assert allocator.allocate("Customer Service") == "customer_service_2"


def test_client_pagination_fallback():
    from connect_config.aws.client import list_all

    class LocalClient:
        def __init__(self):
            self.items = [1, 2, 3]

        def list_items(self, **kwargs):
            return {"Items": self.items}

    client = LocalClient()
    assert list_all(client, "list_items", "Items") == [1, 2, 3]
