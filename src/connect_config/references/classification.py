from __future__ import annotations

from dataclasses import dataclass

from connect_config.models.common import ResourceType


@dataclass(frozen=True)
class ParamRule:
    resource_type: ResourceType | None
    kind: str
    category: str


FLOW_PARAMETER_RULES: dict[str, ParamRule] = {
    "QueueId": ParamRule(ResourceType.QUEUE, "TRANSLATED", "queue"),
    "ContactFlowId": ParamRule(ResourceType.CONTACT_FLOW, "TRANSLATED", "contact_flow"),
    "FlowModuleId": ParamRule(ResourceType.CONTACT_FLOW_MODULE, "TRANSLATED", "flow_module"),
    "QuickConnectId": ParamRule(ResourceType.QUICK_CONNECT, "TRANSLATED", "quick_connect"),
    "HoursOfOperationId": ParamRule(ResourceType.HOURS_OF_OPERATION, "TRANSLATED", "hours_of_operation"),
    "RoutingProfileId": ParamRule(ResourceType.ROUTING_PROFILE, "TRANSLATED", "routing_profile"),
    "PromptId": ParamRule(ResourceType.PROMPT, "TRANSLATED", "prompt"),
    "LambdaFunctionARN": ParamRule(None, "EXTERNAL_DEPENDENCY", "lambda_arn"),
    "LexBot": ParamRule(None, "EXTERNAL_DEPENDENCY", "lex_bot"),
    "LexV2Bot": ParamRule(None, "EXTERNAL_DEPENDENCY", "lex_v2_bot"),
    "PhoneNumber": ParamRule(None, "ENVIRONMENT_SPECIFIC", "phone_number"),
    "DialablePhoneNumber": ParamRule(None, "ENVIRONMENT_SPECIFIC", "dialable_phone_number"),
}

KNOWN_NON_REFERENCE_KEYS = {"Identifier", "NextAction", "Type", "Name"}
