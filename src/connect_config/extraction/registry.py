from connect_config.extraction._handler import (
    ContactFlowModulesHandler,
    ContactFlowsHandler,
    HoursHandler,
    HierarchyHandler,
    InstanceHandler,
    PromptsHandler,
    QueuesHandler,
    QuickConnectsHandler,
    RoutingProfilesHandler,
    SecurityProfilesHandler,
    UserHandler,
)

ORDERED_HANDLERS = [
    InstanceHandler(),
    HoursHandler(),
    QueuesHandler(),
    RoutingProfilesHandler(),
    SecurityProfilesHandler(),
    HierarchyHandler(),
    UserHandler(),
    QuickConnectsHandler(),
    PromptsHandler(),
    ContactFlowModulesHandler(),
    ContactFlowsHandler(),
]
