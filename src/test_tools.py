import sys
import os
sys.path.append(os.path.dirname(__file__))

from tools import get_weather, search_wikipedia, calculate, get_country_info, convert_currency

passed = 0
failed = 0

def test(name, condition, detail=""):
    global passed, failed
    if condition:
        print(f"    PASS - {name}")
        passed += 1
    else:
        print(f"    FAIL - {name} {detail}")
        failed += 1

print("\n── Tool 1: get_weather ───────────────────────────────────────")
result = get_weather("London")
test("returns city name", "city" in result)
test("returns temperature", "temperature_c" in result and isinstance(result["temperature_c"], (int, float)))
test("returns condition", "condition" in result and len(result["condition"]) > 0)
test("handles invalid city", "error" in get_weather("ThisCityDoesNotExist12345"))

print("\n── Tool 2: search_wikipedia ──────────────────────────────────")
result = search_wikipedia("Eiffel Tower")
test("returns title", "title" in result and result["title"] != "")
test("returns summary", "summary" in result and len(result["summary"]) > 50)
test("returns url", "url" in result and "wikipedia" in result["url"])
test("handles unknown topic", "error" in search_wikipedia("xyzzy123notarealthing999"))

print("\n── Tool 3: calculate ─────────────────────────────────────────")
result = calculate("2 + 2")
test("basic addition", result.get("result") == 4)
result = calculate("150 * 3 + 22 / 2")
test("complex expression", result.get("result") == 461.0)
test("handles division by zero", "error" in calculate("10 / 0"))
test("blocks non-math input", "error" in calculate("__import__('os')"))

print("\n── Tool 4: get_country_info ──────────────────────────────────")
result = get_country_info("France")
print(f"  Debug: {result}")
test("returns country name", "country" in result)
test("returns capital", "capital" in result and result["capital"] != "")
test("returns population", "population" in result)
test("handles unknown country", "error" in get_country_info("Xqzptlnarniafakecountry45"))

print("\n── Tool 5: convert_currency ────────────────────────────────")
result = convert_currency(100, "USD", "EUR")
test("returns converted amount", "converted_amount" in result)
test("handles invalid currency", "error" in convert_currency(100, "USD", "FAKECODE"))

print(f"\n── Results: {passed} passed, {failed} failed ─────────────────")