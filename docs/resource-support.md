# Resource support matrix

| Resource | AWS API | Terraform | Notes |
| --- | --- | --- | --- |
| Hours of operation | list_hours_of_operations, describe_hours_of_operation | aws_connect_hours_of_operation | Supported |
| Queue | list_queues, describe_queue | aws_connect_queue | Supported |
| Routing profile | list_routing_profiles, describe_routing_profile | aws_connect_routing_profile | Supported |
| Security profile | list_security_profiles, describe_security_profile | aws_connect_security_profile | Supported |
| Hierarchy group | list_user_hierarchy_groups, describe_user_hierarchy_group | aws_connect_user_hierarchy_group | Supported |
| User | list_users, describe_user | aws_connect_user | Supported with identity-source branching |
| Quick connect | list_quick_connects, describe_quick_connect | aws_connect_quick_connect | Supported |
| Contact flow module | list_contact_flow_modules, describe_contact_flow_module | aws_connect_contact_flow_module | Supported |
| Contact flow | list_contact_flows, describe_contact_flow | aws_connect_contact_flow | Supported |
| Prompt | list_prompts | data.aws_connect_prompt | Metadata export only |

Out of scope for v1: vocabulary, integration associations, lambda associations, instance storage config, phone numbers, Lex bot associations, views, task templates, evaluation forms, and rules. Those remain manual-export candidates for future work.
