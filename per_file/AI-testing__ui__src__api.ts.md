# File: AI-testing/ui/src/api.ts

- Size: 4290 bytes
- Kind: text
- SHA256: a6c5f94a3ef503810c6a372ce2a18aaeb364384a37a6b5201b49f4e35d595446

## Head (first 60 lines)

```

const ORCH_URL = import.meta.env.VITE_ORCH_URL || 'http://localhost:8080';

let DEV_USER = import.meta.env.VITE_DEV_USER || 'dev';
let DEV_EMAIL = import.meta.env.VITE_DEV_EMAIL || 'dev@example.com';
let TENANT = import.meta.env.VITE_TENANT_ID || 't_demo';

export function setDevHeaders(u: string, e: string, t: string) {
  DEV_USER = u; DEV_EMAIL = e; TENANT = t;
}

function headers(extra: Record<string,string> = {}) {
  return {
    'Content-Type': 'application/json',
    'X-Dev-User': DEV_USER,
    'X-Dev-Email': DEV_EMAIL,
    'X-Tenant-Id': TENANT,
    ...extra
  };
}

export async function getCatalog() {
  const r = await fetch(`${ORCH_URL}/v1/catalog`, { headers: headers() });
  if (!r.ok) throw new Error('catalog fetch failed');
  return r.json();
}

export async function getPacks() {
  const r = await fetch(`${ORCH_URL}/v1/catalog/packs`, { headers: headers() });
  if (!r.ok) return { packs: [] };
  return r.json();
}

export async function createEngagement(body: any) {
  const r = await fetch(`${ORCH_URL}/v1/engagements`, { method: 'POST', headers: headers(), body: JSON.stringify(body) });
  if (!r.ok) throw await r.json();
  return r.json();
}

export async function validatePlan(engId: string, body: any) {
  const r = await fetch(`${ORCH_URL}/v2/engagements/${engId}/plan/validate`, { method: 'POST', headers: headers(), body: JSON.stringify(body) });
  return r.json();
}

export async function previewPlan(engId: string, body: any) {
  const r = await fetch(`${ORCH_URL}/v2/engagements/${engId}/plan/preview`, { method: 'POST', headers: headers(), body: JSON.stringify(body) });
  return r.json();
}

export async function createPlan(engId: string, body: any) {
  const r = await fetch(`${ORCH_URL}/v1/engagements/${engId}/plan`, { method: 'POST', headers: headers(), body: JSON.stringify(body) });
  if (!r.ok) throw await r.json();
  return r.json();
}

export async function startRun(body: any) {
  const r = await fetch(`${ORCH_URL}/v1/tests`, { method: 'POST', headers: headers(), body: JSON.stringify(body) });
  if (!r.ok) throw await r.json();
  return r.json();
}
```

## Tail (last 60 lines)

```
  const r = await fetch(`${ORCH_URL}/v1/tests`, { method: 'POST', headers: headers(), body: JSON.stringify(body) });
  if (!r.ok) throw await r.json();
  return r.json();
}

export function events(runId: string) {
  const url = `${ORCH_URL}/v2/runs/${runId}/events`;
  return new EventSource(url, { withCredentials: false });
}

export async function setQuota(body: any) {
  const r = await fetch(`${ORCH_URL}/v2/quotas`, { method: 'POST', headers: headers(), body: JSON.stringify(body) });
  return r.json();
}

export async function getQuota(tenant: string) {
  const r = await fetch(`${ORCH_URL}/v2/quotas/${tenant}`, { headers: headers() });
  return r.json();
}

export async function requestApproval(body: any) {
  const r = await fetch(`${ORCH_URL}/v2/approvals`, { method: 'POST', headers: headers(), body: JSON.stringify(body) });
  return r.json();
}

export async function decideApproval(id: string, body: any) {
  const r = await fetch(`${ORCH_URL}/v2/approvals/${id}/decide`, { method: 'POST', headers: headers(), body: JSON.stringify(body) });
  return r.json();
}

export async function listFindings(runId: string) {
  const r = await fetch(`${ORCH_URL}/v2/runs/${runId}/findings`, { headers: headers() });
  if (!r.ok) return { findings: [] };
  return r.json();
}

export async function upsertFindings(runId: string, items: any[]) {
  const r = await fetch(`${ORCH_URL}/v2/runs/${runId}/findings`, { method: 'POST', headers: headers(), body: JSON.stringify(items) });
  return r.json();
}

export async function uploadArtifact(runId: string, file: File, findingId?: string) {
  const form = new FormData();
  form.append('file', file);
  if (findingId) form.append('finding_id', findingId);
  const r = await fetch(`${ORCH_URL}/v2/runs/${runId}/artifacts`, { method: 'POST', headers: { 'X-Dev-User': DEV_USER, 'X-Dev-Email': DEV_EMAIL, 'X-Tenant-Id': TENANT }, body: form });
  return r.json();
}

export function reportURL(runId: string, fmt: 'json'|'md'|'html') {
  return `${ORCH_URL}/v2/reports/run/${runId}.${fmt}`;
}


export async function getArtifactsIndex(runId: string) {
  const r = await fetch(`${ORCH_URL}/v2/runs/${runId}/artifacts/index.json`, { headers: headers() });
  if (r.status === 404) throw new Error('run not found');
  if (!r.ok) throw new Error(`failed to load artifacts index: ${r.status}`);
  return r.json();
}
```

