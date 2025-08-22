FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \ 
    wkhtmltopdf python3 python3-pip && rm -rf /var/lib/apt/lists/*

WORKDIR /app
RUN pip3 install fastapi uvicorn pdfkit

COPY services/reporter /app
EXPOSE 9090
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "9090"]
