# File: AI-testing/orchestrator/ui/static/brain.js

- Size: 1784 bytes
- Kind: text
- SHA256: 2ce7ccec7b156f9424914b9681bc137238f750ad4316b42828480d2fe790c89f

## Head (first 60 lines)

```
async function plan() {
  const tenant = document.getElementById('tenant').value || 't_demo';
  const etype = document.getElementById('etype').value;
  const domains = (document.getElementById('domains').value||'').split(',').map(s=>s.trim()).filter(Boolean);
  const cidrs = (document.getElementById('cidrs').value||'').split(',').map(s=>s.trim()).filter(Boolean);
  const provider = document.getElementById('provider').value;
  const allow_intrusive = document.getElementById('allow_intrusive').checked;
  const scope = { in_scope_domains: domains, in_scope_cidrs: cidrs };
  const res = await fetch('/v3/brain/plan/guarded', {
    method:'POST',
    headers:{'Content-Type':'application/json','X-Tenant-Id': tenant},
    body: JSON.stringify({ engagement_type: etype, scope, tenant_id: tenant, preferences:{provider}, allow_intrusive })
  });
  const data = await res.json();
  window.__brainPlan = { tenant, etype, scope, plan: data };
  document.getElementById('planOut').textContent = JSON.stringify(data, null, 2);
}
document.getElementById('btnPlan').onclick = plan;

async function validate() {
  const p = window.__brainPlan;
  if(!p) return alert('Run Plan first');
  const body = { selected_tests: p.plan.selected_tests, agents: {}, risk_tier: p.plan.risk_tier, params: p.plan.params || {} };
  const r = await fetch(`/v2/engagements/dummy/plan/validate`.replace('dummy', 'ENG_ID'), { method:'POST' });
  // This UI only prepares body; use the Builder page to finalize or add ENG workflow here later.
  alert('Use the Builder page to validate/create plan. (This page focuses on planning)');
}
document.getElementById('btnValidate').onclick = validate;
document.getElementById('btnCreatePlan').onclick = validate;
document.getElementById('btnStartRun').onclick = validate;
```

