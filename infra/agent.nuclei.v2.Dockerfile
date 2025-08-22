FROM projectdiscovery/nuclei:latest
RUN apk add --no-cache python3 py3-pip
RUN pip3 install --no-cache-dir requests==2.32.3
WORKDIR /app
COPY agents/nuclei_agent_v2 /app/agent
CMD ["python3","/app/agent/agent.py"]
