# File: AI-testing/orchestrator/ui/static/code.js

- Size: 2309 bytes
- Kind: text
- SHA256: 27112b82a163939c27048c70d5c82b10d4f31c19f3b2931aa21a1dd034e651cd

## Head (first 60 lines)

```
const API = location.origin.includes('8081') ? 'http://localhost:8081' : 'http://localhost:8080';
let ENG_ID = null, PLAN_ID = null, RUN_ID = null;

async function createEng(){
  const name = document.getElementById('eng_name').value || 'code-review';
  const body = {name, tenant_id: 't_demo', type: 'code', scope: {}};
  const r = await fetch(`${API}/v1/engagements`, {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body)});
  const j = await r.json();
  ENG_ID = j.id; document.getElementById('eng_out').textContent = JSON.stringify(j, null, 2);
}

async function autoPlan(){
  const body = {preferences: {packs: ['default_code_review']}};
  const r = await fetch(`${API}/v2/engagements/${ENG_ID}/plan/auto`, {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body)});
  const j = await r.json();
  window._SEL = {selected_tests: j.selected_tests, agents: {}, risk_tier: 'safe_passive'};
  document.getElementById('plan_out').textContent = JSON.stringify(j, null, 2);
}

async function createPlan(){
  const r = await fetch(`${API}/v1/engagements/${ENG_ID}/plan`, {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(window._SEL)});
  const j = await r.json(); PLAN_ID = j.id; document.getElementById('run_out').textContent = JSON.stringify(j, null, 2);
}

async function startRun(){
  const body = {engagement_id: ENG_ID, plan_id: PLAN_ID};
  const r = await fetch(`${API}/v1/tests`, {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body)});
  const j = await r.json(); RUN_ID = j.id; document.getElementById('run_out').textContent = JSON.stringify(j, null, 2);
}

async function uploadCode(){
  const f = document.getElementById('codefile').files[0];
  const fd = new FormData();
  fd.append('file', f);
  fd.append('label', 'code_package');
  fd.append('kind', 'code');
  const r = await fetch(`${API}/v2/runs/${RUN_ID}/artifacts`, {method:'POST', body: fd});
  const j = await r.json(); document.getElementById('upload_out').textContent = JSON.stringify(j, null, 2);
}

async function listFindings(){
  const r = await fetch(`${API}/v2/runs/${RUN_ID}/findings`);
  const j = await r.json(); document.getElementById('findings_out').textContent = JSON.stringify(j, null, 2);
}
```

