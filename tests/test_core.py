import json

from connect_config.generation.terraform.render import generate_terraform
from connect_config.extraction.pipeline import run_export
from connect_config.models.config_bundle import CanonicalConfig, Queue, QuickConnect, RoutingProfile
from connect_config.validation.validator import validate_config
from tests.fake_connect_client import FakeConnectClient


def test_queue_reference_rendering_uses_real_resource_addresses():
    cfg = CanonicalConfig(
        queues=[
            Queue(logical_name="customer_service", source_id="q-1", name="Customer Service", hours_of_operation_ref="business_hours", quick_connect_refs=["agent_transfer"]),
        ],
        routing_profiles=[
            RoutingProfile(logical_name="default", source_id="rp-1", name="Default", default_outbound_queue_ref="customer_service", queue_configs=[{"channel": "VOICE", "delay": 0, "priority": 1, "queue_ref": "customer_service"}]),
        ],
        quick_connects=[
            QuickConnect(logical_name="agent_transfer", source_id="qq-1", name="Agent Transfer", quick_connect_type="QUEUE", queue_ref="customer_service", contact_flow_ref="main_inbound"),
        ],
    )
    rendered = "\n".join(generate_terraform(cfg).values())
    assert "aws_connect_queue.customer_service.queue_id" in rendered
    assert "aws_connect_quick_connect.agent_transfer.quick_connect_id" in rendered
    assert "aws_connect_queue..queue_id" not in rendered


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


def test_missing_queue_references_are_rejected():
    cfg = CanonicalConfig(
        queues=[
            Queue(logical_name="customer_service", source_id="q-1", name="Customer Service"),
        ],
        routing_profiles=[
            RoutingProfile(
                logical_name="default",
                source_id="rp-1",
                name="Default",
                default_outbound_queue_ref="missing_queue",
                queue_configs=[{"channel": "VOICE", "delay": 0, "priority": 1, "queue_ref": "missing_queue"}],
            )
        ],
        quick_connects=[
            QuickConnect(
                logical_name="agent_transfer",
                source_id="qq-1",
                name="Agent Transfer",
                quick_connect_type="QUEUE",
                queue_ref="missing_queue",
                contact_flow_ref="main_inbound",
            )
        ],
    )
    issues = validate_config(cfg)
    assert any(issue.severity == "ERROR" and issue.resource_type == "queue" for issue in issues)


def test_resolve_flow_content_handles_non_dict_actions():
    from connect_config.models.common import ResourceType
    from connect_config.references.catalog import ReferenceCatalog
    from connect_config.references.flow_resolver import resolve_flow_content

    result = resolve_flow_content({"Actions": ["bad-action", {"Parameters": {"QueueId": "queued"}}]}, ReferenceCatalog(), ResourceType.CONTACT_FLOW, "main_inbound", "cf-1")
    assert result["resolved_json"]["Actions"][0] == "bad-action"
    assert result["is_valid"] is False


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
