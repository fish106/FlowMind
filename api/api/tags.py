from enum import Enum


class RouteTags(str, Enum):
    MONITORING = "Monitoring"
    AGENTS = "Agents"
    AGENT_SCHEMAS = "Agent Schemas"
    RUNS = "Runs"
    EXAMPLES = "Examples"
    AGENT_GROUPS = "Agent Groups"
    ORGANIZATIONS = "Organizations"
    MODELS = "Models"
    TRANSCRIPTIONS = "Transcriptions"
    TOOLS = "Tools"
    RUN = "Run"
    API_KEYS = "API Keys"
    REVIEWS = "Reviews"
    UPLOAD = "Upload Files"
    VERSIONS = "Versions"
    PAYMENTS = "Payments"
    NEW_TOOL_AGENT = "New Tool Agent"
    FEATURES = "Features"
    PROMPT_ENGINEER_AGENT = "Prompt Engineer Agent"
    FEEDBACK = "Feedback"
