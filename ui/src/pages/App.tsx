
import React, { useState, useEffect } from 'react'
import '../styles.css'
import { setDevHeaders, getCatalog, getPacks, createEngagement, validatePlan, previewPlan, createPlan, startRun, events,
  setQuota, getQuota, requestApproval, decideApproval, listFindings, upsertFindings, uploadArtifact, reportURL } from '../api'

type TestItem = { id: string, title?: string, category?: string }

export default function App(){
  const [devUser, setDevUser] = useState(import.meta.env.VITE_DEV_USER || 'yered')
  const [devEmail, setDevEmail] = useState(import.meta.env.VITE_DEV_EMAIL || 'yered@example.com')
  const [tenant, setTenant] = useState(import.meta.env.VITE_TENANT_ID || 't_demo')
  const [catalog, setCatalog] = useState<{items: TestItem[]}>({items: []})
  const [packs, setPacks] = useState<{packs: {id:string,name:string,tests:string[]}[]}>({packs:[]})
  const [engId, setEngId] = useState('')
  const [plan, setPlan] = useState<any[]>([])
  const [riskTier, setRiskTier] = useState('safe_active')
  const [cidr, setCidr] = useState('10.0.0.0/24')
  const [domain, setDomain] = useState('example.com')
  const [runId, setRunId] = useState('')
  const [sseLog, setSseLog] = useState<string[]>([])
  const [quota, setQuotaState] = useState<any>(null)
  const [approvalId, setApprovalId] = useState<string>('')
  const [findings, setFindings] = useState<any[]>([])
  const [newFinding, setNewFinding] = useState<any>({"title":"Sample finding","severity":"low"})

  useEffect(()=>{ setDevHeaders(devUser, devEmail, tenant)},[devUser,devEmail,tenant])

  const loadCatalog = async ()=>{
    const c = await getCatalog(); setCatalog(c)
    const p = await getPacks(); setPacks(p)
  }

  const makeEng = async ()=>{
    const body = { name: "Demo Net", tenant_id: tenant, type: "network",
      scope: { in_scope_domains: [domain], in_scope_cidrs: [cidr], out_of_scope:[], risk_tier: riskTier, windows: [] } }
    const e = await createEngagement(body); setEngId(e.id)
  }

  const addFromPack = (packId: string)=>{
    const p = packs.packs.find(x=>x.id===packId); if (!p) return
    const current = new Set(plan.map(x=>x.id))
    const merged = [...plan]
    p.tests.forEach(t=>{ if(!current.has(t)) merged.push({id:t}) })
    setPlan(merged)
  }

  const validate = async ()=>{
    if(!engId) return alert('Create engagement first')
    const res = await validatePlan(engId, { selected_tests: plan, agents:{}, risk_tier: riskTier })
    alert(JSON.stringify(res, null, 2))
  }

  const preview = async ()=>{
    if(!engId) return alert('Create engagement first')
    const res = await previewPlan(engId, { selected_tests: plan, agents:{}, risk_tier: riskTier })
    alert(JSON.stringify(res, null, 2))
  }

  const createPlanAndRun = async ()=>{
    if(!engId) return alert('Create engagement first')
    const p = await createPlan(engId, { selected_tests: plan, agents:{}, risk_tier: riskTier })
    const r = await startRun({ engagement_id: engId, plan_id: p.id })
    setRunId(r.id)
    const es = events(r.id)
    es.onmessage = (ev)=> setSseLog(prev => [...prev, `${ev.type||'message'}: ${ev.data}`].slice(-200))
    es.addEventListener('step.started', (ev:any)=> setSseLog(prev=>[...prev, `step.started: ${ev.data}`].slice(-200)))
    es.addEventListener('step.completed', (ev:any)=> setSseLog(prev=>[...prev, `step.completed: ${ev.data}`].slice(-200)))
    es.addEventListener('run.completed', (ev:any)=> setSseLog(prev=>[...prev, `run.completed: ${ev.data}`].slice(-200)))
  }

  const configureQuota = async ()=>{
    const res = await setQuota({ tenant_id: tenant, monthly_budget: 100, per_plan_cap: 30 }); setQuotaState(res)
  }
  const refreshQuota = async ()=>{ const q = await getQuota(tenant); setQuotaState(q) }

  const askApproval = async ()=>{
    if(!engId) return alert('Need engagement id')
    const res = await requestApproval({ tenant_id: tenant, engagement_id: engId, reason: "Allow intrusive tests" })
    setApprovalId(res.id || '')
    alert(JSON.stringify(res, null, 2))
  }
  const approveIt = async ()=>{
    if(!approvalId) return alert('No approval id')
    const res = await decideApproval(approvalId, { tenant_id: tenant, decision: "approved" })
    alert(JSON.stringify(res, null, 2))
  }

  const loadFindings = async ()=>{
    if(!runId) return alert('Start a run first')
    const res = await listFindings(runId); setFindings(res.findings || [])
  }
  const addFinding = async ()=>{
    if(!runId) return alert('Start a run first')
    const res = await upsertFindings(runId, [newFinding])
    await loadFindings()
  }
  const doUpload = async (e:any)=>{
    if(!runId) return alert('Start a run first')
    const file = e.target.files[0]; if(!file) return
    await uploadArtifact(runId, file)
    alert('Uploaded')
  }

  return (
    <div>
      <header>
        <div className="container flex">
          <strong>AI Pentest UI</strong>
          <span className="right small">Tenant:</span>
          <input style={{width:140}} value={tenant} onChange={e=>setTenant(e.target.value)} />
        </div>
      </header>

      <div className="container">
        <div className="card">
          <h3>Dev headers</h3>
          <div className="row">
            <div><label>User</label><input value={devUser} onChange={e=>setDevUser(e.target.value)} /></div>
            <div><label>Email</label><input value={devEmail} onChange={e=>setDevEmail(e.target.value)} /></div>
            <div><label>Tenant</label><input value={tenant} onChange={e=>setTenant(e.target.value)} /></div>
            <div><button onClick={loadCatalog}>Load Catalog</button></div>
          </div>
        </div>

        <div className="grid">
          <div className="card">
            <h3>Engagement</h3>
            <div className="row">
              <div><label>Domain</label><input value={domain} onChange={e=>setDomain(e.target.value)} /></div>
              <div><label>CIDR</label><input value={cidr} onChange={e=>setCidr(e.target.value)} /></div>
              <div><label>Risk Tier</label>
                <select value={riskTier} onChange={e=>setRiskTier(e.target.value)}>
                  <option>recon</option><option>safe_active</option><option>intrusive</option>
                </select>
              </div>
              <div><button onClick={makeEng}>Create</button></div>
            </div>
            <div className="small">Engagement ID: {engId || '—'}</div>
          </div>

          <div className="card">
            <h3>Catalog & Packs</h3>
            <div className="row">
              <select onChange={e=>addFromPack(e.target.value)}>
                <option value="">-- Add from pack --</option>
                {packs.packs.map(p=><option key={p.id} value={p.id}>{p.name}</option>)}
              </select>
              <button onClick={()=>setPlan([])}>Clear selection</button>
            </div>
            <div className="hr" />
            <div className="grid">
              {catalog.items.map(it=>(
                <label key={it.id} className="card" style={{display:'block'}}>
                  <input type="checkbox" checked={!!plan.find(p=>p.id===it.id)} onChange={(e)=>{
                    if(e.target.checked) setPlan([...plan,{id:it.id}])
                    else setPlan(plan.filter(p=>p.id!==it.id))
                  }} /> <strong>{it.id}</strong><div className="small">{it.category||''}</div>
                </label>
              ))}
            </div>
          </div>

          <div className="card">
            <h3>Plan</h3>
            <div className="row">
              <button onClick={validate}>Validate</button>
              <button onClick={preview}>Preview</button>
              <button onClick={createPlanAndRun}>Create & Start</button>
            </div>
            <pre><code>{JSON.stringify(plan,null,2)}</code></pre>
          </div>

          <div className="card">
            <h3>Live Events</h3>
            <div className="sse">
              {sseLog.slice(-20).map((l,i)=>(<div key={i} className="small">{l}</div>))}
            </div>
            <div className="small">Run ID: {runId || '—'}</div>
          </div>

          <div className="card">
            <h3>Quotas & Approvals</h3>
            <div className="row">
              <button onClick={configureQuota}>Set Quota</button>
              <button onClick={refreshQuota}>Refresh</button>
              <button onClick={askApproval}>Request Approval</button>
              <button onClick={approveIt} disabled={!approvalId}>Approve</button>
            </div>
            <pre><code>{JSON.stringify(quota,null,2)}</code></pre>
          </div>

          <div className="card">
            <h3>Findings</h3>
            <div className="row">
              <button onClick={loadFindings}>Load</button>
              <input type="file" onChange={doUpload} />
            </div>
            <div className="row">
              <div style={{flex:1}}>
                <label>New finding (JSON)</label>
                <textarea rows={8} value={JSON.stringify(newFinding,null,2)} onChange={e=>{
                  try{ setNewFinding(JSON.parse(e.target.value)) }catch{}
                }} />
                <button onClick={addFinding}>Upsert</button>
              </div>
              <div style={{flex:1}}>
                <label>Export</label>
                <div className="row">
                  <a className="badge" href={reportURL(runId,'json')} target="_blank">JSON</a>
                  <a className="badge" href={reportURL(runId,'md')} target="_blank">Markdown</a>
                  <a className="badge" href={reportURL(runId,'html')} target="_blank">HTML</a>
                </div>
              </div>
            </div>
            <table><thead><tr><th>Severity</th><th>Title</th></tr></thead><tbody>
              {findings.map(f=>(<tr key={f.id}><td className={'sev-'+f.severity}>{f.severity}</td><td>{f.title}</td></tr>))}
            </tbody></table>
          </div>

        </div>
      </div>

      <footer><div className="container small">UI connected to orchestrator at {import.meta.env.VITE_ORCH_URL || 'http://localhost:8080'}</div></footer>
    </div>
  )
}
