
import React, { useCallback, useEffect, useMemo, useState } from 'react'

type DevHeaders = { user: string; email: string; tenant: string }
const API_BASE = (import.meta as any).env?.VITE_API_BASE || 'http://localhost:8080'

const defaultHeaders: DevHeaders = {
  user: localStorage.getItem('dev_user') || 'yered',
  email: localStorage.getItem('dev_email') || 'yered@example.com',
  tenant: localStorage.getItem('dev_tenant') || 't_demo'
}

async function api(path: string, opts: RequestInit = {}, dev: DevHeaders = defaultHeaders) {
  const headers: any = {
    'Content-Type': 'application/json',
    'X-Dev-User': dev.user,
    'X-Dev-Email': dev.email,
    'X-Tenant-Id': dev.tenant,
    ...(opts.headers || {})
  }
  const res = await fetch(`${API_BASE}${path}`, { ...opts, headers })
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`)
  const ct = res.headers.get('content-type') || ''
  return ct.includes('application/json') ? res.json() : res.text()
}

async function stream(path: string, onEvent: (evt: {event: string; data: any}) => void, dev: DevHeaders) {
  const res = await fetch(`${API_BASE}${path}`, { headers: {'X-Dev-User':dev.user,'X-Dev-Email':dev.email,'X-Tenant-Id':dev.tenant} })
  if (!res.body) return
  const reader = res.body.getReader(); const dec = new TextDecoder()
  let buf = ''
  while (true) {
    const {done, value} = await reader.read(); if (done) break
    buf += dec.decode(value, {stream:true})
    let idx
    while ((idx = buf.indexOf('\n\n')) >= 0) {
      const chunk = buf.slice(0, idx); buf = buf.slice(idx+2)
      const lines = chunk.split('\n')
      let event='message', data=''
      for (const l of lines) { if (l.startsWith('event:')) event = l.slice(6).trim(); if (l.startsWith('data:')) data += l.slice(5).trim() }
      if (data) { try { onEvent({event, data: JSON.parse(data)}) } catch { onEvent({event, data}) } }
    }
  }
}

export default function App() {
  const [dev, setDev] = useState<DevHeaders>(defaultHeaders)
  const saveDev = (d: DevHeaders) => { localStorage.setItem('dev_user', d.user); localStorage.setItem('dev_email', d.email); localStorage.setItem('dev_tenant', d.tenant); setDev(d) }

  const [catalog, setCatalog] = useState<any[]>([])
  const [packs, setPacks] = useState<any[]>([])
  const [eng, setEng] = useState<any>(null)
  const [planId, setPlanId] = useState<string>('')
  const [runId, setRunId] = useState<string>('')
  const [selected, setSelected] = useState<Record<string, boolean>>({})
  const [validateRes, setValidateRes] = useState<any>(null)
  const [events, setEvents] = useState<{event:string,data:any}[]>([])
  const [recentRuns, setRecentRuns] = useState<any[]>([])
  const [agents, setAgents] = useState<any[]>([])
  const [token, setToken] = useState<string>('')
  const [approvals, setApprovals] = useState<any[]>([])
  const [quota, setQuota] = useState<any>(null)

  const selList = useMemo(() => Object.keys(selected).filter(k => selected[k]).map(id => ({id, params:{}})), [selected])

  const loadCatalog = useCallback(async () => {
    const cat = await api('/v1/catalog', {method:'GET'}, dev)
    setCatalog(cat.items || [])
    try { const ps = await api('/v1/catalog/packs', {method:'GET'}, dev); setPacks(ps.packs || []) } catch {}
  }, [dev])

  const refresh = useCallback(async () => {
    try { const rr = await api('/v2/runs/recent', {method:'GET'}, dev); setRecentRuns(rr.runs || []) } catch {}
    try { const ag = await api('/v2/agents', {method:'GET'}, dev); setAgents(ag.agents || []) } catch {}
    if (eng) { try { const ap = await api(`/v2/approvals?engagement_id=${eng.id}`, {method:'GET'}, dev); setApprovals(ap.approvals || []) } catch {} }
    try { const q = await api(`/v2/quotas/${dev.tenant}`, {method:'GET'}, dev); setQuota(q || null) } catch {}
  }, [dev, eng])

  useEffect(() => { loadCatalog().catch(console.error); refresh().catch(console.error) }, [loadCatalog, refresh])

  const toggle = (id: string) => setSelected(s => ({...s, [id]: !s[id]}))

  const createEng = async () => {
    const body = { name: 'Demo Engagement', tenant_id: dev.tenant, type: 'network', scope: { in_scope_domains: ['example.com'], in_scope_cidrs: ['10.0.0.0/24'], out_of_scope: [], risk_tier: 'safe_active', windows: [] } }
    const e = await api('/v1/engagements', {method:'POST', body: JSON.stringify(body)}, dev)
    setEng(e)
    refresh().catch(console.error)
  }

  const validatePlan = async () => {
    if (!eng) return
    const body = { selected_tests: selList, agents:{strategy:'recommended'}, risk_tier: 'safe_active' }
    const res = await api(`/v2/engagements/${eng.id}/plan/validate`, {method:'POST', body: JSON.stringify(body)}, dev)
    setValidateRes(res)
  }

  const autoPlan = async () => {
    if (!eng) return
    const res = await api(`/v2/engagements/${eng.id}/plan/auto`, {method:'POST', body: JSON.stringify({preferences:{packs:['pack.standard_network']}, risk_tier:'safe_active'})}, dev)
    const tests = (res.selected_tests || []).map((t:any)=>t.id)
    const next = {...selected}; for (const t of tests) next[t]=true; setSelected(next)
  }

  const createPlan = async () => {
    if (!eng) return
    const body = { selected_tests: selList, agents:{strategy:'recommended'}, risk_tier: 'safe_active' }
    const res = await api(`/v1/engagements/${eng.id}/plan`, {method:'POST', body: JSON.stringify(body)}, dev)
    setPlanId(res.id)
  }

  const startRun = async () => {
    if (!eng || !planId) return
    const res = await api('/v1/tests', {method:'POST', body: JSON.stringify({engagement_id: eng.id, plan_id: planId})}, dev)
    setRunId(res.id); setEvents([])
    stream(`/v2/runs/${res.id}/events`, (evt)=>setEvents(prev=>[...prev, evt]), dev).catch(console.error)
    refresh().catch(console.error)
  }

  const controlRun = async (action: 'pause'|'resume'|'abort') => {
    if (!runId) return
    await api(`/v2/runs/${runId}/control`, {method:'POST', body: JSON.stringify({action})}, dev)
  }

  const createToken = async () => {
    const res = await api('/v2/agent_tokens', {method:'POST', body: JSON.stringify({tenant_id: dev.tenant, name:'ui-token'})}, dev)
    setToken(res.token)
  }

  const requestApproval = async () => {
    if (!eng) return
    await api('/v2/approvals', {method:'POST', body: JSON.stringify({tenant_id: dev.tenant, engagement_id: eng.id, reason:'Enable intrusive checks'})}, dev)
    refresh().catch(console.error)
  }
  const approveFirst = async () => {
    if (!approvals.length) return
    const id = approvals[0].id
    await api(`/v2/approvals/${id}/decide`, {method:'POST', body: JSON.stringify({tenant_id: dev.tenant, decision:'approved'})}, dev)
    refresh().catch(console.error)
  }
  const setQuota = async () => {
    await api('/v2/quotas', {method:'POST', body: JSON.stringify({tenant_id: dev.tenant, monthly_budget: 100, per_plan_cap: 30})}, dev)
    refresh().catch(console.error)
  }

  return (
    <div style={{fontFamily:'system-ui, -apple-system, Segoe UI, Roboto, sans-serif', padding:24, maxWidth: 1200, margin:'0 auto'}}>
      <h1>AI Testing Platform — UI v2</h1>

      <section style={{border:'1px solid #eee', padding:12, borderRadius:8, marginBottom:16}}>
        <h2>Dev Headers</h2>
        <div style={{display:'flex', gap:8}}>
          <input value={dev.user} onChange={e=>saveDev({...dev, user:e.target.value})} placeholder="User" />
          <input value={dev.email} onChange={e=>saveDev({...dev, email:e.target.value})} placeholder="Email" />
          <input value={dev.tenant} onChange={e=>saveDev({...dev, tenant:e.target.value})} placeholder="Tenant" />
        </div>
      </section>

      <section style={{display:'grid', gridTemplateColumns:'1fr 1fr', gap:12, marginBottom:16}}>
        <div style={{border:'1px solid #eee', padding:12, borderRadius:8}}>
          <h2>Engagement</h2>
          <button onClick={createEng}>Create Demo Engagement</button>
          {eng && <div>Engagement: <code>{eng.id}</code></div>}
          <div style={{marginTop:8, display:'flex', gap:8, flexWrap:'wrap'}}>
            <button onClick={autoPlan} disabled={!eng}>Auto‑Plan</button>
            <button onClick={validatePlan} disabled={!eng || selList.length===0}>Validate & Estimate</button>
            <button onClick={createPlan} disabled={!eng || selList.length===0}>Create Plan</button>
          </div>
          {validateRes && <pre style={{marginTop:8, background:'#f7f7f7', padding:8, borderRadius:6}}>{JSON.stringify(validateRes,null,2)}</pre>}
        </div>

        <div style={{border:'1px solid #eee', padding:12, borderRadius:8}}>
          <h2>Quotas & Approvals</h2>
          <div style={{display:'flex', gap:8, flexWrap:'wrap'}}>
            <button onClick={setQuota}>Set Demo Quota</button>
            <button onClick={requestApproval} disabled={!eng}>Request Approval</button>
            <button onClick={approveFirst} disabled={!approvals.length}>Approve First</button>
          </div>
          <div style={{marginTop:8}}><strong>Quota:</strong> <pre style={{background:'#f7f7f7', padding:8}}>{JSON.stringify(quota,null,2)}</pre></div>
          <div><strong>Approvals:</strong> <pre style={{background:'#f7f7f7', padding:8}}>{JSON.stringify(approvals,null,2)}</pre></div>
        </div>
      </section>

      <section style={{border:'1px solid #eee', padding:12, borderRadius:8, marginBottom:16}}>
        <h2>Catalog & Packs</h2>
        <div style={{marginBottom:8}}>
          {packs.map((p:any)=> <button key={p.id} style={{marginRight:6}} onClick={()=>{
            const next = {...selected}; for (const t of p.tests) next[t]=true; setSelected(next)
          }}>{p.name}</button>)}
        </div>
        <div style={{display:'grid', gridTemplateColumns:'repeat(auto-fill, minmax(260px, 1fr))', gap:8}}>
          {catalog.map((item:any)=>(
            <label key={item.id} style={{border:'1px solid #ddd', padding:8, borderRadius:6}}>
              <input type="checkbox" checked={!!selected[item.id]} onChange={()=>setSelected(prev=>({...prev, [item.id]: !prev[item.id]}))} />{' '}
              <strong>{item.title || item.id}</strong><br/>
              <small>{item.description || ''}</small><br/>
              <small>Risk: {item.risk_tier || 'n/a'}</small>
            </label>
          ))}
        </div>
      </section>

      <section style={{display:'grid', gridTemplateColumns:'1fr 1fr', gap:12, marginBottom:16}}>
        <div style={{border:'1px solid #eee', padding:12, borderRadius:8}}>
          <h2>Runs</h2>
          <div style={{display:'flex', gap:8, flexWrap:'wrap'}}>
            <button onClick={startRun} disabled={!planId}>Start Run</button>
            <button onClick={()=>controlRun('pause')} disabled={!runId}>Pause</button>
            <button onClick={()=>controlRun('resume')} disabled={!runId}>Resume</button>
            <button onClick={()=>controlRun('abort')} disabled={!runId}>Abort</button>
          </div>
          <div style={{marginTop:8}}>
            <strong>Plan:</strong> <code>{planId || '—'}</code><br/>
            <strong>Run:</strong> <code>{runId || '—'}</code>
          </div>
          <div style={{marginTop:8, maxHeight:240, overflow:'auto', background:'#0b1022', color:'#cde3ff', padding:8, borderRadius:6}}>
            {events.map((e,i)=>(<div key={i}><strong>{e.event}</strong> — <code>{JSON.stringify(e.data)}</code></div>))}
          </div>
        </div>

        <div style={{border:'1px solid #eee', padding:12, borderRadius:8}}>
          <h2>Recent Runs</h2>
          <button onClick={()=>refresh().catch(console.error)}>Refresh</button>
          <div style={{maxHeight:260, overflow:'auto', marginTop:8}}>
            <table width="100%" style={{borderCollapse:'collapse'}}>
              <thead><tr><th style={{textAlign:'left'}}>Run</th><th style={{textAlign:'left'}}>Engagement</th><th>Status</th><th>Created</th></tr></thead>
              <tbody>
                {recentRuns.map((r:any)=>(
                  <tr key={r.id} style={{borderTop:'1px solid #eee', cursor:'pointer'}} onClick={()=>{setRunId(r.id); setEvents([]); stream(`/v2/runs/${r.id}/events`, (evt)=>setEvents(prev=>[...prev, evt]), dev)}}>
                    <td><code>{r.id}</code></td>
                    <td><code>{r.engagement_id}</code></td>
                    <td>{r.status}</td>
                    <td>{r.created_at}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <section style={{display:'grid', gridTemplateColumns:'1fr 1fr', gap:12, marginBottom:16}}>
        <div style={{border:'1px solid #eee', padding:12, borderRadius:8}}>
          <h2>Agents</h2>
          <div style={{display:'flex', gap:8}}>
            <button onClick={createToken}>Create Enroll Token</button>
            {token && <input readOnly value={token} onFocus={(e)=>e.currentTarget.select()} style={{width:'100%'}}/>}
          </div>
          <div style={{marginTop:8}}>
            <strong>Registered Agents</strong>
            <ul>
              {agents.map((a:any)=>(<li key={a.id}><code>{a.id}</code> — {a.name} — {a.kind} — {a.status} — {a.last_seen}</li>))}
            </ul>
          </div>
        </div>

        <div style={{border:'1px solid #eee', padding:12, borderRadius:8}}>
          <h2>Findings & Reports</h2>
          <div style={{display:'flex', gap:8, flexWrap:'wrap'}}>
            <button onClick={async()=>{
              if (!runId) return
              const f = await api(`/v2/runs/${runId}/findings`, {method:'GET'}, dev)
              alert(JSON.stringify(f, null, 2))
            }}>List Findings</button>
            <button onClick={async()=>{
              if (!runId) return
              const res = await fetch(`${API_BASE}/v2/reports/run/${runId}.md`, {headers: {'X-Dev-User':dev.user, 'X-Dev-Email':dev.email, 'X-Tenant-Id':dev.tenant}})
              const blob = await res.blob(); const a = document.createElement('a')
              a.href = URL.createObjectURL(blob); a.download = 'report.md'; a.click(); URL.revokeObjectURL(a.href)
            }}>Download Report (MD)</button>
            <button onClick={async()=>{
              if (!runId) return
              const res = await fetch(`${API_BASE}/v2/reports/run/${runId}.html`, {headers: {'X-Dev-User':dev.user, 'X-Dev-Email':dev.email, 'X-Tenant-Id':dev.tenant}})
              const blob = await res.blob(); const a = document.createElement('a')
              a.href = URL.createObjectURL(blob); a.download = 'report.html'; a.click(); URL.revokeObjectURL(a.href)
            }}>Download Report (HTML)</button>
          </div>
        </div>
      </section>
    </div>
  )
}
