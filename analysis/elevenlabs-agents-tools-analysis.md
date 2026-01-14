# ElevenLabs Agents Platform - Tools Analysis

## Executive Summary

ElevenLabs Agents Platform is a conversational AI platform focused on voice-based interactions. The platform supports **four types of tools** that extend agent capabilities: Client Tools, Server Tools, MCP Tools, and System Tools. This analysis evaluates tool integration patterns for potential SkillForge adapter design.

---

## Tool Types Overview

### 1. Client Tools
**Purpose**: Execute operations directly on the client-side application.

**Use Cases**:
- Triggering UI events
- Manipulating the DOM
- Sending notifications
- Running browser-side functions

**Definition Process**:
1. Configure in agent dashboard (set Tool Type to "Client")
2. Provide: Name, Description, Parameters (data type, identifier, requirements)
3. Register tool in code (Python, JavaScript, or Swift)

**Python Registration Example**:
```python
from elevenlabs import ClientTools, Conversation, ElevenLabs

def log_message(parameters):
    message = parameters.get("message")
    print(message)

client_tools = ClientTools()
client_tools.register("logMessage", log_message)

conversation = Conversation(
    client=ElevenLabs(api_key="your-api-key"),
    agent_id="your-agent-id",
    client_tools=client_tools
)
```

**Key Features**:
- Supports both sync and async tools
- "Wait for response" option allows data integration back into conversation
- Case-sensitive parameter matching required

---

### 2. Server Tools
**Purpose**: Connect with external data and systems via HTTP API calls.

**Capabilities**:
- Fetch real-time data from REST-enabled databases
- Trigger authenticated actions
- Dynamically generate query and parameter requests

**Configuration Components**:
1. **Basic Config**: Name, Description, Method (GET/POST/etc.), URL
2. **Parameter Types**:
   - Path Parameters: URL variables in `{curly braces}`
   - Query Parameters: URL-appended data
   - Body Parameters: Request payload details
   - Headers: Custom request metadata

**Authentication Methods**:
- OAuth2 Client Credentials
- OAuth2 JWT
- Basic Authentication
- Bearer Tokens
- Custom Headers

**Example - Weather Tool**:
```
URL: https://api.open-meteo.com/v1/forecast
Parameters:
- latitude (dynamic)
- longitude (dynamic)
- current weather metrics
- hourly weather metrics
```

---

### 3. MCP (Model Context Protocol) Tools
**Purpose**: Connect agents to external tools and data sources using Anthropic's open standard.

**How It Works**:
- MCP defines how applications provide context to LLMs
- Enables dynamic interactions by connecting to third-party MCP servers

**Configuration**:
1. Retrieve MCP server URL
2. Navigate to integrations dashboard
3. Add server details: Name, Description, Server URL, Optional secret token, HTTP headers

**Tool Approval Modes**:
- **Always Ask** (recommended): Request permission before each tool use
- **Fine-Grained Tool Approval**: Selectively pre-approve specific tools
- **No Approval**: Unrestricted tool usage

**Supported Servers**:
- Zapier integration (hundreds of tools/services)
- SSE and HTTP streamable transport servers
- Custom MCP servers

**Limitations**:
- Not available for Zero Retention Mode or HIPAA-compliant environments
- Users responsible for security/compliance of third-party MCP servers

---

### 4. System Tools
**Purpose**: Built-in platform tools for common conversational actions.

**Available System Tools**:

| Tool | Purpose | Key Parameters |
|------|---------|----------------|
| **End Call** | Terminate conversations | `reason` (required), `message` (optional) |
| **Language Detection** | Auto-switch conversation language | `reason`, `language` (both required) |
| **Agent Transfer** | Transfer between specialized AI agents | `agent_number` (required), `reason` (optional) |
| **Transfer to Human** | Hand off to human operators | `transfer_number`, `client_message`, `agent_message` (all required) |
| **Skip Turn** | Allow agent to pause without speaking | `reason` (optional) |
| **Play Keypad Touch Tone** | Interact with phone systems (DTMF) | `dtmf_tones` (required) |
| **Voicemail Detection** | Detect/interact with voicemail | `reason` (required) |

---

## Tool Communication Events

### WebSocket Event Flow

**Client Tool Execution Flow**:
1. Agent sends `client_tool_call` (tool name, call ID, parameters)
2. Client executes the tool
3. Client sends `client_tool_result` (call ID, result, error status)
4. Agent processes result, may send `agent_tool_response`

**Event Types**:

| Event | Direction | Purpose |
|-------|-----------|---------|
| `client_tool_call` | Server -> Client | Agent requests client tool execution |
| `client_tool_result` | Client -> Server | Client returns tool execution result |
| `agent_tool_response` | Server -> Client | Agent acknowledges tool execution |
| `mcp_tool_call` | Server -> Client | MCP tool execution notification (with state: loading, awaiting_approval, success, failure) |

---

## Personalization & Dynamic Data

**Dynamic Variables**:
- Inject runtime values using `{{ var_name }}` syntax
- Can personalize: messages, system prompts, **and tool parameters**
- Supports different variable types (strings, numbers, booleans)

**Overrides**:
- Replace system prompts, first messages, language, or voice per user
- Passed via `conversation_initiation_client_data` structure

---

## Best Practices (from Documentation)

1. **Tool Naming**: Use intuitive, descriptive names
2. **Parameter Descriptions**: Provide clear, detailed descriptions
3. **System Prompt**: Include tool usage guidance in the system prompt
4. **Model Selection**: Use high-intelligence models (GPT-4o mini, Claude 3.5 Sonnet) when using tools
5. **Troubleshooting**: Verify tool name matches registration, check console for errors

---

## Architecture Insights

### Platform Components
1. Speech-to-Text (ASR) model
2. Language Model (configurable - supports GPT-4, Claude, etc.)
3. Text-to-Speech model (5k+ voices, 31 languages)
4. Proprietary turn-taking conversation model

### Key Characteristics
- **Voice-first**: Platform optimized for voice conversations
- **Real-time**: WebSocket-based communication
- **Multi-modal**: Tools can interact with audio, UI, and external APIs
- **LLM-agnostic**: Supports multiple language models

---

## Implications for SkillForge Adapter Design

### Opportunity Areas

1. **Client Tools Integration**
   - Skills could be registered as client tools via `ClientTools.register()`
   - Skill instructions could inform the agent when to call the tool
   - Tool results return to conversation context

2. **System Prompt Injection**
   - Similar to CrewAI's backstory, system prompt is configurable
   - Meta-skill could be injected into system prompt
   - Dynamic variables (`{{ }}`) could inject skill-related data

3. **Server Tools for Skill-Bundled APIs**
   - Skills with tools.py could be exposed as server endpoints
   - Webhook-style integration possible

4. **MCP Integration**
   - SkillForge could expose skills via MCP server
   - Would allow any ElevenLabs agent to access SkillForge skills

### Challenges

1. **Voice-First Paradigm**
   - Skills designed for text interaction may need voice adaptation
   - No direct file/code manipulation (unlike coding agents)

2. **No Direct Bash Execution**
   - `skillforge read` CLI pattern won't work directly
   - Would need to pre-load skills or expose via API

3. **Tool Registration Model**
   - Tools must be pre-registered (dashboard or code)
   - Dynamic skill loading not directly supported

### Recommended Adapter Strategy

**Option A: Pre-Registration Model**
- Register each skill as a client tool at conversation start
- Inject skill instructions into system prompt
- Tool execution returns skill-specific responses

**Option B: MCP Server Approach**
- Build SkillForge MCP server that exposes skills as tools
- Agent connects to SkillForge MCP server
- Skills become available as MCP tools

**Option C: Hybrid Approach**
- System prompt includes meta-skill (skill discovery)
- One client tool: `skillforge_invoke(skill_name, parameters)`
- Backend resolves skill and returns instructions/actions

---

## Key Differences from CrewAI/LangChain

| Aspect | ElevenLabs | CrewAI/LangChain |
|--------|------------|------------------|
| **Primary Mode** | Voice | Text |
| **Tool Registration** | Pre-configured | Runtime |
| **Bash Access** | No | Yes (assumption to validate) |
| **System Prompt** | Configurable | Configurable |
| **Dynamic Variables** | Yes (`{{ }}`) | Limited |
| **Tool Result Handling** | WebSocket events | Direct return |

---

## References

- [ElevenLabs Agents Platform Overview](https://elevenlabs.io/docs/agents-platform/overview)
- [Client Tools Documentation](https://elevenlabs.io/docs/agents-platform/customization/tools/client-tools)
- [Server Tools Documentation](https://elevenlabs.io/docs/agents-platform/customization/tools/server-tools)
- [System Tools Documentation](https://elevenlabs.io/docs/agents-platform/customization/tools/system-tools)
- [MCP Tools Documentation](https://elevenlabs.io/docs/agents-platform/customization/tools/mcp)
- [Events Documentation](https://elevenlabs.io/docs/agents-platform/customization/events)
- [ElevenLabs Python SDK](https://github.com/elevenlabs/elevenlabs-python)
