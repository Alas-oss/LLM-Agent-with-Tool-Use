# Task 4 - LLM Agent with Tool Use

A research assistant agent that combines weather, Wikipedia, calculator, country facts, and currency conversion tools to answer multi-step questions.

## Setup
1. Clone the repo
2. Create a virtual environmnet: `python -m venv venv`
3. Activate it: `.\venv\Scripts\activate` (Windows) or
4. Install dependencies: `pip install -r requirements.txt` (powershell)
5. Create a `.env` file with your API keys: 
    - GROQ_API_KEY = your_groq_key
    - OPENWEATHER_API_KEY = your_openweather_key

## How to Run
- Test all 5 tools individually: `pytho src/test_tools.py`
- Ask the agent a specific question: `python src/agent.py -- query "your question here" 
    - or `pythoon src/agent.py -- query "your question here" -- verbose` if you want more details on its response
- Run all 5 test queries at the same time: `python src/agent.py --test-all --verbose`

## To Add a New Tool
1. Write the function in `src/tools.py` with a clear docstring
2. Add it to the TOOLS dictionary at the bottom of `tools.py`
3. Add a JSON schema for it to `TOOL_SCHEMAS` in `src/agent.py`
4. Add at least two tests for it in `src/test_tools.py`

## Tools Available and their description

get_weather → Current weather for some city

search_wikipedia → Summary of a Wikipedia topic

calculate → Safely evaluates math expressions

get_country_info → Provides the capital, population, area, currencies

convert_currency → Currency conversion using live rates