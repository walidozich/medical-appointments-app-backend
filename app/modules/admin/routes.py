from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, require_roles
from app.modules.admin import service, schemas
from app.modules.users.models import User

router = APIRouter()


@router.get("/reports/summary", response_model=schemas.Summary)
def get_summary_report(
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_roles("ADMIN")),
):
    """
    High-level dashboard summary for admins.
    """
    return service.summary(db)
