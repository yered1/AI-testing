from . import logging_setup
from .app_v2 import app
from .routers import ui_brain
from .routers import ui_builder
from .routers import ui_code
from .routers import ui_mobile
from .routers import ui_pages
from .routers import v2_agents_artifacts
from .routers import v2_agents_bus
from .routers import v2_agents_bus_lease2
from .routers import v2_artifacts_downloads
from .routers import v2_artifacts_index
from .routers import v2_brain
from .routers import v2_findings_reports
from .routers import v2_listings
from .routers import v2_quotas_approvals
from .routers import v2_reports_bundle
from .routers import v2_reports_enhanced
from .routers import v3_brain
from .routers import v3_brain_guarded

app.include_router(ui_brain.router, tags=['ui'])
try:
    ui_brain.mount_static(app)
except Exception:
    pass
app.include_router(ui_builder.router, tags=['ui'])
try:
    ui_builder.mount_static(app)
except Exception:
    pass
app.include_router(ui_code.router, tags=['ui'])
try:
    ui_code.mount_static(app)
except Exception:
    pass
app.include_router(ui_mobile.router, tags=['ui'])
try:
    ui_mobile.mount_static(app)
except Exception:
    pass
app.include_router(ui_pages.router, tags=['ui'])
try:
    ui_pages.mount_static(app)
except Exception:
    pass
app.include_router(v2_agents_artifacts.router, tags=['agents', 'artifacts'])
app.include_router(v2_agents_bus.router, tags=['agents'])
app.include_router(v2_agents_bus_lease2.router, tags=['agents'])
app.include_router(v2_artifacts_downloads.router, tags=['artifacts'])
app.include_router(v2_artifacts_index.router, tags=['artifacts'])
app.include_router(v2_brain.router, tags=['brain'])
app.include_router(v2_findings_reports.router, tags=['findings', 'artifacts', 'reports'])
app.include_router(v2_listings.router, tags=['listings'])
app.include_router(v2_quotas_approvals.router, tags=['quotas', 'approvals'])
app.include_router(v2_reports_bundle.router, tags=['reports'])
app.include_router(v2_reports_enhanced.router, tags=['reports'])
app.include_router(v3_brain.router, tags=['brain-v3'])
app.include_router(v3_brain_guarded.router, tags=['brain-v3'])
