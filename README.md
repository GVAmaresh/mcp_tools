# mcp_tools

### Initialisation after cloning

```bash
python3 -m venv myenv
source myenv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

python mcp_server.py
```


for fastapi
```
python3 -m venv myenv
source myenv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

python server.py
```

explample cli line
```
Test Case 1: Get the forecast for Sringeri, Karnataka
curl -X POST http://127.0.0.1:8000/invoke \
-H "Content-Type: application/json" \
-d '{
    "tool_name": "get_forecast",
    "tool_args": {
        "location": "Sringeri, Karnataka",
        "forecast_days": 5
    }
}'

**Test Case 2: Get current weather using coordinates**
```bash
curl -X POST http://127.0.0.1:8000/invoke \
-H "Content-Type: application/json" \
-d '{
    "tool_name": "get_current_weather",
    "tool_args": {
        "latitude": 13.42,
        "longitude": 75.25
    }
}'

**Test Case 3: Trigger a validation error**
```bash
curl -X POST http://127.0.0.1:8000/invoke \
-H "Content-Type: application/json" \
-d '{
    "tool_name": "get_forecast",
    "tool_args": {}
}'
```

```

docker-compose up --build

docker-compose -f docker-compose.stdio.yml up


```
mcp_tools/
│── mcp_server.py           # Entry point (loads all tools, runs MCP)
│── config.py               # Config (env vars, Redis, RabbitMQ, API keys)
│── requirements.txt        # Python dependencies
│── docker-compose.yml      # Local Docker (Redis, RabbitMQ, Loki, Grafana, etc.)
│── Dockerfile              # Container build for MCP server
│── kubernetes/             # K8s manifests (Deployment, Service, ConfigMap, etc.)
│
├── tools/                  # All MCP tools grouped here
│   ├── __init__.py
│   ├── flight.py
│   ├── weather.py
│   ├── forecast.py
│   ├── places.py
│
├── utils/                  # Shared utilities
│   ├── __init__.py
│   ├── cache.py            # Redis caching helper
│   ├── queue.py            # RabbitMQ producer/consumer
│   ├── logger.py           # Structured logging setup (Loki-compatible)
│   ├── http_client.py      # Reusable async HTTP client
│   ├── error_handler.py    # Custom exceptions, retries
│
├── tests/                  # Testing
│   ├── test_flight.py
│   ├── test_weather.py
│   ├── test_forecast.py
│   ├── test_places.py
│   ├── test_integration.py
│
├── monitoring/             # Monitoring configs
│   ├── prometheus.yml      # Prometheus config
│   ├── grafana_dashboard.json
│   ├── loki-config.yaml
```


### Features Breakdown

- Logging → Use structlog or loguru, output JSON logs → ship to Loki.

- Redis (Caching) → Cache responses (e.g., weather forecast results for 10 mins).

- RabbitMQ (Queueing) → For heavy requests (e.g., flight search), offload jobs.

- Async Handlers → Use httpx.AsyncClient + asyncio.
 
- Error Handling → Custom exceptions + retries (tenacity library is great).

- Swagger Docs → If you expose a REST API for testing/debug (via FastAPI wrapper).

- Monitoring 

    - Prometheus → Metrics

    - Grafana → Dashboards
    
    - Loki → Logs

- Kubernetes → Helm charts or manifests for scaling.

- Testing → pytest-asyncio for async unit tests + integration tests (mock Redis/RabbitMQ).


reference
for iata code
https://raw.githubusercontent.com/datasets/airport-codes/refs/heads/main/data/airport-codes.csv