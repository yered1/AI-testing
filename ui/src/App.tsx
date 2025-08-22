import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react'

type DevHeaders = { user: string; email: string; tenant: string }
const defaultHeaders: DevHeaders = {
  user: localStorage.getItem('dev_user') || 'yered',
  email: localStorage.getItem('dev_email') || 'yered@example.com',
  tenant: localStorage.getItem('dev_tenant') || 't_demo'
}

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8080'

async function api(path: string, opts: RequestInit = {}, dev: DevHeaders = defaultHeaders) {
  const headers: any = {
    'Content-Type': 'application/json',
    'X-Dev-User': dev.user,
    'X-Dev-Email': dev.email,
    'X-Tenant-Id': dev.tenant,
    ...(opts.headers || {})
  }
  const res = await fetch(`${API_BASE}${path}`, { ...opts, headers })
  if (!res.ok) {
    const text = await res.text().catch(()=>'')
    throw new Error(`HTTP ${res.status}: ${text}`)
  }
  const ct = res.headers.get('content-type') || ''
  if (ct.includes('application/json')) return res.json()
  return res.text()
}

async function streamEvents(path: string, onEvent: (evt: {event: string, data: any}) => void, dev: DevHeaders) {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'GET',
    headers: {
      'X-Dev-User': dev.user,
      'X-Dev-Email': dev.email,
      'X-Tenant-Id': dev.tenant
    }
  })
  if (!res.ok || !res.body) throw new Error(`Stream failed: ${res.status}`)
  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buf = ''
  while (true) {
    const {done, value} = await reader.read()
    if (done) break
    buf += decoder.decode(value, {stream:true})
    let idx
    while ((idx = buf.indexOf('\n\n')) >= 0) {
      const chunk = buf.slice(0, idx)
      buf = buf.slice(idx + 2)
      const lines = chunk.split('\n')
      let event = 'message'
      let data = ''
      for (const line of lines) {
        if (line.startsWith('event:')) event = line.slice(6).trim()
        if (line.startsWith('data:')) data += line.slice(5).trim()
      }
      if (data) {
        try { onEvent({event, data: JSON.parse(data)}) }
        catch { onEvent({event, data}) }
      }
    }
  }
}

export default function App() {
  const [dev, setDev] = useState<DevHeaders>(defaultHeaders)
  const [catalog, setCatalog] = useState<any[]>([])
  const [packs, setPacks] = useState<any[]>([])
  const [eng, setEng] = useState<any>(null)
  const [planId, setPlanId] = useState<string>('')
  const [runId, setRunId] = useState<string>('')
  const [selected, setSelected] = useState<Record<string, boolean>>({})
  const [validateRes, setValidateRes] = useState<any>(null)
  const [events, setEvents] = useState<{event:string,data:any}[]>([])
  const [file, setFile] = useState<File | null>(null)
  const [findingId, setFindingId] = useState<string>('')

  const selList = useMemo(() => Object.keys(selected).filter(k => selected[k]).map(id => ({id, params:{}})), [selected])

  const saveDev = (d: DevHeaders) => {
    localStorage.setItem('dev_user', d.user)
    localStorage.setItem('dev_email', d.email)
    localStorage.setItem('dev_tenant', d.tenant)
    setDev(d)
  }

  const loadCatalog = useCallback(async () => {
    const cat = await api('/v1/catalog', {method:'GET'}, dev)
    setCatalog(cat.items || [])
    try {
      const ps = await api('/v1/catalog/packs', {method: 'GET'}, dev)
      setPacks(ps.packs || [])
    } catch {}
  }, [dev])

  useEffect(() => { loadCatalog().catch(console.error) }, [loadCatalog])

  const createEng = async () => {
    const body = {
      name: 'Demo Engagement',
      tenant_id: dev.tenant,
      type: 'network',
      scope: { in_scope_domains: ['example.com'], in_scope_cidrs: ['10.0.0.0/24'], out_of_scope: [], risk_tier: 'safe_active', windows: [] }
    }
    const e = await api('/v1/engagements', {method:'POST', body: JSON.stringify(body)}, dev)
    setEng(e)
  }

  const toggle = (id: string) => setSelected(s => ({...s, [id]: !s[id]}))

  const validatePlan = async () => {
    if (!eng) return
    const body = { selected_tests: selList, agents:{strategy:'recommended'}, risk_tier: 'safe_active' }
    const res = await api(`/v2/engagements/${eng.id}/plan/validate`, {method:'POST', body: JSON.stringify(body)}, dev)
    setValidateRes(res)
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
    setRunId(res.id)
    setEvents([])
    // start streaming
    streamEvents(`/v2/runs/${res.id}/events`, (evt) => setEvents(prev => [...prev, evt]), dev).catch(console.error)
  }

  const controlRun = async (action: 'pause'|'resume'|'abort') => {
    if (!runId) return
    await api(`/v2/runs/${runId}/control`, {method:'POST', body: JSON.stringify({action})}, dev)
  }

  const uploadArtifact = async () => {
    if (!runId || !file) return
    const fd = new FormData()
    if (findingId) fd.append('finding_id', findingId)
    fd.append('file', file)
    const res = await fetch(`${API_BASE}/v2/runs/${runId}/artifacts`, {
      method: 'POST',
      headers: {
        'X-Dev-User': dev.user,
        'X-Dev-Email': dev.email,
        'X-Tenant-Id': dev.tenant
      },
      body: fd
    })
    if (!res.ok) throw new Error('upload failed')
    alert('Uploaded')
  }

  const exportReport = async (fmt: 'json'|'md'|'html') => {
    if (!runId) return
    const res = await fetch(`${API_BASE}/v2/reports/run/${runId}.${fmt}`, {
      headers: {'X-Dev-User': dev.user, 'X-Dev-Email': dev.email, 'X-Tenant-Id': dev.tenant}
    })
    const blob = await res.blob()
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = `report.${fmt}`
    a.click()
    URL.revokeObjectURL(a.href)
  }

  return (
    <div style={{fontFamily:'system-ui, -apple-system, Segoe UI, Roboto, sans-serif', padding:'24px', maxWidth: 1100, margin:'0 auto'}}>
      <h1>AI Testing Platform — UI</h1>

      <section style={{border:'1px solid #eee', padding:'12px', borderRadius:8, marginBottom:16}}>
        <h2>Dev Headers</h2>
        <div style={{display:'flex', gap:8}}>
          <input placeholder="User" value={dev.user} onChange={e=>saveDev({...dev, user:e.target.value})}/>
          <input placeholder="Email" value={dev.email} onChange={e=>saveDev({...dev, email:e.target.value})}/>
          <input placeholder="Tenant" value={dev.tenant} onChange={e=>saveDev({...dev, tenant:e.target.value})}/>
        </div>
        <small>API Base: {API_BASE}</small>
      </section>

      <section style={{border:'1px solid #eee', padding:'12px', borderRadius:8, marginBottom:16}}>
        <h2>Engagement</h2>
        <button onClick={createEng}>Create Demo Engagement</button>
        {eng && <div style={{marginTop:8}}>Engagement ID: <code>{eng.id}</code></div>}
      </section>

      <section style={{border:'1px solid #eee', padding:'12px', borderRadius:8, marginBottom:16}}>
        <h2>Catalog & Packs</h2>
        {packs.length>0 && (
          <div style={{marginBottom:8}}>
            <strong>Packs:</strong> {packs.map((p:any)=> <button key={p.id} onClick={()=>{
              const next = {...selected}
              for (const t of p.tests) next[t] = true
              setSelected(next)
            }} style={{marginRight:6}}>{p.name}</button>)}
          </div>
        )}
        <div style={{display:'grid', gridTemplateColumns:'repeat(auto-fill, minmax(260px, 1fr))', gap:8}}>
          {catalog.map((item:any)=>(
            <label key={item.id} style={{border:'1px solid #ddd', borderRadius:6, padding:8}}>
              <input type="checkbox" checked={!!selected[item.id]} onChange={()=>toggle(item.id)} />{' '}
              <strong>{item.title || item.id}</strong><br/>
              <small>{item.description || ''}</small><br/>
              <small>Risk: {item.risk_tier || 'n/a'}</small>
            </label>
          ))}
        </div>
      </section>

      <section style={{border:'1px solid #eee', padding:'12px', borderRadius:8, marginBottom:16}}>
        <h2>Plan</h2>
        <div style={{display:'flex', gap:8, flexWrap:'wrap'}}>
          <button onClick={validatePlan} disabled={!eng || selList.length===0}>Validate & Estimate</button>
          <button onClick={createPlan} disabled={!eng || selList.length===0}>Create Plan</button>
        </div>
        {validateRes && (
          <pre style={{whiteSpace:'pre-wrap', background:'#f7f7f7', padding:8, borderRadius:6, marginTop:8}}>
{JSON.stringify(validateRes, null, 2)}
          </pre>
        )}
        {planId && <div>Plan ID: <code>{planId}</code></div>}
      </section>

      <section style={{border:'1px solid #eee', padding:'12px', borderRadius:8, marginBottom:16}}>
        <h2>Run</h2>
        <div style={{display:'flex', gap:8, flexWrap:'wrap'}}>
          <button onClick={startRun} disabled={!planId}>Start Run</button>
          <button onClick={()=>controlRun('pause')} disabled={!runId}>Pause</button>
          <button onClick={()=>controlRun('resume')} disabled={!runId}>Resume</button>
          <button onClick={()=>controlRun('abort')} disabled={!runId}>Abort</button>
        </div>
        {runId && <div>Run ID: <code>{runId}</code></div>}
        <div style={{marginTop:8, maxHeight:240, overflow:'auto', background:'#0b1022', color:'#cde3ff', padding:8, borderRadius:6}}>
          {events.map((e,i)=>(
            <div key={i}><strong>{e.event}</strong> — <code>{JSON.stringify(e.data)}</code></div>
          ))}
        </div>
      </section>

      <section style={{border:'1px solid #eee', padding:'12px', borderRadius:8, marginBottom:16}}>
        <h2>Findings & Reports</h2>
        <div style={{display:'flex', gap:8, alignItems:'center', flexWrap:'wrap'}}>
          <input type="text" placeholder="Finding ID (optional for upload)" value={findingId} onChange={e=>setFindingId(e.target.value)} />
          <input type="file" onChange={e=>setFile(e.target.files?.[0] || null)} />
          <button onClick={uploadArtifact} disabled={!runId || !file}>Upload Artifact</button>
          <button onClick={()=>exportReport('json')} disabled={!runId}>Report JSON</button>
          <button onClick={()=>exportReport('md')} disabled={!runId}>Report MD</button>
          <button onClick={()=>exportReport('html')} disabled={!runId}>Report HTML</button>
        </div>
        <div style={{marginTop:8}}>
          <em>Tip:</em> Use the API to POST findings in bulk: <code>/v2/runs/&lt;run_id&gt;/findings</code> (see README).
        </div>
      </section>

      <footer style={{color:'#666', marginTop:24}}>
        <small>UI talks to {API_BASE}. Make sure the orchestrator is running and CORS is allowed (it is by default).</small>
      </footer>
    </div>
  )
}
