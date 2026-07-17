"""
Repositories layer for Phase 7 AI Outreach & Sales Automation collections.

Includes:
- EmailAccountRepository
- EmailTemplateRepository
- CampaignRepository
- CampaignStepRepository
- CampaignRecipientRepository
- EmailEventRepository
- EmailAnalyticsRepository
"""
from typing import List, Optional, Tuple
from bson import ObjectId
from app.database.mongodb.collections.outreach import (
    EmailAccount,
    EmailTemplate,
    Campaign,
    CampaignStep,
    CampaignRecipient,
    EmailEvent,
    EmailAnalytics,
)


class EmailAccountRepository:
    """Repository for EmailAccount CRUD operations."""

    async def get_by_id(self, account_id: str, owner_id: str) -> Optional[EmailAccount]:
        try:
            doc = await EmailAccount.get(ObjectId(account_id))
        except Exception:
            doc = await EmailAccount.get(account_id)
        if doc and str(doc.owner_id) == owner_id:
            return doc
        return None

    async def get_by_id_no_auth(self, account_id: str) -> Optional[EmailAccount]:
        try:
            return await EmailAccount.get(ObjectId(account_id))
        except Exception:
            return await EmailAccount.get(account_id)

    async def get_default(self, owner_id: str) -> Optional[EmailAccount]:
        return await EmailAccount.find_one({
            "owner_id": ObjectId(owner_id),
            "is_default": True,
            "is_active": True,
        })

    async def list_by_owner(self, owner_id: str) -> List[EmailAccount]:
        return await EmailAccount.find({"owner_id": ObjectId(owner_id)}).to_list()

    async def create(self, data: dict) -> EmailAccount:
        doc = EmailAccount(**data)
        await doc.insert()
        return doc

    async def update(self, doc: EmailAccount, update_data: dict) -> EmailAccount:
        for field, value in update_data.items():
            if hasattr(doc, field):
                setattr(doc, field, value)
        await doc.update_timestamp()
        return doc

    async def delete(self, doc: EmailAccount) -> bool:
        await doc.delete()
        return True


class EmailTemplateRepository:
    """Repository for EmailTemplate CRUD operations."""

    async def get_by_id(self, template_id: str, owner_id: str) -> Optional[EmailTemplate]:
        try:
            doc = await EmailTemplate.get(ObjectId(template_id))
        except Exception:
            doc = await EmailTemplate.get(template_id)
        if doc and str(doc.owner_id) == owner_id:
            return doc
        return None

    async def list_by_owner(self, owner_id: str) -> List[EmailTemplate]:
        return await EmailTemplate.find({"owner_id": ObjectId(owner_id)}).to_list()

    async def create(self, data: dict) -> EmailTemplate:
        doc = EmailTemplate(**data)
        await doc.insert()
        return doc

    async def update(self, doc: EmailTemplate, update_data: dict) -> EmailTemplate:
        for field, value in update_data.items():
            if hasattr(doc, field):
                setattr(doc, field, value)
        await doc.update_timestamp()
        return doc

    async def delete(self, doc: EmailTemplate) -> bool:
        await doc.delete()
        return True


class CampaignRepository:
    """Repository for Campaign CRUD operations."""

    async def get_by_id(self, campaign_id: str, owner_id: str) -> Optional[Campaign]:
        try:
            doc = await Campaign.get(ObjectId(campaign_id))
        except Exception:
            doc = await Campaign.get(campaign_id)
        if doc and str(doc.owner_id) == owner_id:
            return doc
        return None

    async def get_by_id_no_auth(self, campaign_id: str) -> Optional[Campaign]:
        try:
            return await Campaign.get(ObjectId(campaign_id))
        except Exception:
            return await Campaign.get(campaign_id)

    async def list_by_owner(self, owner_id: str) -> List[Campaign]:
        return await Campaign.find({"owner_id": ObjectId(owner_id)}).to_list()

    async def list_active_campaigns(self) -> List[Campaign]:
        return await Campaign.find({"status": "active"}).to_list()

    async def create(self, data: dict) -> Campaign:
        doc = Campaign(**data)
        await doc.insert()
        return doc

    async def update(self, doc: Campaign, update_data: dict) -> Campaign:
        for field, value in update_data.items():
            if hasattr(doc, field):
                setattr(doc, field, value)
        await doc.update_timestamp()
        return doc

    async def delete(self, doc: Campaign) -> bool:
        await doc.delete()
        return True


class CampaignStepRepository:
    """Repository for CampaignStep CRUD operations."""

    async def list_by_campaign(self, campaign_id: str) -> List[CampaignStep]:
        try:
            cid = ObjectId(campaign_id)
        except Exception:
            cid = campaign_id
        return await CampaignStep.find({"campaign_id": cid}).sort([("step_number", 1)]).to_list()

    async def get_step_by_number(self, campaign_id: str, step_number: int) -> Optional[CampaignStep]:
        try:
            cid = ObjectId(campaign_id)
        except Exception:
            cid = campaign_id
        return await CampaignStep.find_one({"campaign_id": cid, "step_number": step_number})

    async def create(self, data: dict) -> CampaignStep:
        doc = CampaignStep(**data)
        await doc.insert()
        return doc

    async def delete_by_campaign(self, campaign_id: str) -> None:
        try:
            cid = ObjectId(campaign_id)
        except Exception:
            cid = campaign_id
        await CampaignStep.find({"campaign_id": cid}).delete()


class CampaignRecipientRepository:
    """Repository for CampaignRecipient CRUD operations."""

    async def get_by_id(self, recipient_id: str) -> Optional[CampaignRecipient]:
        try:
            return await CampaignRecipient.get(ObjectId(recipient_id))
        except Exception:
            return await CampaignRecipient.get(recipient_id)

    async def get_by_unsubscribe_token(self, token: str) -> Optional[CampaignRecipient]:
        return await CampaignRecipient.find_one({"unsubscribe_token": token})

    async def list_by_campaign(self, campaign_id: str, owner_id: str) -> List[CampaignRecipient]:
        try:
            cid = ObjectId(campaign_id)
            oid = ObjectId(owner_id)
        except Exception:
            cid = campaign_id
            oid = owner_id
        return await CampaignRecipient.find({"campaign_id": cid, "owner_id": oid}).to_list()

    async def get_pending_batch(self, campaign_id: str, limit: int = 50) -> List[CampaignRecipient]:
        try:
            cid = ObjectId(campaign_id)
        except Exception:
            cid = campaign_id
        return await CampaignRecipient.find({
            "campaign_id": cid,
            "status": {"$in": ["pending", "opened", "clicked"]}
        }).limit(limit).to_list()

    async def create_many(self, recipients_data: List[dict]) -> int:
        if not recipients_data:
            return 0
        docs = [CampaignRecipient(**d) for d in recipients_data]
        res = await CampaignRecipient.insert_many(docs)
        return len(res.inserted_ids)

    async def update(self, doc: CampaignRecipient, update_data: dict) -> CampaignRecipient:
        for field, value in update_data.items():
            if hasattr(doc, field):
                setattr(doc, field, value)
        await doc.update_timestamp()
        return doc


class EmailEventRepository:
    """Repository for EmailEvent CRUD operations."""

    async def create(self, data: dict) -> EmailEvent:
        doc = EmailEvent(**data)
        await doc.insert()
        return doc

    async def list_by_campaign(self, campaign_id: str, owner_id: str) -> List[EmailEvent]:
        try:
            cid = ObjectId(campaign_id)
            oid = ObjectId(owner_id)
        except Exception:
            cid = campaign_id
            oid = owner_id
        return await EmailEvent.find({"campaign_id": cid, "owner_id": oid}).sort([("timestamp", -1)]).to_list()

    async def count_by_type(self, campaign_id: str, event_type: str) -> int:
        try:
            cid = ObjectId(campaign_id)
        except Exception:
            cid = campaign_id
        return await EmailEvent.find({"campaign_id": cid, "event_type": event_type}).count()


class EmailAnalyticsRepository:
    """Repository for EmailAnalytics CRUD operations."""

    async def get_by_campaign(self, campaign_id: str, owner_id: str) -> Optional[EmailAnalytics]:
        try:
            cid = ObjectId(campaign_id)
            oid = ObjectId(owner_id)
        except Exception:
            cid = campaign_id
            oid = owner_id
        return await EmailAnalytics.find_one({"campaign_id": cid, "owner_id": oid})

    async def upsert_analytics(self, campaign_id: str, owner_id: str, data: dict) -> EmailAnalytics:
        doc = await self.get_by_campaign(campaign_id, owner_id)
        if not doc:
            doc_data = {
                "campaign_id": ObjectId(campaign_id),
                "owner_id": ObjectId(owner_id),
                **data,
            }
            doc = EmailAnalytics(**doc_data)
            await doc.insert()
        else:
            for field, val in data.items():
                if hasattr(doc, field):
                    setattr(doc, field, val)
            await doc.update_timestamp()
        return doc
