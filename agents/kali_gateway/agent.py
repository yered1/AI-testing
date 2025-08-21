import os, time, json, uuid, requests

ORCH = os.environ.get("ORCH_URL","http://localhost:8080")
TENANT = os.environ.get("TENANT_ID","t_demo")
AGENT_ID = os.environ.get("AGENT_ID", f"agt_{uuid.uuid4().hex[:8]}")

def main():
    print(f"[agent] starting {AGENT_ID} for tenant {TENANT}, orchestrator={ORCH}")
    # This is a placeholder; in a real agent, you'd register, attest, and poll for jobs.
    while True:
        try:
            health = requests.get(f"{ORCH}/health", timeout=5).json()
            print(f"[agent] heartbeat ok: {health}")
        except Exception as e:
            print(f"[agent] heartbeat failed: {e}")
        time.sleep(5)

if __name__ == "__main__":
    main()
