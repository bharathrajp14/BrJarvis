# career/api_routes.py — FastAPI REST Endpoints for BR JARVIS Career OS
from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel

from .analytics import CareerAnalyticsEngine
from .application_engine.assistant import ManualApplicationAssistant
from .application_engine.tracker import ApplicationTracker
from .ats_engine.scorer import ATSEngine
from .canva.capability import CanvaCapabilityProbe
from .interview_prep import InterviewPrepGenerator
from .job_engine.finder import JobFinder
from .job_engine.matcher import JobMatcher
from .models import ApplicationStatus
from .profile_manager import get_profile_manager
from .resume_engine.exporter import ResumeExportPipeline
from .resume_engine.renderer import ResumeRenderer
from .resume_engine.tailoring import ResumeTailoringEngine
from .resume_engine.templates import list_templates
from .resume_engine.version_manager import ResumeVersionManager

logger = logging.getLogger("JARVIS.CareerAPI")

router = APIRouter(prefix="/career", tags=["Career OS"])


# ── Request / Response Schemas ───────────────────────────────────────────────


class ProfileUpdateRequest(BaseModel):
    updates: Dict[str, Any]


class OnboardingAnswerRequest(BaseModel):
    answers: Dict[str, Any]


class ResumeCreateRequest(BaseModel):
    target_role: Optional[str] = None
    template_id: str = "ats_classic"


class ResumeTailorRequest(BaseModel):
    job_description: str
    target_role: Optional[str] = None
    company_name: Optional[str] = None
    template_id: str = "ats_classic"


class ATSScoreRequest(BaseModel):
    job_description: Optional[str] = None
    target_role: Optional[str] = None


class ApplicationPrepareRequest(BaseModel):
    job_id: str
    auto_open_browser: bool = True


class ApplicationStatusUpdateRequest(BaseModel):
    new_status: str
    note: Optional[str] = ""
    confirmation_id: Optional[str] = None


# ── Profile Endpoints ────────────────────────────────────────────────────────


@router.get("/profile")
def get_career_profile():
    mgr = get_profile_manager()
    profile = mgr.get_profile()
    val = mgr.validate_profile(profile)
    return {
        "profile": profile.to_dict(),
        "validation": val,
    }


@router.post("/profile")
def update_career_profile(req: ProfileUpdateRequest):
    mgr = get_profile_manager()
    updated = mgr.apply_onboarding_answers(req.updates)
    val = mgr.validate_profile(updated)
    return {
        "status": "SUCCESS",
        "profile": updated.to_dict(),
        "validation": val,
    }


@router.get("/profile/onboarding")
def get_onboarding_questions():
    mgr = get_profile_manager()
    questions = mgr.get_onboarding_questions()
    return {
        "count": len(questions),
        "questions": questions,
    }


@router.post("/profile/onboarding")
def submit_onboarding_answers(req: OnboardingAnswerRequest):
    mgr = get_profile_manager()
    updated = mgr.apply_onboarding_answers(req.answers)
    val = mgr.validate_profile(updated)
    return {
        "status": "SUCCESS",
        "validation": val,
    }


# ── Resume & Template Endpoints ──────────────────────────────────────────────


@router.get("/resumes/templates")
def get_resume_templates():
    return {"templates": list_templates()}


@router.post("/resumes/create")
def create_resume(req: ResumeCreateRequest):
    mgr = get_profile_manager()
    profile = mgr.get_profile()

    schema = ResumeRenderer.schema_from_profile(
        profile,
        target_role=req.target_role,
        template_id=req.template_id,
    )

    exporter = ResumeExportPipeline()
    export_res = exporter.export_all_formats(schema)

    ver_mgr = ResumeVersionManager.get_instance()
    ver_rec = ver_mgr.register_version(
        resume=schema,
        provider="native",
        docx_path=export_res["docx"]["path"],
        pdf_path=export_res["pdf"]["path"],
        html_path=export_res["html"]["path"],
    )

    return {
        "status": "SUCCESS_VERIFIED" if export_res["all_verified"] else "PARTIAL_SUCCESS",
        "version_id": ver_rec.version_id,
        "resume": schema.to_dict(),
        "artifacts": export_res,
    }


@router.post("/resumes/tailor")
def tailor_resume(req: ResumeTailorRequest):
    mgr = get_profile_manager()
    profile = mgr.get_profile()

    tailored_schema, diff = ResumeTailoringEngine.tailor_resume(
        profile=profile,
        job_description=req.job_description,
        target_role=req.target_role,
        company_name=req.company_name,
        template_id=req.template_id,
    )

    exporter = ResumeExportPipeline()
    export_res = exporter.export_all_formats(tailored_schema)

    ats_rep = ATSEngine.evaluate_resume(tailored_schema, job_description=req.job_description)
    tailored_schema.ats_score = ats_rep.overall_score

    ver_mgr = ResumeVersionManager.get_instance()
    ver_rec = ver_mgr.register_version(
        resume=tailored_schema,
        provider="native",
        docx_path=export_res["docx"]["path"],
        pdf_path=export_res["pdf"]["path"],
        html_path=export_res["html"]["path"],
    )

    return {
        "status": "SUCCESS_VERIFIED" if export_res["all_verified"] else "PARTIAL_SUCCESS",
        "version_id": ver_rec.version_id,
        "resume": tailored_schema.to_dict(),
        "diff": diff.to_dict(),
        "ats_score": ats_rep.to_dict(),
        "artifacts": export_res,
    }


@router.get("/resumes/versions")
def list_resume_versions(limit: int = 50):
    ver_mgr = ResumeVersionManager.get_instance()
    versions = ver_mgr.list_versions(limit=limit)
    return {"versions": [v.to_dict() for v in versions]}


@router.post("/ats/score")
def score_resume_ats(req: ATSScoreRequest):
    mgr = get_profile_manager()
    profile = mgr.get_profile()
    schema = ResumeRenderer.schema_from_profile(profile, target_role=req.target_role)

    report = ATSEngine.evaluate_resume(schema, job_description=req.job_description)
    return report.to_dict()


# ── Job Endpoints ────────────────────────────────────────────────────────────


@router.get("/jobs/search")
def search_jobs(
    query: str = Query(..., description="Job search query"),
    location: Optional[str] = Query(None, description="Location"),
    limit: int = Query(15, description="Max results"),
):
    finder = JobFinder.get_instance()
    results = finder.search_and_match(query_or_filters=query, limit=limit)
    return {
        "count": len(results),
        "matches": [r.to_dict() for r in results],
    }


@router.get("/jobs/{job_id}")
def get_job_details(job_id: str):
    finder = JobFinder.get_instance()
    job = finder.get_job_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job ID '{job_id}' not found.")

    mgr = get_profile_manager()
    profile = mgr.get_profile()
    match = JobMatcher.match(profile, job)
    return {
        "job": job.to_dict(),
        "match": match.to_dict(),
    }


# ── Application Endpoints ────────────────────────────────────────────────────


@router.post("/applications/prepare")
def prepare_application(req: ApplicationPrepareRequest):
    finder = JobFinder.get_instance()
    job = finder.get_job_by_id(req.job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job ID '{req.job_id}' not found.")

    assistant = ManualApplicationAssistant()
    res = assistant.prepare_and_assist(job=job, auto_open_browser=req.auto_open_browser)
    return res


@router.get("/applications")
def list_applications(status: Optional[str] = None):
    st_enum = None
    if status:
        try:
            st_enum = ApplicationStatus(status.upper())
        except Exception:
            pass

    tracker = ApplicationTracker.get_instance()
    apps = tracker.list_applications(status=st_enum)
    return {
        "count": len(apps),
        "applications": [a.to_dict() for a in apps],
        "funnel_counts": tracker.get_funnel_counts(),
    }


@router.post("/applications/{application_id}/status")
def update_application_status(application_id: str, req: ApplicationStatusUpdateRequest):
    try:
        st_enum = ApplicationStatus(req.new_status.upper())
    except Exception:
        raise HTTPException(status_code=400, detail=f"Invalid status '{req.new_status}'.")

    tracker = ApplicationTracker.get_instance()
    updated = tracker.update_status(
        application_id=application_id,
        new_status=st_enum,
        note=req.note or "",
        confirmation_id=req.confirmation_id,
    )
    if not updated:
        raise HTTPException(status_code=404, detail=f"Application ID '{application_id}' not found.")

    return {"status": "SUCCESS", "application": updated.to_dict()}


# ── Analytics & Prep Endpoints ───────────────────────────────────────────────


@router.get("/analytics")
def get_career_analytics():
    return CareerAnalyticsEngine.compute_analytics().to_dict()


@router.get("/interview-prep/{job_id}")
def get_interview_prep(job_id: str):
    finder = JobFinder.get_instance()
    job = finder.get_job_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job ID '{job_id}' not found.")

    mgr = get_profile_manager()
    profile = mgr.get_profile()

    kit = InterviewPrepGenerator.generate_prep_kit(profile=profile, job=job)
    return kit.to_dict()


@router.get("/canva/capabilities")
def get_canva_capabilities():
    return CanvaCapabilityProbe.detect_capabilities().to_dict()


# ── File Download & Preview ──────────────────────────────────────────────────


@router.get("/download/{file_path:path}")
def download_career_file(file_path: str):
    p = Path(file_path).resolve()
    from brjarvis.core.paths import paths

    workspace_dir = paths.WORKSPACE_ROOT.resolve()
    try:
        p.relative_to(workspace_dir)
    except ValueError:
        raise HTTPException(status_code=403, detail="Access denied: file is outside the workspace.")

    if not p.exists() or not p.is_file():
        raise HTTPException(status_code=404, detail="File not found.")

    media_type = "application/octet-stream"
    if p.suffix == ".pdf":
        media_type = "application/pdf"
    elif p.suffix == ".docx":
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    return FileResponse(path=str(p), media_type=media_type, filename=p.name)


# ── Canonical Career CRM & Email Intelligence Endpoints ──────────────────────


class EmailProcessRequest(BaseModel):
    sender: str
    subject: str
    body: str
    provider: str = "gmail"
    message_id: Optional[str] = None


class InterviewCreateRequest(BaseModel):
    application_id: Optional[str] = None
    company: str
    role: str
    round: str = "Technical Round"
    date: str
    time_str: str
    timezone: str = "IST"
    meeting_url: Optional[str] = None
    interviewer: Optional[str] = None


class OfferConfirmRequest(BaseModel):
    offer_id: str
    user_confirmed: bool = True


class FollowupDraftRequest(BaseModel):
    followup_id: str
    candidate_name: str = "Bharath"


@router.post("/email/process")
def process_career_email(req: EmailProcessRequest):
    from brjarvis.career.email_intelligence.service import get_email_career_intelligence

    service = get_email_career_intelligence()
    res = service.process_incoming_email(
        provider=req.provider,
        message_id=req.message_id or f"msg_{int(time.time() * 1000)}",
        sender=req.sender,
        subject=req.subject,
        body=req.body,
    )
    return res


@router.post("/email/sync")
def sync_career_emails(limit: int = 15):
    from brjarvis.career.email_intelligence.service import get_email_career_intelligence

    service = get_email_career_intelligence()
    return service.sync_career_emails(limit=limit)


@router.get("/email/events")
def list_email_events(limit: int = 100):
    from brjarvis.career.crm.database import get_career_crm_db

    db = get_career_crm_db()
    records = db.list_email_records(limit=limit)
    return {"count": len(records), "events": [r.to_dict() for r in records]}


@router.get("/crm/events")
def list_career_events(limit: int = 50):
    from brjarvis.career.crm.database import get_career_crm_db

    db = get_career_crm_db()
    events = db.list_recent_events(limit=limit)
    return {"count": len(events), "events": [e.to_dict() for e in events]}


@router.get("/crm/events/{application_id}")
def get_application_events(application_id: str):
    from brjarvis.career.crm.database import get_career_crm_db

    db = get_career_crm_db()
    events = db.get_events_for_application(application_id)
    return {"application_id": application_id, "count": len(events), "events": [e.to_dict() for e in events]}


@router.get("/interviews")
def list_interviews(application_id: Optional[str] = None):
    from brjarvis.career.crm.database import get_career_crm_db

    db = get_career_crm_db()
    interviews = db.list_interviews(application_id=application_id)
    return {"count": len(interviews), "interviews": [i.to_dict() for i in interviews]}


@router.post("/interviews")
def schedule_interview(req: InterviewCreateRequest):
    import uuid

    from brjarvis.career.calendar_engine.manager import get_career_calendar_manager
    from brjarvis.career.models import InterviewSchedule

    schedule = InterviewSchedule(
        interview_id=f"INT-{uuid.uuid4().hex[:6].upper()}",
        application_id=req.application_id or "",
        company=req.company,
        role=req.role,
        round=req.round,
        date=req.date,
        time_str=req.time_str,
        timezone=req.timezone,
        meeting_url=req.meeting_url or "",
        interviewer=req.interviewer or "",
        status="SCHEDULED",
    )

    manager = get_career_calendar_manager()
    res = manager.schedule_interview_event(schedule, auto_generate_prep=True)
    return res


@router.get("/offers")
def list_offers(application_id: Optional[str] = None):
    from brjarvis.career.crm.database import get_career_crm_db

    db = get_career_crm_db()
    offers = db.list_offers(application_id=application_id)
    return {"count": len(offers), "offers": [o.to_dict() for o in offers]}


@router.post("/offers/confirm")
def confirm_offer(req: OfferConfirmRequest):
    from brjarvis.career.crm.database import get_career_crm_db
    from brjarvis.career.models import OfferStatus
    from brjarvis.career.spreadsheet.projection import get_spreadsheet_projection

    if not req.user_confirmed:
        raise HTTPException(status_code=400, detail="Offer confirmation requires user_confirmed=True.")

    db = get_career_crm_db()
    offer = db.get_offer(req.offer_id)
    if not offer:
        raise HTTPException(status_code=404, detail=f"Offer ID '{req.offer_id}' not found.")

    offer.status = OfferStatus.OFFER_CONFIRMED
    db.save_offer(offer)
    get_spreadsheet_projection().project_database_to_excel()

    return {
        "status": "SUCCESS",
        "message": f"Offer {offer.offer_id} for {offer.company} is confirmed.",
        "offer": offer.to_dict(),
    }


@router.get("/followups")
def list_followups(status: Optional[str] = None):
    from brjarvis.career.crm.database import get_career_crm_db

    db = get_career_crm_db()
    followups = db.list_followups(status=status)
    return {"count": len(followups), "followups": [f.to_dict() for f in followups]}


@router.post("/followups/draft")
def generate_followup_draft_endpoint(req: FollowupDraftRequest):
    from brjarvis.career.crm.followup_engine import get_followup_engine

    engine = get_followup_engine()
    try:
        draft = engine.generate_followup_draft(req.followup_id, candidate_name=req.candidate_name)
        return draft
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/spreadsheet/sync")
def sync_spreadsheet():
    from .spreadsheet.projection import get_spreadsheet_projection

    proj = get_spreadsheet_projection()
    return proj.project_database_to_excel()


@router.get("/spreadsheet/download")
def download_master_spreadsheet():
    from brjarvis.core.paths import paths

    p = paths.DOCUMENTS_DIR / "BR_JARVIS_Career_Tracker.xlsx"
    if not p.exists():
        from .spreadsheet.projection import get_spreadsheet_projection

        get_spreadsheet_projection().project_database_to_excel()

    return FileResponse(
        path=str(p),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="BR_JARVIS_Career_Tracker.xlsx",
    )


@router.get("/notifications")
def get_career_notifications(unread_only: bool = False):
    from .notifications import get_career_notification_engine

    engine = get_career_notification_engine()
    notifs = engine.list_notifications(unread_only=unread_only)
    return {"count": len(notifs), "notifications": [n.to_dict() for n in notifs]}
