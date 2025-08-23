# File: AI-testing/orchestrator/ui/static/app.js

- Size: 4241 bytes
- Kind: text
- SHA256: 39131a573f156145eee4fadf55fdd14e2bb12e35b314ba5d6e2956781105e23e

## Head (first 60 lines)

```
async function j(url, opts={}) {
  const r = await fetch(url, Object.assign({headers: {'Content-Type':'application/json'}}, opts));
  if (!r.ok) throw new Error(await r.text());
  const ct = r.headers.get('content-type')||'';
  if (ct.includes('application/json')) return await r.json();
  return await r.text();
}
function el(id){return document.getElementById(id)}
function show(id){el(id).classList.remove('hidden')}
function hide(id){el(id).classList.add('hidden')}

let state = { engagementId:null, planId:null, selected_tests:[] };

async function createEngagement(){
  const name = el('engName').value || 'eng';
  const type = el('engType').value || 'web';
  const tenant = el('tenantId').value || 't_demo';
  const domains = (el('domains').value||'').split(',').map(s=>s.trim()).filter(Boolean);
  const cidrs = (el('cidrs').value||'').split(',').map(s=>s.trim()).filter(Boolean);
  const scope = {};
  if (domains.length) scope.in_scope_domains = domains;
  if (cidrs.length) scope.in_scope_cidrs = cidrs;
  const e = await j('/v1/engagements', {method:'POST', body: JSON.stringify({name, tenant_id: tenant, type, scope})});
  state.engagementId = e.id;
  await loadCatalog();
  show('plan-area');
}

async function loadCatalog(){
  const cat = await j('/v1/catalog');
  const testsDiv = el('tests'); testsDiv.innerHTML='';
  (cat.tests || cat.items || []).forEach(t => {
    const id = t.id;
    const row = document.createElement('div');
    row.className='row';
    row.innerHTML = `<label><input type="checkbox" value="${id}" onchange="toggleTest('${id}',this.checked)"> ${id} — ${t.title||''}</label>`;
    testsDiv.appendChild(row);
  });
}

function toggleTest(id, checked){
  const idx = state.selected_tests.findIndex(x=>x.id===id);
  if (checked && idx<0) state.selected_tests.push({id, params:{}});
  if (!checked && idx>=0) state.selected_tests.splice(idx,1);
}

async function autoPlan(){
  const body = {}; // could include packs later
  const res = await j(`/v2/engagements/${state.engagementId}/plan/auto`, {method:'POST', body: JSON.stringify(body)});
  state.selected_tests = (res.selected_tests||[]).map(x=>({id:x.id, params:x.params||{}}));
  // tick checkboxes
  document.querySelectorAll('#tests input[type=checkbox]').forEach(cb => {
    cb.checked = state.selected_tests.some(x=>x.id===cb.value);
  });
}

async function validatePlan(){
  const risk_tier = el('riskTier').value;
  const body = {selected_tests: state.selected_tests, agents:{}, risk_tier};
  const v = await j(`/v2/engagements/${state.engagementId}/plan/validate`, {method:'POST', body: JSON.stringify(body)});
```

## Tail (last 60 lines)

```
  const res = await j(`/v2/engagements/${state.engagementId}/plan/auto`, {method:'POST', body: JSON.stringify(body)});
  state.selected_tests = (res.selected_tests||[]).map(x=>({id:x.id, params:x.params||{}}));
  // tick checkboxes
  document.querySelectorAll('#tests input[type=checkbox]').forEach(cb => {
    cb.checked = state.selected_tests.some(x=>x.id===cb.value);
  });
}

async function validatePlan(){
  const risk_tier = el('riskTier').value;
  const body = {selected_tests: state.selected_tests, agents:{}, risk_tier};
  const v = await j(`/v2/engagements/${state.engagementId}/plan/validate`, {method:'POST', body: JSON.stringify(body)});
  el('validateOut').textContent = JSON.stringify(v,null,2);
}

async function createPlan(){
  const risk_tier = el('riskTier').value;
  const body = {selected_tests: state.selected_tests, agents:{}, risk_tier};
  const res = await j(`/v1/engagements/${state.engagementId}/plan`, {method:'POST', body: JSON.stringify(body)});
  state.planId = res.id;
  alert('Plan created: '+state.planId);
}

async function startRun(){
  const res = await j('/v1/tests', {method:'POST', body: JSON.stringify({engagement_id: state.engagementId, plan_id: state.planId})});
  const runId = res.id;
  window.location = `/ui/runs/${runId}`;
}

function openReport(runId, kind){
  window.open(`/v2/reports/run/${runId}.${kind}`, '_blank');
}
function openBundle(runId){
  window.open(`/v2/reports/run/${runId}.zip`, '_blank');
}

async function loadArtifacts(runId){
  try{
    const idx = await j(`/v2/runs/${runId}/artifacts/index.json`);
    const ul = el('artifactList'); ul.innerHTML='';
    (idx.artifacts||[]).forEach(a=>{
      const li=document.createElement('li');
      li.innerHTML = `<code>${a.label||a.name||''}</code> — <small>${a.path||''}</small>`;
      ul.appendChild(li);
    });
  }catch(e){
    console.error(e);
    alert('No artifacts yet or endpoint not available.');
  }
}

// SSE on run page
document.addEventListener('DOMContentLoaded', () => {
  const ev = el('events');
  if (window.RUN_ID && ev){
    const es = new EventSource(`/v2/runs/${window.RUN_ID}/events`);
    es.onmessage = (m) => { ev.textContent += (m.data || '') + "\n"; ev.scrollTop = ev.scrollHeight; };
    es.onerror = () => { /* ignore */ };
  }
});
```

