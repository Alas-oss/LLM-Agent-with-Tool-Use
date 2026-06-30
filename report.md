# Agent & Tool Use

Built a research assistant agent that answers multi-step questions by combining information from multiple tools, using a standard ReAct-style loop where LLM decides which tools to call and when.


| Tool | Source | Purpose |
| :--- | :--- | :--- |
| **get_weather** | OpenWeatherMap | Temperature, condition, humidity for a city |
| **search_wikipedia** | Wikipedia REST API | Plain-text summary of a topic |
| **calculate** | Local | Safely evaluates math expressions |
| **get_country_info** | REST Countries | Capital, population, area, currencies |
| **convert_currency** | ExchangeRate-API | Currency conversion (stretch goal) |

## Results
All 5 requires test queries were answered correctly, using 5 tools (4 required + 1 stretch), wth full JSON trace logging for every run.

## How the Agent Loop Works
The agent sends the conversation and tool schemas to the LLM on every iteration. If the model returns tool calls, the code executes them and appends the results back into the conversation. And if not, the model's response is the final answer. A `MAX_ITERATIONS` cap of 10 was added as a safety guard, since a model that can't converge on an answer could other wise loop indefinitely and run up API costs without bounds.

## A Surprising Finding
Tool docstrings turned out to be functionally part of the code, not just part of the documentation, as they're copied directly into the JSON schema that is sent to the LLM ,so a vague docstring measurably hurts the model's ability to pick the right tool. This became obvoius while debugging the `calculate` tool: earlier I tried to use Python's ast module to walk the expression tree which ended up throwing an `AttributeError` from an incorrect assumption about the API in Python 3.11, so it waas replaced with a simple character whitelist that blocks anything outside of digits and basic math operations before the string ever reaches `eval()`. If one wants to evaluate more complex mathematical problems then they can just widen the scope of acceptable characters and etc.

A second surprise came form the `get_country_info` tool: mid-build, the REST Countries API started returning a 200-status response with `{"success": false}` instead of a clean error, which surfaced several calls downstream as an unrelated-looking crash. The fix detects that response shape and falls back to `search_wikipedia` for basic country facts, so the tool degrades gracefully instead of failing outright.

## The Recommended Default Pattern
### System Prompt:
"You are a helpful research assistant with access to tools."

"Always use tools to look up real information rather than guessing."

"Always use the calculate tool for any arithmetic."

"When you have all the information needed, give a clear complete answer."

### Tool Dispatch Pattern:
```
result = dispatch_tool(tool_call.function.name, json.loads(tool_call.function.arguments))
messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": result})
```
#### Reason: 
Every tool returns a structured dict with either real data or an "error" key rather than raising an exception, so a single failing tool (like the country API) never crashes the whole agent loop — it degrades to an error message or a fallback the model can reason about and route around.