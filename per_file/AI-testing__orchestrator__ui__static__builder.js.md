# File: AI-testing/orchestrator/ui/static/builder.js

- Size: 6699 bytes
- Kind: text
- SHA256: d6b1afce0eeb4deeb7b522c4ba419134c7cae9b98ca4a73a617aab1947e3169a

## Head (first 60 lines)

```

(async function(){
  const $ = (s)=>document.querySelector(s);
  const headers = {
    "Content-Type":"application/json",
    // dev headers still honored in dev mode; in prod use OIDC proxy
    "X-Dev-User":"yered",
    "X-Dev-Email":"yered@example.com",
    "X-Tenant-Id": "t_demo"
  };
  const state = { catalog:null, selected:new Set(), params:{}, eng_id:null, plan_id:null, run_id:null };

  function el(tag, attrs={}, inner=""){
    const n = document.createElement(tag);
    Object.entries(attrs).forEach(([k,v])=>n.setAttribute(k,v));
    if (inner) n.innerHTML = inner;
    return n;
  }
  function renderCatalog(){
    $("#catalog_loading").style.display="none";
    $("#catalog_container").style.display="";
    const testsByCat = {};
    (state.catalog.items||[]).forEach(it=>{
      const c = it.category||"misc";
      (testsByCat[c]=testsByCat[c]||[]).push(it);
    });
    const testsList = $("#tests_list"); testsList.innerHTML="";
    Object.keys(testsByCat).sort().forEach(cat=>{
      const h = el("h5",{},cat);
      testsList.appendChild(h);
      testsByCat[cat].forEach(it=>{
        const id = it.id;
        const row = el("div",{"class":"row"});
        const cb = el("input",{type:"checkbox"});
        cb.checked = state.selected.has(id);
        cb.addEventListener("change",()=>{
          if (cb.checked) state.selected.add(id); else state.selected.delete(id);
          renderParamsList();
        });
        const btn = el("button",{"class":"linkbtn"},"edit params");
        btn.addEventListener("click",()=>openParamEditor(id));
        row.appendChild(cb);
        row.appendChild(el("span",{"class":"mono"},id));
        row.appendChild(el("span",{"class":"muted"},it.title||""));
        row.appendChild(btn);
        testsList.appendChild(row);
      });
    });

    // Packs
    const packs = state.catalog.packs||[];
    const packsList = $("#packs_list"); packsList.innerHTML="";
    packs.forEach(p=>{
      const row = el("div",{"class":"row"});
      const cb = el("input",{type:"checkbox"});
      cb.addEventListener("change",()=>{
        (p.tests||[]).forEach(tid=>{
          if (cb.checked) state.selected.add(tid);
          else state.selected.delete(tid);
        });
```

## Tail (last 60 lines)

```
    state.catalog = {items: j.items || [], packs};
    renderCatalog();
  }

  $("#btn_create_eng").addEventListener("click", async ()=>{
    const body = {
      tenant_id: $("#tenant_id").value || "t_demo",
      name: $("#eng_name").value || "demo-eng",
      type: $("#eng_type").value || "web",
      scope: {}
    };
    const domains = ($("#scope_domains").value||"").split(",").map(s=>s.trim()).filter(Boolean);
    const cidrs = ($("#scope_cidrs").value||"").split(",").map(s=>s.trim()).filter(Boolean);
    if (domains.length) body.scope.in_scope_domains = domains;
    if (cidrs.length) body.scope.in_scope_cidrs = cidrs;
    const r = await fetch("/v1/engagements", {method:"POST", headers, body: JSON.stringify(body)});
    const j = await r.json();
    state.eng_id = j.id;
    $("#eng_id_view").innerText = state.eng_id || "";
  });

  $("#btn_validate").addEventListener("click", async ()=>{
    if (!state.eng_id){ alert("Create an engagement first."); return; }
    const steps = [...state.selected].map(id=>({id, params: state.params[id]||undefined}));
    const payload = { selected_tests: steps, agents: {}, risk_tier: $("#risk_tier").value };
    const r = await fetch(`/v2/engagements/${state.eng_id}/plan/validate`, {method:"POST", headers, body: JSON.stringify(payload)});
    const j = await r.json();
    $("#validate_out").innerText = (j.estimated_cost != null) ? `Estimated cost: ${j.estimated_cost}` : "Validated";
    $("#btn_create_plan").disabled = false;
  });

  $("#btn_create_plan").addEventListener("click", async ()=>{
    const steps = [...state.selected].map(id=>({id, params: state.params[id]||undefined}));
    const payload = { selected_tests: steps, agents: {}, risk_tier: $("#risk_tier").value };
    const r = await fetch(`/v1/engagements/${state.eng_id}/plan`, {method:"POST", headers, body: JSON.stringify(payload)});
    const j = await r.json();
    state.plan_id = j.id;
    $("#plan_id_view").innerText = state.plan_id || "";
    $("#btn_start_run").disabled = false;
  });

  $("#btn_start_run").addEventListener("click", async ()=>{
    const r = await fetch(`/v1/tests`, {method:"POST", headers, body: JSON.stringify({engagement_id: state.eng_id, plan_id: state.plan_id})});
    const j = await r.json();
    state.run_id = j.id;
    $("#run_id_view").innerText = state.run_id || "";
    $("#quick_links").innerHTML = `
      <a href="/v2/runs/${state.run_id}/events" target="_blank">Live Events (SSE)</a> ·
      <a href="/v2/runs/${state.run_id}/findings" target="_blank">Findings</a> ·
      <a href="/v2/runs/${state.run_id}/artifacts" target="_blank">Artifacts</a> ·
      <a href="/v2/reports/run/${state.run_id}.html" target="_blank">Report (HTML)</a> ·
      <a href="/v2/reports/run/${state.run_id}.zip" target="_blank">Bundle (.zip)</a>
    `;
  });

  fetchCatalog().catch(e=>{
    $("#catalog_loading").innerText = "Failed to load catalog";
    console.error(e);
  });
})();
```

