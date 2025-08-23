# File: AI-testing/ui/src/pages/App.tsx

- Size: 10160 bytes
- Kind: text
- SHA256: bad28fd6fff6624d8de90a2e75dac9694688710f7e6d07bad03c8377e3f1e8b3

## Head (first 60 lines)

```

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
```

## Tail (last 60 lines)

```
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
```

