from collections.abc import Sequence
from datetime import date, timedelta
from enum import Enum as PythonEnum
from typing import Protocol

from dateutil.relativedelta import relativedelta
from fastapi import HTTPException
from starlette import status


class PeriodEnum(PythonEnum):
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"


class WaterIntakePeriodEnum(PythonEnum):
    DAY = "day"
    WEEK = "week"
    MONTH = "month"


class HasRecordDate(Protocol):
    record_date: date


def build_ranges(
    period: PeriodEnum | WaterIntakePeriodEnum | None,
    offset: int,
    today: date,
) -> tuple[list[tuple[date, date]], bool]:
    if not period:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Period is required"
        )

    ranges: list[tuple[date, date]] = []
    is_day = False
    period_value = period.value

    if period_value == PeriodEnum.DAY.value:
        start_of_week = (
            today - timedelta(days=today.weekday()) + relativedelta(weeks=offset)
        )
        ranges = [
            (
                start_of_week + timedelta(days=day_index),
                start_of_week + timedelta(days=day_index),
            )
            for day_index in range(7)
        ]
        is_day = True

    elif period_value == PeriodEnum.WEEK.value:
        start_of_month = today.replace(day=1) + relativedelta(months=offset)
        current_start = start_of_month

        while current_start.month == start_of_month.month:
            current_end = current_start + timedelta(days=6)
            if current_end.month != current_start.month:
                current_end = (current_start + relativedelta(months=1)) - timedelta(
                    days=1
                )
            ranges.append((current_start, current_end))
            current_start = current_end + timedelta(days=1)

    elif period_value == PeriodEnum.MONTH.value:
        start_month = (today.month - 1) // 6 * 6 + 1
        start_date = date(today.year, start_month, 1) + relativedelta(months=6 * offset)

        for month_index in range(6):
            month_start = start_date + relativedelta(months=month_index)
            month_end = month_start + relativedelta(months=1) - timedelta(days=1)
            ranges.append((month_start, month_end))

    elif period_value == PeriodEnum.YEAR.value:
        start_year = today.year - (today.year % 5) + (offset * 5)

        for i in range(5):
            year_start = date(start_year + i, 1, 1)
            year_end = date(start_year + i, 12, 31)
            ranges.append((year_start, year_end))

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported period"
        )

    return ranges, is_day


def find_by_record_date[RecordType: HasRecordDate](
    records: Sequence[RecordType], record_date: date
) -> RecordType | None:
    return next(
        (record for record in records if record.record_date == record_date),
        None,
    )
