from datetime import datetime, time, timedelta
from io import BytesIO

from openpyxl import Workbook
from sqlalchemy.orm import Session, joinedload

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
            Violation.action_status == "approved",
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
            .options(
                joinedload(Violation.content),
                joinedload(Violation.account),
                joinedload(Violation.policy),
            )
            .filter(*filters)
            .order_by(Violation.created_at.desc())
            .all()
        )

        workbook = Workbook()
        worksheet = workbook.active
        worksheet.title = "Violations"

        headers = [
            "محتوای منتشر شده",
            "عنوان تخلف",
            "شرح تخلف",
            "آیدی اکانت متخلف",
            "یوزرنیم اکانت متخلف",
            "پلتفرم",
            "نام متخلف",
            "اقدام کارشناس",
            "توضیحات کارشناس",
            "وضعیت اقدام",
            "تاریخ ثبت",
        ]

        worksheet.append(headers)

        for violation in violations:
            content = violation.content
            account = violation.account
            policy = violation.policy

            # نام متخلف را از first_name + last_name می‌سازیم
            full_name = None

            if account:
                first_name = account.first_name or ""
                last_name = account.last_name or ""

                full_name = f"{first_name} {last_name}".strip()

            worksheet.append([
                # محتوای منتشر شده
                content.body if content else None,

                # عنوان تخلف
                policy.title if policy else None,

                # شرح تخلف
                policy.description if policy else None,

                # آیدی اکانت
                account.platform_account_id if account else None,

                # Username
                account.username if account else None,

                # Platform
                account.platform if account else None,

                # نام متخلف
                full_name,

                # Expert Action
                violation.expert_action,

                # Expert Comment
                violation.expert_comment,

                # Action Status
                violation.action_status,

                # Created At
                violation.created_at,
            ])

        output = BytesIO()
        workbook.save(output)
        output.seek(0)

        return output