import csv
import io
import logging
from typing import Optional
from bson import ObjectId
from fastapi import HTTPException, status
from pymongo.errors import BulkWriteError
from app.database.mongodb.repositories.lead_repository import LeadRepository
from app.schemas.lead import LeadCreate, LeadListResponse, LeadResponse, LeadUpdate

logger = logging.getLogger("backend.modules.leadfinder")


class LeadFinderModule:
    def __init__(self, lead_repository: LeadRepository):
        self.lead_repo = lead_repository

    async def get_lead(self, lead_id: str, owner_id: str) -> LeadResponse:
        """Retrieve a specific lead with owner validation check."""
        lead = await self.lead_repo.get_by_id(lead_id, owner_id)
        if not lead:
            logger.warning(f"Lead lookup failed: Lead {lead_id} not found for owner {owner_id}.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lead record not found or access denied."
            )
        return LeadResponse.from_orm(lead)

    async def list_leads(
        self,
        owner_id: str,
        page: int = 1,
        limit: int = 20,
        search: Optional[str] = None,
        status_filter: Optional[str] = None,
        min_score: Optional[int] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> LeadListResponse:
        """List and search leads with sorting, filtering, and page parameters."""
        skip = (page - 1) * limit
        leads, total = await self.lead_repo.list_leads(
            owner_id=owner_id,
            skip=skip,
            limit=limit,
            search=search,
            status=status_filter,
            min_score=min_score,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        pages = (total + limit - 1) // limit
        items = [LeadResponse.from_orm(lead) for lead in leads]
        
        return LeadListResponse(
            items=items,
            total_count=total,
            page=page,
            pages=pages,
            limit=limit
        )

    async def create_lead(self, lead_data: LeadCreate, owner_id: str) -> LeadResponse:
        """Create a new lead under the specified owner account."""
        data = lead_data.dict()
        data["owner_id"] = ObjectId(owner_id)
        
        try:
            lead = await self.lead_repo.create(data)
            logger.info(f"Successfully created lead ID: {lead.id} for owner: {owner_id}")
            return LeadResponse.from_orm(lead)
        except Exception as e:
            logger.error(f"Lead creation failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create lead. Ensure a lead with the same name and location doesn't exist."
            )

    async def update_lead(self, lead_id: str, update_data: LeadUpdate, owner_id: str) -> LeadResponse:
        """Update fields of an existing lead checking owner validation."""
        lead = await self.lead_repo.get_by_id(lead_id, owner_id)
        if not lead:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lead record not found or access denied."
            )
            
        data = update_data.dict(exclude_unset=True)
        try:
            updated_lead = await self.lead_repo.update(lead, data)
            logger.info(f"Successfully updated lead ID: {lead_id} for owner: {owner_id}")
            return LeadResponse.from_orm(updated_lead)
        except Exception as e:
            logger.error(f"Lead update failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update lead. Check uniqueness constraints or input values."
            )

    async def delete_lead(self, lead_id: str, owner_id: str) -> dict:
        """Delete a lead record checking owner validation."""
        lead = await self.lead_repo.get_by_id(lead_id, owner_id)
        if not lead:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lead record not found or access denied."
            )
            
        await self.lead_repo.delete(lead)
        logger.info(f"Successfully deleted lead ID: {lead_id} for owner: {owner_id}")
        return {"status": "success", "message": "Lead record successfully deleted."}

    async def import_leads_csv(self, csv_content: str, owner_id: str) -> dict:
        """Parse raw CSV string data and bulk insert leads with validation mapping."""
        # Setup CSV string buffer reader
        csv_file = io.StringIO(csv_content)
        reader = csv.DictReader(csv_file)
        
        if not reader.fieldnames:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CSV file contains no headers."
            )
            
        # Normalize headers to lowercase to match model properties
        field_mapping = {name.lower().strip().replace(" ", "_"): name for name in reader.fieldnames}
        
        leads_to_create = []
        for row_index, row in enumerate(reader, start=1):
            try:
                # Extract columns mapping to standard lead attributes
                name_key = field_mapping.get("name") or field_mapping.get("business_name")
                if not name_key or not row[name_key]:
                    continue  # skip rows missing name
                    
                name = row[name_key].strip()
                website = row.get(field_mapping.get("website") or "") or None
                phone = row.get(field_mapping.get("phone") or "") or None
                email = row.get(field_mapping.get("email") or "") or None
                location = row.get(field_mapping.get("location") or field_mapping.get("address") or "") or None
                
                score_str = row.get(field_mapping.get("score") or "")
                score = int(score_str) if score_str and score_str.isdigit() else None
                
                status_str = row.get(field_mapping.get("status") or "") or "discovered"
                status_val = status_str.strip().lower()
                
                lead_payload = {
                    "owner_id": ObjectId(owner_id),
                    "name": name,
                    "website": website.strip() if website else None,
                    "phone": phone.strip() if phone else None,
                    "email": email.strip() if email else None,
                    "location": location.strip() if location else None,
                    "score": score,
                    "status": status_val
                }
                leads_to_create.append(lead_payload)
            except Exception as row_error:
                logger.warning(f"Skip importing CSV row {row_index} due to parsing error: {str(row_error)}")
                continue
                
        if not leads_to_create:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid leads found in the CSV file."
            )
            
        try:
            inserted_count = await self.lead_repo.bulk_create(leads_to_create)
            logger.info(f"Successfully bulk imported {inserted_count} leads for owner: {owner_id}")
            return {
                "status": "success",
                "message": f"Successfully imported {inserted_count} out of {len(leads_to_create)} leads.",
                "inserted_count": inserted_count
            }
        except BulkWriteError as bwe:
            # Handle duplicate key errors gracefully during bulk insert
            inserted_count = bwe.details.get("nInserted", 0)
            logger.warning(f"Bulk import completed with write errors. Inserted {inserted_count} leads.")
            return {
                "status": "success",
                "message": f"Successfully imported {inserted_count} leads. Some duplicates were skipped.",
                "inserted_count": inserted_count
            }
        except Exception as e:
            logger.error(f"Bulk CSV import failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to bulk insert leads. Verify columns formatting and constraints."
            )

    async def export_leads_csv(self, owner_id: str, status_filter: Optional[str] = None) -> str:
        """Fetch all matched leads under owner scope and render as CSV payload."""
        # Export all matches (retrieve up to 100k records)
        leads, _ = await self.lead_repo.list_leads(
            owner_id=owner_id,
            skip=0,
            limit=100000,
            status=status_filter,
            sort_by="created_at",
            sort_order="desc"
        )
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write CSV headers
        writer.writerow(["Name", "Website", "Phone", "Email", "Location", "Score", "Status", "Created At"])
        
        # Write leads data
        for lead in leads:
            writer.writerow([
                lead.name,
                lead.website or "",
                lead.phone or "",
                lead.email or "",
                lead.location or "",
                lead.score if lead.score is not None else "",
                lead.status,
                lead.created_at.strftime("%Y-%m-%d %H:%M:%S")
            ])
            
        return output.getvalue()
