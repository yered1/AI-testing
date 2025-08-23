FROM alpine:3.19
RUN apk add --no-cache python3 py3-pip wget unzip ca-certificates bash
# Install ProjectDiscovery dnsx and httpx
ENV HTTPX_VER=1.6.6 DNSX_VER=1.2.1
RUN wget -q https://github.com/projectdiscovery/httpx/releases/download/v${HTTPX_VER}/httpx_${HTTPX_VER}_linux_amd64.zip     && unzip httpx_${HTTPX_VER}_linux_amd64.zip -d /usr/local/bin     && chmod +x /usr/local/bin/httpx && rm -f httpx_${HTTPX_VER}_linux_amd64.zip     && wget -q https://github.com/projectdiscovery/dnsx/releases/download/v${DNSX_VER}/dnsx_${DNSX_VER}_linux_amd64.zip     && unzip dnsx_${DNSX_VER}_linux_amd64.zip -d /usr/local/bin     && chmod +x /usr/local/bin/dnsx && rm -f dnsx_${DNSX_VER}_linux_amd64.zip
RUN pip3 install --no-cache-dir requests==2.32.3
WORKDIR /app
COPY agents/web_discovery_agent /app/agent
CMD ["python3","/app/agent/agent.py"]
