# Destination: patches/v2.0.0/orchestrator/bootstrap_extras.py
# Rationale: Fix syntax errors and provide clean router mounting utility
# This allows dynamic router inclusion if needed

"""
Bootstrap extras - utility for mounting all routers dynamically.
"""

from fastapi import FastAPI
import logging

logger = logging.getLogger(__name__)

# Import all routers
from .routers import (
    v2_agents_bus,
    v2_agents_bus_lease2,
    v2_artifacts,
    v2_artifacts_index,
    v2_artifacts_downloads,
    findings_v2,
    v2_findings_reports,
    v2_quotas_approvals,
    v2_listings,
    v2_brain,
    v3_brain,
    v3_brain_guarded,
    ui_pages,
    ui_brain,
    ui_code,
    ui_builder,
    ui_mobile
)

def mount_all_routers(app: FastAPI):
    """
    Mount all available routers to the FastAPI application.
    
    This is useful for dynamic router inclusion or testing.
    """
    
    # V2 routers with /v2 prefix
    v2_routers = [
        (v2_agents_bus, "agents"),
        (v2_agents_bus_lease2, "agents"),
        (v2_artifacts, "artifacts"),
        (v2_artifacts_index, "artifacts"),
        (v2_artifacts_downloads, "artifacts"),
        (findings_v2, "findings"),
        (v2_findings_reports, "reports"),
        (v2_quotas_approvals, "quotas"),
        (v2_listings, "listings"),
        (v2_brain, "brain"),
    ]
    
    for router_module, tag in v2_routers:
        try:
            app.include_router(router_module.router, prefix="/v2", tags=[tag])
            logger.info(f"Mounted v2 router: {router_module.__name__}")
        except Exception as e:
            logger.error(f"Failed to mount v2 router {router_module.__name__}: {e}")
    
    # V3 routers with /v3 prefix
    v3_routers = [
        (v3_brain, "brain"),
        (v3_brain_guarded, "brain"),
    ]
    
    for router_module, tag in v3_routers:
        try:
            app.include_router(router_module.router, prefix="/v3", tags=[tag])
            logger.info(f"Mounted v3 router: {router_module.__name__}")
        except Exception as e:
            logger.error(f"Failed to mount v3 router {router_module.__name__}: {e}")
    
    # UI routers (mixed prefixes)
    ui_routers = [
        (ui_pages, "", "ui"),  # No prefix
        (ui_brain, "/ui", "ui"),
        (ui_code, "/ui", "ui"),
        (ui_builder, "/ui", "ui"),
        (ui_mobile, "/ui", "ui"),
    ]
    
    for router_module, prefix, tag in ui_routers:
        try:
            if prefix:
                app.include_router(router_module.router, prefix=prefix, tags=[tag])
            else:
                app.include_router(router_module.router, tags=[tag])
            logger.info(f"Mounted UI router: {router_module.__name__}")
        except Exception as e:
            logger.error(f"Failed to mount UI router {router_module.__name__}: {e}")
    
    logger.info("All routers mounting attempted")
    return app

def get_router_info():
    """
    Get information about available routers.
    
    Returns a list of router information dictionaries.
    """
    routers = []
    
    # Collect all router modules
    all_modules = [
        ("v2", v2_agents_bus),
        ("v2", v2_agents_bus_lease2),
        ("v2", v2_artifacts),
        ("v2", v2_artifacts_index),
        ("v2", v2_artifacts_downloads),
        ("v2", findings_v2),
        ("v2", v2_findings_reports),
        ("v2", v2_quotas_approvals),
        ("v2", v2_listings),
        ("v2", v2_brain),
        ("v3", v3_brain),
        ("v3", v3_brain_guarded),
        ("ui", ui_pages),
        ("ui", ui_brain),
        ("ui", ui_code),
        ("ui", ui_builder),
        ("ui", ui_mobile),
    ]
    
    for version, module in all_modules:
        try:
            router = module.router
            routes = []
            for route in router.routes:
                if hasattr(route, 'path') and hasattr(route, 'methods'):
                    routes.append({
                        "path": route.path,
                        "methods": list(route.methods) if route.methods else []
                    })
            
            routers.append({
                "module": module.__name__,
                "version": version,
                "route_count": len(routes),
                "routes": routes[:5]  # First 5 routes as sample
            })
        except Exception as e:
            logger.error(f"Error getting info for {module.__name__}: {e}")
            routers.append({
                "module": module.__name__,
                "version": version,
                "error": str(e)
            })
    
    return routers