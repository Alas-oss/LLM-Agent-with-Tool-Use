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
        "units": "metric"
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
        allowed = set("0123456789+-*/()., ")
        if not all(c in allowed for c in expression):
            return {"error": "Invalid expression — only math operations allowed"}
        result = eval(expression)
        if not isinstance(result, (int, float)):
            return {"error": "Expression did not return a number"}
        
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
            return {"error": f"Country '{country}' not found"}
        r.raise_for_status()
        data = r.json()

        if isinstance(data, dict) and not data.get("success", True):
            wiki = search_wikipedia(country)
            if "error" not in wiki:
                return {
                    "country": country,
                    "capital": "See Wikipedia",
                    "population": 0,
                    "area_km2": 0,
                    "currencies": [],
                    "note": wiki["summary"][:300]
                }
            return {"error": f"Country API unavailable and Wikipedia fallback failed"}

        if r.status_code == 404:
            return {"error": f"Country '{country}' not found"}

        if not isinstance(data, list):
            return {"error": "Unexpected API response format"}

        match = None
        for entry in data:
            if entry.get("name", {}).get("common", "").lower() == country.lower():
                match = entry
                break
        if match is None:
            match = data[0]

        currencies = []
        for code, info in match.get("currencies", {}).items():
            currencies.append(f"{info.get('name', code)} ({code})")

        capital = match.get("capital", [])
        return {
            "country": match.get("name", {}).get("common", country),
            "capital": capital[0] if capital else "Unkown",
            "population": match.get("population", 0),
            "area_km2": match.get("area", 0),
            "currencies": currencies
        }
    except Exception as e:
        return {"error": str(e)}
    
def convert_currency(amount: float, from_currency: str, to_currency: str) -> dict:
    url = f"https://api.exchangerate-api.com/v4/latest/{from_currency.upper()}"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()

        rates = data.get("rates", {})
        to_code = to_currency.upper()

        if to_code not in rates:
            return {"error": f"Currency '{to_currency}' not found"}

        rate = rates[to_code]
        converted = round(amount * rate, 2)

        return {
            "amount": amount,
            "from": from_currency.upper(),
            "to":to_code,
            "rate": rate,
            "converted_amount": converted
        }
    except Exception as e:
        return {"error": str(e)}
        

TOOLS = {
    "get_weather": get_weather,
    "search_wikipedia": search_wikipedia,
    "calculate": calculate,
    "get_country_info": get_country_info,
    "convert_currency": convert_currency,
}

def dispatch_tool(tool_name: str, arguments: dict) -> str:
    if tool_name not in TOOLS:
        return json.dumps({"error": f"Unknown tool: {tool_name}"})
    func = TOOLS[tool_name]
    result = func(**arguments)
    return json.dumps(result)
