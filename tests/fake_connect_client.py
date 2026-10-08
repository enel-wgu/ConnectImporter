class FakeConnectClient:
    """Minimal fake client for acceptance tests."""

    def __init__(self):
        self.instance_id = "instance-1"
        self.hours_of_operation = {
            "hoo-1": {
                "HoursOfOperationId": "hoo-1",
                "Name": "Business Hours",
                "TimeZone": "UTC",
                "Config": [{"Day": "MONDAY", "StartTime": "09:00", "EndTime": "17:00"}],
            }
        }
        self.queues = {
            "q-1": {
                "QueueId": "q-1",
                "Name": "Customer Service",
                "Description": "Main queue",
                "HoursOfOperationId": "hoo-1",
                "Status": "ACTIVE",
                "MaxContacts": 100,
                "OutboundCallerConfig": {},
            }
        }
        self.routing_profiles = {
            "rp-1": {
                "RoutingProfileId": "rp-1",
                "Name": "Default Routing Profile",
                "DefaultOutboundQueueId": "q-1",
                "QueueConfigSummaryList": [{"QueueId": "q-1", "Priority": 1, "Delay": 0, "Channel": "VOICE"}],
            }
        }
        self.security_profiles = {
            "sp-1": {
                "SecurityProfileId": "sp-1",
                "Name": "Administrator",
                "Permissions": ["connect:*"],
            }
        }
        self.hierarchy_groups = {
            "hg-1": {
                "HierarchyGroupId": "hg-1",
                "Name": "Operations",
                "ParentGroupId": "",
            }
        }
        self.users = {
            "u-1": {
                "UserId": "u-1",
                "Username": "alice",
                "IdentityInfo": {"FirstName": "Alice", "LastName": "Example", "Email": "alice@example.com"},
                "PhoneConfig": {"AutoAccept": True},
                "RoutingProfileId": "rp-1",
                "SecurityProfileIds": ["sp-1"],
                "HierarchyGroupId": "hg-1",
                "IdentityManagementType": "CONNECT_MANAGED",
            }
        }
        self.quick_connects = {
            "qq-1": {
                "QuickConnectId": "qq-1",
                "Name": "Agent Transfer",
                "QuickConnectConfig": {
                    "QuickConnectType": "QUEUE",
                    "QueueConfig": {"QueueId": "q-1", "ContactFlowId": "cf-1"},
                },
            }
        }
        self.prompts = {
            "pr-1": {
                "PromptId": "pr-1",
                "Name": "Welcome Prompt",
            }
        }
        self.contact_flow_modules = {
            "cfm-1": {
                "ContactFlowModuleId": "cfm-1",
                "Name": "Module A",
                "Content": {"Version": "1.0", "Actions": []},
            }
        }
        self.contact_flows = {
            "cf-1": {
                "ContactFlowId": "cf-1",
                "Name": "Main Inbound",
                "Type": "CONTACT_FLOW",
                "Content": {
                    "Version": "1.0",
                    "Metadata": {"position": {"x": 0, "y": 0}},
                    "Actions": [
                        {
                            "Identifier": "a-1",
                            "Type": "TransferToQueue",
                            "Parameters": {"QueueId": "q-1"},
                            "Transitions": {"NextAction": "a-2"},
                        },
                        {
                            "Identifier": "a-2",
                            "Type": "InvokeLambdaFunction",
                            "Parameters": {"LambdaFunctionARN": "arn:aws:lambda:us-east-1:111111111111:function:lookup"},
                            "Transitions": {"NextAction": "a-3"},
                        },
                        {
                            "Identifier": "a-3",
                            "Type": "TransferToQueue",
                            "Parameters": {"ContactFlowId": "cf-UNKNOWN"},
                            "Transitions": {"NextAction": ""},
                        },
                    ],
                },
            },
            "cf-2": {
                "ContactFlowId": "cf-2",
                "Name": "Escalation Flow",
                "Type": "CONTACT_FLOW",
                "Content": {"Version": "1.0", "Actions": []},
            },
        }

    def list_hours_of_operations(self, InstanceId, **kwargs):
        return {"HoursOfOperationSummaryList": list(self.hours_of_operation.values())}

    def describe_hours_of_operation(self, InstanceId, HoursOfOperationId, **kwargs):
        return {"HoursOfOperation": self.hours_of_operation[HoursOfOperationId]}

    def list_queues(self, InstanceId, **kwargs):
        return {"QueueSummaryList": [{"Id": qid, "Name": data["Name"]} for qid, data in self.queues.items()]}

    def describe_queue(self, InstanceId, QueueId, **kwargs):
        return {"Queue": self.queues[QueueId]}

    def list_queue_quick_connects(self, InstanceId, QueueId, **kwargs):
        return {"QuickConnectSummaryList": [{"Id": "qq-1", "Name": "Agent Transfer"}]}

    def list_routing_profiles(self, InstanceId, **kwargs):
        return {"RoutingProfileSummaryList": [{"Id": rid, "Name": data["Name"]} for rid, data in self.routing_profiles.items()]}

    def describe_routing_profile(self, InstanceId, RoutingProfileId, **kwargs):
        return {"RoutingProfile": self.routing_profiles[RoutingProfileId]}

    def list_routing_profile_queues(self, InstanceId, RoutingProfileId, **kwargs):
        return {"QueueConfigSummaryList": self.routing_profiles[RoutingProfileId]["QueueConfigSummaryList"]}

    def list_security_profiles(self, InstanceId, **kwargs):
        return {"SecurityProfileSummaryList": [{"Id": sid, "Name": data["Name"]} for sid, data in self.security_profiles.items()]}

    def describe_security_profile(self, InstanceId, SecurityProfileId, **kwargs):
        return {"SecurityProfile": self.security_profiles[SecurityProfileId]}

    def list_security_profile_permissions(self, InstanceId, SecurityProfileId, **kwargs):
        return {"Permissions": self.security_profiles[SecurityProfileId]["Permissions"]}

    def describe_user_hierarchy_structure(self, InstanceId, **kwargs):
        return {"HierarchyStructure": {"HierarchyPath": ["root", "operations"]}}

    def list_user_hierarchy_groups(self, InstanceId, **kwargs):
        return {"HierarchyGroupSummaryList": [{"Id": hid, "Name": data["Name"]} for hid, data in self.hierarchy_groups.items()]}

    def describe_user_hierarchy_group(self, InstanceId, HierarchyGroupId, **kwargs):
        return {"HierarchyGroup": self.hierarchy_groups[HierarchyGroupId]}

    def list_users(self, InstanceId, **kwargs):
        return {"UserSummaryList": [{"Id": uid, "Username": data["Username"]} for uid, data in self.users.items()]}

    def describe_user(self, InstanceId, UserId, **kwargs):
        return {"User": self.users[UserId]}

    def list_quick_connects(self, InstanceId, **kwargs):
        return {"QuickConnectSummaryList": [{"Id": qid, "Name": data["Name"]} for qid, data in self.quick_connects.items()]}

    def describe_quick_connect(self, InstanceId, QuickConnectId, **kwargs):
        return {"QuickConnect": self.quick_connects[QuickConnectId]}

    def list_prompts(self, InstanceId, **kwargs):
        return {"PromptSummaryList": [{"Id": pid, "Name": data["Name"]} for pid, data in self.prompts.items()]}

    def list_contact_flow_modules(self, InstanceId, **kwargs):
        return {"ContactFlowModulesSummaryList": [{"Id": cid, "Name": data["Name"]} for cid, data in self.contact_flow_modules.items()]}

    def describe_contact_flow_module(self, InstanceId, ContactFlowModuleId, **kwargs):
        return {"ContactFlowModule": self.contact_flow_modules[ContactFlowModuleId]}

    def list_contact_flows(self, InstanceId, **kwargs):
        return {"ContactFlowSummaryList": [{"Id": cid, "Name": data["Name"]} for cid, data in self.contact_flows.items()]}

    def describe_contact_flow(self, InstanceId, ContactFlowId, **kwargs):
        return {"ContactFlow": self.contact_flows[ContactFlowId]}

    def list_instances(self, **kwargs):
        return {"InstanceSummaryList": [{"Id": self.instance_id, "Arn": "arn:aws:connect:us-east-1:123456789012:instance/instance-1"}]}
