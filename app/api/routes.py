"""
Main API routes for the PRAT application
"""

from fastapi import APIRouter

from app.api.endpoints import invoices, purchase_orders, folder_monitoring

# Create main API router
api_router = APIRouter()

# Include endpoint routers
api_router.include_router(invoices.router, prefix="/invoices", tags=["invoices"])
api_router.include_router(
    purchase_orders.router, prefix="/purchase-orders", tags=["purchase-orders"]
)
api_router.include_router(folder_monitoring.router, prefix="/folder-monitoring", tags=["folder-monitoring"])
