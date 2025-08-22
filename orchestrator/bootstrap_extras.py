from .app_v2 import app
from .routers import v2_quotas_approvals, v2_findings_reports, v2_agents_bus, v2_brain, v2_listings

app.include_router(v2_quotas_approvals.router, tags=["quotas","approvals"])
app.include_router(v2_findings_reports.router, tags=["findings","artifacts","reports"])
app.include_router(v2_agents_bus.router, tags=["agents"])
app.include_router(v2_brain.router, tags=["brain"])
app.include_router(v2_listings.router, tags=["listings"])

# --- v0.9.5: extra routers (lease2 + agent artifacts) ---
from .routers import v2_agents_bus_lease2, v2_agents_artifacts
app.include_router(v2_agents_bus_lease2.router, tags=["agents"])
app.include_router(v2_agents_artifacts.router, tags=["agents","artifacts"])
from .routers import v2_reports_bundle
app.include_router(v2_reports_bundle.router, tags=["reports"]) 

# --- v0.9.7 UI include ---
from .routers import ui_pages as ui_pages_router
app.include_router(ui_pages_router.router, tags=["ui"])\ntry:\n    ui_pages_router.mount_static(app)\nexcept Exception:\n    pass\n