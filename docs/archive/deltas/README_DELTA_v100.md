
# Delta v1.0.0 — Test Builder UI (additive)

Adds a self-serve UI at **/ui/builder** to:
- Create an engagement (tenant, type, scope)
- Browse **catalog** (tests + packs), select via checkboxes
- Optional **per-test params** editor (JSON per test)
- **Validate** → **Create Plan** → **Start Run**
- Quick links to live events, findings, artifacts, and the **Report Bundle** (.zip)

## Apply
```bash
git checkout -b overlay-v100
unzip -o ~/Downloads/ai-testing-overlay-v100.zip
git add -A && git commit -m "v1.0.0 overlay: Test Builder UI (additive)"
bash scripts/enable_ui_builder_v100.sh
bash scripts/merge_readme_v100.sh
```

## Use
Open **http://localhost:8080/ui/builder** (or **:8081** when behind OIDC proxy).
