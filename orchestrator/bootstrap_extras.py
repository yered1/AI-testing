from .app_v2 import app
from .routers import v2_quotas_approvals, v2_findings_reports, v2_agents_bus, v2_brain, v2_listings

app.include_router(v2_quotas_approvals.router, tags=["quotas","approvals"])
app.include_router(v2_findings_reports.router, tags=["findings","artifacts","reports"])
app.include_router(v2_agents_bus.router, tags=["agents"])
app.include_router(v2_brain.router, tags=["brain"])
app.include_router(v2_listings.router, tags=["listings"])
