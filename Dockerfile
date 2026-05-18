FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir fastapi "uvicorn[standard]" jinja2 python-multipart openpyxl

COPY main.py .
COPY init_db.py .
COPY vpn.xlsx .
COPY templates/ templates/

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
