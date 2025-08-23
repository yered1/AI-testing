# File: AI-testing/orchestrator/ui/static/mobile.js

- Size: 2777 bytes
- Kind: text
- SHA256: 4538bc981fcbed82344cce850db1edf2efb58f58e7da8588f3a8b30f08ec2d45

## Head (first 60 lines)

```

async function api(path, opt) {
  opt = opt || {};
  opt.headers = Object.assign({
    "Content-Type":"application/json",
  }, opt.headers||{});
  const res = await fetch(path, opt);
  if (!res.ok) throw new Error("API "+path+" -> "+res.status);
  if (res.headers.get("content-type")?.includes("application/json")) return res.json();
  return res.text();
}

async function mobileCreateEng() {
  const name = document.getElementById("eng_name").value || "apk-review";
  const body = {name, tenant_id: (document.getElementById("tenant").value||"t_demo"), type: "mobile", scope: {}};
  const res = await api("/v1/engagements", {method:"POST", body: JSON.stringify(body)});
  document.getElementById("eng_id").textContent = res.id;
}

async function mobileAutoPlan() {
  const eng = document.getElementById("eng_id").textContent;
  if (!eng) { alert("Create an engagement first"); return; }
  const pref = {preferences:{packs:["default_mobile_static"]}};
  const j = await api(`/v2/engagements/${eng}/plan/auto`, {method:"POST", body: JSON.stringify(pref)});
  window.__selected = {selected_tests: j.selected_tests, agents: {}, risk_tier: "safe_passive"};
  alert("Auto plan ready with "+(j.selected_tests||[]).length+" step(s).");
}

async function mobileCreatePlan() {
  const eng = document.getElementById("eng_id").textContent;
  if (!eng) { alert("Create an engagement first"); return; }
  const sel = window.__selected || {selected_tests: [], agents: {}, risk_tier: "safe_passive"};
  const plan = await api(`/v1/engagements/${eng}/plan`, {method:"POST", body: JSON.stringify(sel)});
  document.getElementById("plan_id").textContent = plan.id;
}

async function mobileStartRun() {
  const eng = document.getElementById("eng_id").textContent;
  const plan = document.getElementById("plan_id").textContent;
  if (!eng || !plan) { alert("Need engagement and plan"); return; }
  const run = await api(`/v1/tests`, {method:"POST", body: JSON.stringify({engagement_id: eng, plan_id: plan})});
  document.getElementById("run_id").textContent = run.id;
  alert("Run started: "+run.id);
}

async function uploadApk(ev) {
  ev.preventDefault();
  const run = document.getElementById("run_id").textContent;
  if (!run) { alert("Start a run first"); return; }
  const f = document.getElementById("apk_file").files[0];
  if (!f) { alert("Choose an APK file"); return; }
  const fd = new FormData();
  fd.append("run_id", run);
  fd.append("file", f, f.name);
  const res = await fetch("/ui/mobile/upload", {method:"POST", body: fd});
  if (!res.ok) { alert("Upload failed"); return; }
  alert("APK uploaded to run "+run);
}

function openRun() {
```

## Tail (last 60 lines)

```
    "Content-Type":"application/json",
  }, opt.headers||{});
  const res = await fetch(path, opt);
  if (!res.ok) throw new Error("API "+path+" -> "+res.status);
  if (res.headers.get("content-type")?.includes("application/json")) return res.json();
  return res.text();
}

async function mobileCreateEng() {
  const name = document.getElementById("eng_name").value || "apk-review";
  const body = {name, tenant_id: (document.getElementById("tenant").value||"t_demo"), type: "mobile", scope: {}};
  const res = await api("/v1/engagements", {method:"POST", body: JSON.stringify(body)});
  document.getElementById("eng_id").textContent = res.id;
}

async function mobileAutoPlan() {
  const eng = document.getElementById("eng_id").textContent;
  if (!eng) { alert("Create an engagement first"); return; }
  const pref = {preferences:{packs:["default_mobile_static"]}};
  const j = await api(`/v2/engagements/${eng}/plan/auto`, {method:"POST", body: JSON.stringify(pref)});
  window.__selected = {selected_tests: j.selected_tests, agents: {}, risk_tier: "safe_passive"};
  alert("Auto plan ready with "+(j.selected_tests||[]).length+" step(s).");
}

async function mobileCreatePlan() {
  const eng = document.getElementById("eng_id").textContent;
  if (!eng) { alert("Create an engagement first"); return; }
  const sel = window.__selected || {selected_tests: [], agents: {}, risk_tier: "safe_passive"};
  const plan = await api(`/v1/engagements/${eng}/plan`, {method:"POST", body: JSON.stringify(sel)});
  document.getElementById("plan_id").textContent = plan.id;
}

async function mobileStartRun() {
  const eng = document.getElementById("eng_id").textContent;
  const plan = document.getElementById("plan_id").textContent;
  if (!eng || !plan) { alert("Need engagement and plan"); return; }
  const run = await api(`/v1/tests`, {method:"POST", body: JSON.stringify({engagement_id: eng, plan_id: plan})});
  document.getElementById("run_id").textContent = run.id;
  alert("Run started: "+run.id);
}

async function uploadApk(ev) {
  ev.preventDefault();
  const run = document.getElementById("run_id").textContent;
  if (!run) { alert("Start a run first"); return; }
  const f = document.getElementById("apk_file").files[0];
  if (!f) { alert("Choose an APK file"); return; }
  const fd = new FormData();
  fd.append("run_id", run);
  fd.append("file", f, f.name);
  const res = await fetch("/ui/mobile/upload", {method:"POST", body: fd});
  if (!res.ok) { alert("Upload failed"); return; }
  alert("APK uploaded to run "+run);
}

function openRun() {
  const run = document.getElementById("run_id").textContent;
  if (!run) { alert("No run id"); return; }
  location.href = "/ui/run/"+run;
}
```

