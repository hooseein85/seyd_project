from datetime import datetime, time, timedelta
from io import BytesIO

from openpyxl import Workbook
from sqlalchemy.orm import Session

from app.models.violation import Violation


class ViolationExportService:

    def export_to_excel(
        self,
        db: Session,
        from_date,
        to_date,
        expert_action: str | None = None,
    ) -> BytesIO:

        start_datetime = datetime.combine(
            from_date,
            time.min,
        )

        end_datetime = datetime.combine(
            to_date + timedelta(days=1),
            time.min,
        )

        # فیلترهای اصلی
        filters = [
            Violation.action_status == "confirmed",
            Violation.created_at >= start_datetime,
            Violation.created_at < end_datetime,
        ]

        # اگر Action مشخص شده باشد، فیلتر Action را هم اضافه کن
        # اگر None باشد یعنی "همه" و اصلاً این شرط اضافه نمی‌شود.
        if expert_action:
            filters.append(
                Violation.expert_action == expert_action
            )

        violations = (
            db.query(Violation)
            .filter(*filters)
            .order_by(Violation.created_at.desc())
            .all()
        )

        workbook = Workbook()
        worksheet = workbook.active
        worksheet.title = "Violations"

        headers = [
            "ID",
            "Fingerprint",
            "Import Batch ID",
            "Content ID",
            "Assessment ID",
            "Account ID",
            "Person ID",
            "Policy ID",
            "Expert ID",
            "Expert Action",
            "Action Status",
            "Created At",
        ]

        worksheet.append(headers)

        for violation in violations:
            worksheet.append([
                str(violation.id) if violation.id else None,
                violation.fingerprint,
                violation.import_batch_id,
                str(violation.content_id) if violation.content_id else None,
                str(violation.assessment_id) if violation.assessment_id else None,
                str(violation.account_id) if violation.account_id else None,
                str(violation.person_id) if violation.person_id else None,
                str(violation.policy_id) if violation.policy_id else None,
                violation.expert_id,
                violation.expert_action,
                violation.action_status,
                violation.created_at,
            ])

        output = BytesIO()
        workbook.save(output)
        output.seek(0)

        return output