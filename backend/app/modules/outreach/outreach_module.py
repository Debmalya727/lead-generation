"""
Outreach Service Modules orchestrating Phase 7 AI Outreach & Sales Automation.

Modules:
- CampaignModule
- TemplateModule
- SendingModule
- TrackingModule
- AnalyticsModule
- EmailAccountModule
"""
import logging
import secrets
from datetime import datetime, timezone
from typing import Dict, List, Optional
from bson import ObjectId
from fastapi import HTTPException, status

from app.database.mongodb.repositories.outreach_repository import (
    CampaignRepository,
    CampaignStepRepository,
    CampaignRecipientRepository,
    EmailTemplateRepository,
    EmailAccountRepository,
    EmailEventRepository,
    EmailAnalyticsRepository,
)
from app.database.mongodb.repositories.lead_repository import LeadRepository
from app.database.mongodb.repositories.intelligence_repository import IntelligenceRepository
from app.database.mongodb.repositories.scoring_repository import ScoringRepository
from app.email.providers.factory import get_email_provider
from app.modules.outreach.variable_engine import VariableEngine
from app.modules.outreach.tracking_service import TrackingService

logger = logging.getLogger("backend.modules.outreach")


class EmailAccountModule:
    def __init__(self, account_repo: EmailAccountRepository):
        self.account_repo = account_repo

    async def list_accounts(self, owner_id: str) -> List[object]:
        return await self.account_repo.list_by_owner(owner_id)

    async def create_account(self, data: dict, owner_id: str) -> object:
        data["owner_id"] = ObjectId(owner_id)

        # If marked default, un-default other accounts
        if data.get("is_default"):
            accounts = await self.account_repo.list_by_owner(owner_id)
            for acc in accounts:
                if acc.is_default:
                    await self.account_repo.update(acc, {"is_default": False})

        return await self.account_repo.create(data)

    async def delete_account(self, account_id: str, owner_id: str) -> bool:
        doc = await self.account_repo.get_by_id(account_id, owner_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Email account not found")
        return await self.account_repo.delete(doc)

    async def test_account(self, account_id: str, owner_id: str, test_recipient: str) -> dict:
        acc = await self.account_repo.get_by_id(account_id, owner_id)
        if not acc:
            raise HTTPException(status_code=404, detail="Email account not found")

        provider = get_email_provider(acc)
        res = await provider.send_email(
            to_email=test_recipient,
            subject="LeadForgeAI — Test Email Connection",
            body_html="<p>This is a test email confirming your email account integration in LeadForgeAI is active and functional.</p>",
        )
        if not res.success:
            raise HTTPException(status_code=400, detail=f"SMTP test failed: {res.error}")
        return {"status": "success", "message": f"Test email successfully sent to {test_recipient}"}


class TemplateModule:
    def __init__(self, template_repo: EmailTemplateRepository):
        self.template_repo = template_repo

    async def list_templates(self, owner_id: str) -> List[object]:
        return await self.template_repo.list_by_owner(owner_id)

    async def get_template(self, template_id: str, owner_id: str) -> object:
        doc = await self.template_repo.get_by_id(template_id, owner_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Template not found")
        return doc

    async def create_template(self, data: dict, owner_id: str) -> object:
        data["owner_id"] = ObjectId(owner_id)
        subject_vars = VariableEngine.extract_variables(data.get("subject", ""))
        body_vars = VariableEngine.extract_variables(data.get("body", ""))
        data["variables_used"] = list(set(subject_vars + body_vars))
        return await self.template_repo.create(data)

    async def update_template(self, template_id: str, data: dict, owner_id: str) -> object:
        doc = await self.template_repo.get_by_id(template_id, owner_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Template not found")
        subject_vars = VariableEngine.extract_variables(data.get("subject", doc.subject))
        body_vars = VariableEngine.extract_variables(data.get("body", doc.body))
        data["variables_used"] = list(set(subject_vars + body_vars))
        return await self.template_repo.update(doc, data)

    async def delete_template(self, template_id: str, owner_id: str) -> bool:
        doc = await self.template_repo.get_by_id(template_id, owner_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Template not found")
        return await self.template_repo.delete(doc)


class CampaignModule:
    def __init__(
        self,
        campaign_repo: CampaignRepository,
        step_repo: CampaignStepRepository,
        recip_repo: CampaignRecipientRepository,
        lead_repo: LeadRepository,
        analytics_repo: EmailAnalyticsRepository,
    ):
        self.campaign_repo = campaign_repo
        self.step_repo = step_repo
        self.recip_repo = recip_repo
        self.lead_repo = lead_repo
        self.analytics_repo = analytics_repo

    async def list_campaigns(self, owner_id: str) -> List[object]:
        return await self.campaign_repo.list_by_owner(owner_id)

    async def get_campaign_detail(self, campaign_id: str, owner_id: str) -> dict:
        camp = await self.campaign_repo.get_by_id(campaign_id, owner_id)
        if not camp:
            raise HTTPException(status_code=404, detail="Campaign not found")

        steps = await self.step_repo.list_by_campaign(campaign_id)
        recipients = await self.recip_repo.list_by_campaign(campaign_id, owner_id)
        analytics = await self.analytics_repo.get_by_campaign(campaign_id, owner_id)

        return {
            "campaign": camp,
            "steps": steps,
            "recipients_count": len(recipients),
            "analytics": analytics,
        }

    async def create_campaign(self, data: dict, steps_data: List[dict], lead_ids: List[str], owner_id: str) -> object:
        data["owner_id"] = ObjectId(owner_id)

        if data.get("sending_account_id"):
            try:
                data["sending_account_id"] = ObjectId(data["sending_account_id"])
            except Exception:
                pass

        camp = await self.campaign_repo.create(data)

        # Create steps
        for i, sdata in enumerate(steps_data):
            sdata["campaign_id"] = camp.id
            sdata["step_number"] = i + 1
            if sdata.get("template_id"):
                try:
                    sdata["template_id"] = ObjectId(sdata["template_id"])
                except Exception:
                    pass
            await self.step_repo.create(sdata)

        # Enroll lead recipients
        recipients_batch = []
        for lid in lead_ids:
            lead = await self.lead_repo.get_by_id(lid, owner_id)
            if lead and lead.email:
                token = secrets.token_urlsafe(16)
                recipients_batch.append({
                    "campaign_id": camp.id,
                    "lead_id": lead.id,
                    "owner_id": ObjectId(owner_id),
                    "email": lead.email,
                    "first_name": lead.name.split()[0] if lead.name else "There",
                    "company": lead.name,
                    "current_step": 1,
                    "status": "pending",
                    "unsubscribe_token": token,
                })

        if recipients_batch:
            await self.recip_repo.create_many(recipients_batch)

        # Init analytics entry
        await self.analytics_repo.upsert_analytics(
            campaign_id=str(camp.id),
            owner_id=owner_id,
            data={"total_recipients": len(recipients_batch)},
        )

        logger.info(f"Created campaign '{camp.name}' with {len(steps_data)} steps and {len(recipients_batch)} enrolled leads.")
        return camp

    async def update_status(self, campaign_id: str, new_status: str, owner_id: str) -> object:
        camp = await self.campaign_repo.get_by_id(campaign_id, owner_id)
        if not camp:
            raise HTTPException(status_code=404, detail="Campaign not found")

        if new_status not in ["draft", "active", "paused", "completed", "cancelled"]:
            raise HTTPException(status_code=400, detail="Invalid campaign status")

        return await self.campaign_repo.update(camp, {"status": new_status})

    async def delete_campaign(self, campaign_id: str, owner_id: str) -> bool:
        camp = await self.campaign_repo.get_by_id(campaign_id, owner_id)
        if not camp:
            raise HTTPException(status_code=404, detail="Campaign not found")
        await self.step_repo.delete_by_campaign(campaign_id)
        return await self.campaign_repo.delete(camp)


class SendingModule:
    def __init__(
        self,
        campaign_repo: CampaignRepository,
        step_repo: CampaignStepRepository,
        recip_repo: CampaignRecipientRepository,
        account_repo: EmailAccountRepository,
        lead_repo: LeadRepository,
        intel_repo: IntelligenceRepository,
        score_repo: ScoringRepository,
        event_repo: EmailEventRepository,
        analytics_repo: EmailAnalyticsRepository,
    ):
        self.campaign_repo = campaign_repo
        self.step_repo = step_repo
        self.recip_repo = recip_repo
        self.account_repo = account_repo
        self.lead_repo = lead_repo
        self.intel_repo = intel_repo
        self.score_repo = score_repo
        self.event_repo = event_repo
        self.analytics_repo = analytics_repo

    async def send_next_batch(self, campaign_id: str, batch_size: int = 20) -> int:
        camp = await self.campaign_repo.get_by_id_no_auth(campaign_id)
        if not camp or camp.status != "active":
            return 0

        account = None
        if camp.sending_account_id:
            account = await self.account_repo.get_by_id_no_auth(str(camp.sending_account_id))
        if not account:
            account = await self.account_repo.get_default(str(camp.owner_id))

        provider = get_email_provider(account)
        recipients = await self.recip_repo.get_pending_batch(campaign_id, limit=batch_size)

        sent_count = 0
        for recip in recipients:
            step = await self.step_repo.get_step_by_number(campaign_id, recip.current_step)
            if not step:
                # Sequence finished for recipient
                await self.recip_repo.update(recip, {"status": "completed"})
                continue

            # Load lead context for variable resolution
            lead = await self.lead_repo.get_by_id(str(recip.lead_id), str(recip.owner_id))
            intel = await self.intel_repo.get_by_lead_id(str(recip.lead_id), str(recip.owner_id))
            score_doc = await self.score_repo.get_by_lead_id(str(recip.lead_id), str(recip.owner_id))

            rendered_subject = VariableEngine.render(step.subject, recip.variables, lead, intel, score_doc)
            rendered_body = VariableEngine.render(step.body, recip.variables, lead, intel, score_doc)

            token, tracked_body = TrackingService.inject_tracking(
                rendered_body,
                recipient_id=str(recip.id),
                campaign_id=campaign_id,
            )

            # Send email
            res = await provider.send_email(
                to_email=recip.email,
                subject=rendered_subject,
                body_html=tracked_body,
                from_email=account.email_address if account else None,
                from_name=account.name if account else None,
            )

            if res.success:
                sent_count += 1
                now = datetime.now(timezone.utc)
                await self.recip_repo.update(recip, {
                    "status": "sent",
                    "sent_at": now,
                    "current_step": recip.current_step + 1,
                })
                # Log send event
                await self.event_repo.create({
                    "campaign_id": camp.id,
                    "recipient_id": recip.id,
                    "lead_id": recip.lead_id,
                    "owner_id": recip.owner_id,
                    "event_type": "send",
                })
            else:
                logger.error(f"Send failed to {recip.email}: {res.error}")

        # Update analytics after batch send
        if sent_count > 0:
            total_sent = await self.event_repo.count_by_type(campaign_id, "send")
            await self.analytics_repo.upsert_analytics(
                campaign_id=campaign_id,
                owner_id=str(camp.owner_id),
                data={"total_sent": total_sent},
            )

        return sent_count


class TrackingModule:
    def __init__(
        self,
        recip_repo: CampaignRecipientRepository,
        event_repo: EmailEventRepository,
        analytics_repo: EmailAnalyticsRepository,
    ):
        self.recip_repo = recip_repo
        self.event_repo = event_repo
        self.analytics_repo = analytics_repo

    async def track_open(self, token: str, user_agent: str = "", ip: str = "") -> bytes:
        parts = token.split("_")
        if len(parts) >= 2:
            campaign_id, recipient_id = parts[0], parts[1]
            recip = await self.recip_repo.get_by_id(recipient_id)
            if recip:
                now = datetime.now(timezone.utc)
                await self.recip_repo.update(recip, {
                    "status": "opened" if recip.status == "sent" else recip.status,
                    "opened_at": recip.opened_at or now,
                })
                await self.event_repo.create({
                    "campaign_id": ObjectId(campaign_id),
                    "recipient_id": recip.id,
                    "lead_id": recip.lead_id,
                    "owner_id": recip.owner_id,
                    "event_type": "open",
                    "user_agent": user_agent,
                    "ip_address": ip,
                })
                # Update analytics
                total_opens = await self.event_repo.count_by_type(campaign_id, "open")
                await self.analytics_repo.upsert_analytics(
                    campaign_id=campaign_id,
                    owner_id=str(recip.owner_id),
                    data={"total_opened": total_opens},
                )

        return TrackingService.get_pixel_gif()

    async def track_click(self, token: str, target_url: str, user_agent: str = "", ip: str = "") -> str:
        parts = token.split("_")
        if len(parts) >= 2:
            campaign_id, recipient_id = parts[0], parts[1]
            recip = await self.recip_repo.get_by_id(recipient_id)
            if recip:
                now = datetime.now(timezone.utc)
                await self.recip_repo.update(recip, {
                    "status": "clicked" if recip.status in ["sent", "opened"] else recip.status,
                    "clicked_at": recip.clicked_at or now,
                })
                await self.event_repo.create({
                    "campaign_id": ObjectId(campaign_id),
                    "recipient_id": recip.id,
                    "lead_id": recip.lead_id,
                    "owner_id": recip.owner_id,
                    "event_type": "click",
                    "link_url": target_url,
                    "user_agent": user_agent,
                    "ip_address": ip,
                })
                # Update analytics
                total_clicks = await self.event_repo.count_by_type(campaign_id, "click")
                await self.analytics_repo.upsert_analytics(
                    campaign_id=campaign_id,
                    owner_id=str(recip.owner_id),
                    data={"total_clicked": total_clicks},
                )

        return target_url or "http://localhost"


class AnalyticsModule:
    def __init__(
        self,
        analytics_repo: EmailAnalyticsRepository,
        event_repo: EmailEventRepository,
    ):
        self.analytics_repo = analytics_repo
        self.event_repo = event_repo

    async def get_analytics(self, campaign_id: str, owner_id: str) -> object:
        doc = await self.analytics_repo.get_by_campaign(campaign_id, owner_id)
        if not doc:
            return {
                "campaign_id": campaign_id,
                "total_recipients": 0,
                "total_sent": 0,
                "total_opened": 0,
                "total_clicked": 0,
                "total_replied": 0,
                "open_rate": 0.0,
                "click_rate": 0.0,
                "reply_rate": 0.0,
            }

        sent = max(1, doc.total_sent)
        open_rate = round((doc.total_opened / sent) * 100, 1) if doc.total_sent > 0 else 0.0
        click_rate = round((doc.total_clicked / sent) * 100, 1) if doc.total_sent > 0 else 0.0
        reply_rate = round((doc.total_replied / sent) * 100, 1) if doc.total_sent > 0 else 0.0

        return await self.analytics_repo.upsert_analytics(
            campaign_id=campaign_id,
            owner_id=owner_id,
            data={
                "open_rate": open_rate,
                "click_rate": click_rate,
                "reply_rate": reply_rate,
            },
        )
