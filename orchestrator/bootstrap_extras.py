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
from .routers import v2_artifacts_downloads

from .routers import ui_code

app.include_router(v2_artifacts_downloads.router, tags=["artifacts"])

app.include_router(ui_code.router, tags=["ui"])

from .routers import ui_mobile
app.include_router(ui_mobile.router, tags=["ui"])
from .routers import ui_builder

app.include_router(ui_builder.router, tags=["ui"])\ntry:\n    ui_builder.mount_static(app)\nexcept Exception:\n    pass\n
from .routers import v2_reports_enhanced
app.include_router(v2_reports_enhanced.router, tags=["reports"])
# v1.2.0 brain v3 router
from .routers import v3_brain
from .routers import ui_brain, ui_pages, v3_brain_guarded
app.include_router(v3_brain.router, tags=["brain-v3"])
from orchestrator.routers.v3_brain_guarded import router as router_brain_guarded
app.include_router(router_brain_guarded)
from orchestrator.routers.ui_brain import router as router_ui_brain
app.include_router(router_ui_brain)

# auto-added by fix_bootstrap_includes_v141.py
app.include_router(ui_brain.router)
app.include_router(ui_pages.router)
app.include_router(v3_brain_guarded.router)
