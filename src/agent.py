import os
import sys
import json
import argparse
from openai import OpenAI
from dotenv import load_dotenv

sys.path.append(os.path.dirname(__file__))
from tools import dispatch_tool
load_dotenv()

client = OpenAI(
    api_key=os.environ.get("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)
MODEL = "llama-3.1-8b-instant"
MAX_ITERATIONS = 10

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current weather for a city. Returns temperature in Celsius, condition, and humidity.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "Name of the city e.g. 'London' or 'Tokyo'"
                    }
                },
                "required": ["city"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_wikipedia",
            "description": "Search Wikipedia and return a summary of a topic, person, place, or event.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The topic to search e.g. 'Eiffel Tower' or 'Japan'"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Safely evaluate a math expression and return the result. Use for any arithmetic.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "A math expression as a string e.g. '150 * 3 + 22 / 2'"
                    }
                },
                "required": ["expression"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_country_info",
            "description": "Get facts about a country: capital, population, area, and currencies.",
            "parameters": {
                "type": "object",
                "properties": {
                    "country": {
                        "type": "string",
                        "description": "Name of the country e.g. 'France' or 'Brazil'"
                    }
                },
                "required": ["country"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "convert_currency",
            "description": "Convert an amount from one currency to another using current exchange rates.",
            "parameters": {
                "type": "object",
                "properties": {
                    "amount": {"type": "number", "description": "The amount to convert"},
                    "from_currency": {"type": "string", "description": "3-letter currency code e.g. 'USD'"},
                    "to_currency": {"type": "string", "description": "3-letter currency code e.g. 'EUR'"}
                },
                "required": ["amount", "from_currency", "to_currency"]
            }
        }
    }
]

def run_agent(query: str, verbose: bool = False) -> str:
    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful research assistant with access to tools. "
                "Always use tools to look up real information rather than guessing.\n\n"
                
                "CRITICAL INSTRUCTIONS FOR TOOL CALLING:\n"
                "1. DO NOT nest tool calls or guess arguments from other tools. You can only call one tool function at a time per iteration.\n"
                "2. To compare or calculate values across multiple countries (e.g., Canada and Russia), you MUST call 'get_country_info' separately for EACH country in sequence first. Gather all raw facts before calling 'calculate'.\n"
                "3. To find demographic details like population, area, or capitals, ALWAYS use the 'get_country_info' tool.\n"
                "4. When you have all the information needed, give a clear complete answer."
            )
        },
        {
            "role": "user",
            "content": query
        }
    ]

    trace = {
        "query": query,
        "steps": [],
        "final_answer": ""
    }
    iterations = 0

    while iterations < MAX_ITERATIONS:
        iterations += 1

        if verbose:
            print(f"\n[Iteration {iterations}] calling llm")

        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOL_SCHEMAS,
            tool_choice="auto",
            max_tokens=1000
        )

        message = response.choices[0].message
        finish_reason = response.choices[0].finish_reason

        assistant_message = {
            "role": "assistant",
            "content": message.content or ""
        }

        if message.tool_calls:
            assistant_message["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                }
                for tc in message.tool_calls
            ]

        messages.append(assistant_message)

        if finish_reason == "stop" or not message.tool_calls:
            final_answer = message.content or ""
            trace["final_answer"] = final_answer

            if verbose:
                print(f"\n[Done after {iterations} iteration(s)]")

            save_trace(query, trace)
            return final_answer
        
        for tool_call in message.tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)

            if verbose:
                print(f"    Tool call: {tool_name}({arguments})")

            result = dispatch_tool(tool_name, arguments)

            if verbose:
                print(f"    Result: {result[:150]}...")

            trace["steps"].append({
                "iteration": iterations,
                "tool": tool_name,
                "arguments": arguments,
                "result": json.loads(result)
            })

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result
            })
    final_answer = "I reached the maximum number of steps without completing the task."
    trace["final_answer"] = final_answer
    save_trace(query, trace)
    return final_answer

def save_trace(query: str, trace: dict):
    os.makedirs("agent_traces", exist_ok=True)

    safe_name = "".join(c if c.isalnum() or c == " " else "_" for c in query[:40])
    safe_name = safe_name.strip().replace(" ", "_")
    filepath = os.path.join("agent_traces", f"{safe_name}.json")

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(trace, f, indent=2, ensure_ascii=False)

TEST_QUERIES = [
    "What is the weather in Tokyo right now, and what is Japan's population?",
    "Tell me about the Eiffel Tower and what the weather is like there today.",
    "What is the capital of Brazil, and what is it known for?",
    "Compare the area of Canada and Russia in square kilometers. Which is larger?",
    "If Germany has a population of X million people and France has Y million, what is the combined population? Use real numbers.",
]

def run_all_tests(verbose: bool = False):
    results = []
    for i, query in enumerate(TEST_QUERIES):
        print(f"\n[{i+1}/5] {query[:60]}...")
        answer = run_agent(query, verbose=verbose)
        print(f"Answer: {answer[:200]}...")
        results.append({"query": query, "answer": answer})
    return results

if __name__=="__main__":
    parser = argparse.ArgumentParser(description="LLM Agent with tool use")
    parser.add_argument("--query", type=str, help="Question to ask the agent")
    parser.add_argument("--test-all", action="store_true", help="Run all 5 test queries")
    parser.add_argument("--verbose", action="store_true", help="Show tool calls as they happen")
    args = parser.parse_args()

    if args.query:
        print(f"\nQuery: {args.query}\n")
        answer = run_agent(args.query, verbose=args.verbose)
        print(f"\nAnswer:\n{answer}")
    elif args.test_all:
        run_all_tests(verbose=args.verbose)
    else:
        print("Usage:")
        print("  python src/agent.py --query \"your question here\"")
        print("  python src/agent.py --query \"your question\" --verbose")
        print("  python src/agent.py --test-all")
        print("  python src/agent.py --test-all --verbose")