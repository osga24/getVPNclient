## Run

Use Docker Compose to start the FastAPI app behind `nginx`.

```bash
docker compose up --build -d
```

The service is exposed externally on port `80`, and `nginx` proxies requests to the app on internal port `8000`.
