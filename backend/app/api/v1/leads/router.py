from typing import Optional
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import PlainTextResponse
from app.api.deps import get_current_user, get_lead_finder_module
from app.database.mongodb.collections.user import User
from app.modules.leadfinder.lead_finder_module import LeadFinderModule
from app.schemas.lead import LeadCreate, LeadListResponse, LeadResponse, LeadUpdate

router = APIRouter()


@router.get(
    "",
    response_model=LeadListResponse,
    summary="List, search, filter, and paginate leads"
)
async def list_leads(
    page: int = Query(1, ge=1, description="Current page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search term for name, location, email, website"),
    status: Optional[str] = Query(None, description="Filter by status value"),
    min_score: Optional[int] = Query(None, ge=0, le=100, description="Filter by minimum lead score"),
    sort_by: str = Query("created_at", description="Field name to sort by"),
    sort_order: str = Query("desc", description="Sort order: asc or desc"),
    current_user: User = Depends(get_current_user),
    lead_module: LeadFinderModule = Depends(get_lead_finder_module)
):
    """Retrieve owner-constrained paginated list of leads based on query filters."""
    return await lead_module.list_leads(
        owner_id=str(current_user.id),
        page=page,
        limit=limit,
        search=search,
        status_filter=status,
        min_score=min_score,
        sort_by=sort_by,
        sort_order=sort_order
    )


@router.get(
    "/export",
    summary="Export leads list to CSV format"
)
async def export_leads(
    status: Optional[str] = Query(None, description="Filter by status value to export"),
    current_user: User = Depends(get_current_user),
    lead_module: LeadFinderModule = Depends(get_lead_finder_module)
):
    """Generate and download a CSV containing all matching owner leads."""
    csv_data = await lead_module.export_leads_csv(
        owner_id=str(current_user.id),
        status_filter=status
    )
    
    headers = {
        "Content-Disposition": f"attachment; filename=leadforge_leads_{current_user.full_name.lower().replace(' ', '_')}.csv"
    }
    return PlainTextResponse(content=csv_data, media_type="text/csv", headers=headers)


@router.post(
    "/import",
    summary="Import multiple leads from a CSV file"
)
async def import_leads(
    file: UploadFile = File(..., description="CSV file containing lead columns (Name is required)"),
    current_user: User = Depends(get_current_user),
    lead_module: LeadFinderModule = Depends(get_lead_finder_module)
):
    """Read a CSV file upload, parse row headers, and bulk insert lead items."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Only Excel-compatible CSV files are supported."
        )
        
    try:
        content_bytes = await file.read()
        csv_content = content_bytes.decode("utf-8")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to read file encoding. Ensure file is UTF-8 formatted CSV."
        )
        
    return await lead_module.import_leads_csv(
        csv_content=csv_content,
        owner_id=str(current_user.id)
    )


@router.get(
    "/{id}",
    response_model=LeadResponse,
    summary="Retrieve details of a specific lead"
)
async def get_lead(
    id: str,
    current_user: User = Depends(get_current_user),
    lead_module: LeadFinderModule = Depends(get_lead_finder_module)
):
    """Retrieve owner-constrained details of a single lead by ID."""
    return await lead_module.get_lead(
        lead_id=id,
        owner_id=str(current_user.id)
    )


@router.post(
    "",
    response_model=LeadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new lead"
)
async def create_lead(
    lead_data: LeadCreate,
    current_user: User = Depends(get_current_user),
    lead_module: LeadFinderModule = Depends(get_lead_finder_module)
):
    """Create a new lead record owned by the authenticated user."""
    return await lead_module.create_lead(
        lead_data=lead_data,
        owner_id=str(current_user.id)
    )


@router.put(
    "/{id}",
    response_model=LeadResponse,
    summary="Update details of a lead"
)
async def update_lead(
    id: str,
    update_data: LeadUpdate,
    current_user: User = Depends(get_current_user),
    lead_module: LeadFinderModule = Depends(get_lead_finder_module)
):
    """Update fields on a single lead record after owner verification."""
    return await lead_module.update_lead(
        lead_id=id,
        update_data=update_data,
        owner_id=str(current_user.id)
    )


@router.delete(
    "/{id}",
    summary="Delete a lead record"
)
async def delete_lead(
    id: str,
    current_user: User = Depends(get_current_user),
    lead_module: LeadFinderModule = Depends(get_lead_finder_module)
):
    """Delete a single lead record after verifying owner constraints."""
    return await lead_module.delete_lead(
        lead_id=id,
        owner_id=str(current_user.id)
    )
