# File: AI-testing/ui/src/App.tsx

- Size: 14724 bytes
- Kind: text
- SHA256: c3efed14e62fc1d046f091dc0f5fca3787c6ce8857f98ba857bf22ac79dcf402

## Head (first 60 lines)

```

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
```

## Tail (last 60 lines)

```
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
```

