# MCP Tools: The Travel Assistant

A backend service providing travel-related tools for weather, flight searches, and finding places of interest. It can be run as a RESTful API (FastAPI) or a command-line `stdio` application.

## Features

This project is a robust, asynchronous application featuring:

  - **Core**: FastAPI & `asyncio` for high-performance non-blocking I/O.
  - **Services**: Caching with Redis and structured JSON logging.
  - **Deployment**: Fully containerized with Docker and ready for Kubernetes.
  - **Testing**: Includes unit and integration tests with `pytest`.

## Quickstart

### 1\. Prerequisites

  - Python 3.10+
  - Docker & Docker Compose
  - API keys for Google Maps Platform and SerpApi.

### 2\. Local Setup

Follow these steps to run the application locally.

```bash
git clone https://github.com/GVAmaresh/mcp_tools
cd mcp_tools

python3 -m venv myenv
source myenv/bin/activate

pip install -r requirements.txt

cp .env.example .env

```

### 3\. Running the Server

#### FastAPI Server (HTTP API)

Starts a web server on `http://127.0.0.1:8000`.

```bash
uvicorn server:app --reload
```

Access the interactive API docs at `http://127.0.0.1:8000/docs`.

#### MCP Server (Command-Line)

Runs the application directly in your terminal.

```bash
python mcp_server.py
```

## Usage Examples (FastAPI Server)

All examples target the `/invoke` endpoint of the FastAPI server.

#### 1\. Get a 3-day Forecast for the Current Location

```bash
curl -X POST http://127.0.0.1:8000/invoke \
-H "Content-Type: application/json" \
-d '{
    "tool_name": "get_forecast",
    "tool_args": { "location": "Shivamogga", "forecast_days": 3 }
}'
```

#### 2\. Get Current Weather for London

```bash
curl -X POST http://127.0.0.1:8000/invoke \
-H "Content-Type: application/json" \
-d '{
    "tool_name": "get_current_weather",
    "tool_args": { "location": "London" }
}'
```

#### 3\. Search Flights for Next Week (IATA to City), it's working properly

Searches for flights from Chennai (MAA) to Goa for next Thursday.
```bash
curl -X POST http://127.0.0.1:8000/invoke \
-H "Content-Type: application/json" \
-d '{
    "tool_name": "search_flights",
    "tool_args": {
        "origin": "Chennai International Airport",
        "destination": "Dabolim",
        "date": "2025-09-18"
    }
}'
```

#### 3\. Search Flights for Next Week (IATA to City), don;t use this now,still in beta version

Searches for flights from Chennai (MAA) to Goa for next Thursday.

```bash
curl -X POST http://127.0.0.1:8000/invoke \
-H "Content-Type: application/json" \
-d '{
    "tool_name": "search_flights_upgraded",
    "tool_args": {
        "origin": "MAA",
        "destination": "Goa",
        "date": "2025-09-18"
    }
}'
```

#### 4\. Find Restaurants in the Current Location

```bash
curl -X POST http://127.0.0.1:8000/invoke \
-H "Content-Type: application/json" \
-d '{
    "tool_name": "find_places_of_interest",
    "tool_args": {
        "place_name": "Shivamogga, Karnataka",
        "categories": ["restaurant"]
    }
}'
```

#### 5\. Find Tourist Attractions using Coordinates (Bengaluru)

```bash
curl -X POST http://127.0.0.1:8000/invoke \
-H "Content-Type: application/json" \
-d '{
    "tool_name": "find_places_of_interest",
    "tool_args": {
        "latitude": 12.9716,
        "longitude": 77.5946,
        "categories": ["tourist attraction"]
    }
}'
```

#### 6\. Error Case: Flight Search with Invalid Date

This will return an HTTP 400 Validation Error.

```bash
curl -X POST http://127.0.0.1:8000/invoke \
-H "Content-Type: application/json" \
-d '{
    "tool_name": "search_flights_upgraded",
    "tool_args": {
        "origin": "Shivamogga",
        "destination": "New Delhi",
        "date": "20-10-2025"
    }
}'
```

## Usage Examples (MCP Server)

The `stdio` server accepts a single line of JSON as standard input.

#### 1\. Get a 3-day Forecast for Mumbai

```bash
echo '{"tool_name": "get_forecast", "tool_args": {"location": "Mumbai", "forecast_days": 3}}' | python mcp_server.py
```

#### 2\. Search for Flights

```bash
echo '{"tool_name": "search_flights_upgraded", "tool_args": {"origin": "Bengaluru", "destination": "Kolkata", "date": "2025-11-15"}}' | python mcp_server.py
```

#### 3\. Find Places of Interest

```bash
echo '{"tool_name": "find_places_of_interest", "tool_args": {"place_name": "Hampi", "categories": ["historical landmark"]}}' | python mcp_server.py
```

#### 4\. Error Case: Missing Arguments

The server will return a JSON object detailing the validation error.

```bash
echo '{"tool_name": "get_current_weather", "tool_args": {}}' | python mcp_server.py
```

## Running with Docker

Using Docker is the easiest way to run the application with all its services.

1.  **Full Stack (FastAPI + Services):**

    ```bash
    docker-compose up --build
    ```

2.  **Stdio Server Only:**

    ```bash
    docker-compose -f docker-compose.stdio.yml up --build
    ```



[help](tools/flight.py)

```

[help](tools/flight.py)

```

```bash

[help](tools/flight.py)

```