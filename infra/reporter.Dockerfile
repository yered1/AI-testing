FROM python:3.11-slim
RUN apt-get update && apt-get install -y wkhtmltopdf fonts-dejavu && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY services/reporter /app
RUN pip install --no-cache-dir fastapi==0.111.0 uvicorn==0.30.1
EXPOSE 8080
CMD ["uvicorn","app:app","--host","0.0.0.0","--port","8080"]
