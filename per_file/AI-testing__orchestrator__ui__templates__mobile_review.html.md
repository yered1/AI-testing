# File: AI-testing/orchestrator/ui/templates/mobile_review.html

- Size: 1367 bytes
- Kind: text
- SHA256: 634c9537745f0de6fa33ace68a4b297e7ade79ba148e3866082a8e42923566e2

## Head (first 60 lines)

```

{% extends "base.html" %}
{% block content %}
<h2>Mobile Static Analysis (APK)</h2>

<ol>
  <li>Create an engagement of type <code>mobile</code> and auto-plan using pack <code>default_mobile_static</code>.</li>
  <li>Create plan and start run.</li>
  <li>Upload an APK labeled <code>mobile_apk</code>.</li>
  <li>Watch live progress and view findings.</li>
</ol>

<div class="card">
  <h3>Quick Actions</h3>
  <div>
    <label>Tenant</label> <input id="tenant" value="t_demo">
    <label>Name</label> <input id="eng_name" value="apk-review">
    <button onclick="mobileCreateEng()">Create Engagement</button>
  </div>
  <div style="margin-top:8px">
    <button onclick="mobileAutoPlan()">Auto Plan (default_mobile_static)</button>
    <button onclick="mobileCreatePlan()">Create Plan</button>
    <button onclick="mobileStartRun()">Start Run</button>
    <span>Engagement ID: <code id="eng_id"></code> Plan ID: <code id="plan_id"></code> Run ID: <code id="run_id"></code></span>
  </div>
  <div style="margin-top:8px">
    <form id="apkForm" onsubmit="uploadApk(event)">
      <input type="file" id="apk_file" accept=".apk" />
      <button type="submit">Upload APK to Run</button>
    </form>
  </div>
  <div style="margin-top:8px">
    <button onclick="openRun()">Open Run Page</button>
  </div>
</div>

<script src="/ui/static/mobile.js"></script>
{% endblock %}
```

