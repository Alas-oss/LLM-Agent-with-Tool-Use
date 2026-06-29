import os
import ast
import json
import requests
from dotenv import load_dotenv

load_dotenv()

OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY")

def get_weather(city: str) -> dict:
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": OPENWEATHER_API_KEY,
        "unit": "metric"
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        return {
            "city": data["name"],
            "temperature_c": data["main"]["temp"],
            "condition": data["weather"][0]["description"],
            "humidity": data["main"]["humidity"]     
        }
    except requests.exceptions.HTTPError:
        if r.status_code == 404:
            return {"error": f"City '{city}' not found"}
        return {"error": f"HTTP error {r.status_code}"}
    except Exception as e:
        return {"error": str(e)}
    
def search_wikipedia(query: str) -> dict:
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{query.replace(' ', '_')}"
    headers = {"User-Agent": "agent-task/1.0 (learning project)"}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 404:
            return {"error": f"No Wikipedia page found for '{query}'"}
        r.raise_for_status()
        data = r.json()
        return {
            "title": data.get("title", ""),
            "summary": data.get("extract", "")[:1500],
            "url": data.get("content_urls", {}).get("desktop", {}).get("page", "")
        }
    except Exception as e:
        return  {"error": str(e)}
    
def calculate(expression: str) -> dict:
    try:
        tree = ast.parse(expression, mode="eval")
        for node in ast.walk(tree):
            if not isinstance(node, (
                ast.Expression. ast.BinOp, ast.UnaryOp, ast.Constant,
                ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow,
                ast.Mod, ast.FloorDiv, ast.USub, ast.UAdd
            )):
                return {"error": "Invalid expression — only math operations allowed"}
        result = eval(compile(tree, "<string>", "eval"))
        return {"expression": expression, "result": result}
    except ZeroDivisionError:
        return {"error": "Division by zero"}
    except Exception as e:
        return{"error": f"Could not evaluate: {str(e)}"}
    
def get_country_info(country: str) -> dict:
    url = f"https://restcountries.com/v3.1/name/{country}"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 404:
            return {"error": f"Country '{country} not found"}
        r.raise_for_status()
        data = r.json()[0]
        currencies = []
        for code, info in data.get("currencies", {}).items():
            currencies.append(f"{info.get('name', code)} ({code})")
        return {
            "country": data.get("name", {}).get("common", country),
            "capital": data.get("capital", ["Unknown"])[0],
            "population": data.get("population", 0),
            "area_km2": data.get("area", 0),
            "currencies": currencies
        }
    except Exception as e:
        return {"error": str(e)}
    
TOOLS = {
    "get_weather": get_weather,
    "Search_wikipedia": search_wikipedia,
    "calculate": calculate,
    "get_country_info": get_country_info,
}

def dispatch_tool(tool_name: str, arguments: dict) -> str:
    if tool_name not in TOOLS:
        return json.dumpts({"Error": f"Unknown tool: {tool_name}"})
    func = TOOLS[tool_name]
    result = func(**arguments)
    return json.dumps(result)
