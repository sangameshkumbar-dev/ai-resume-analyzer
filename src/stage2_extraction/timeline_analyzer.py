"""
Timeline and Years of Experience Analyzer.
Parses date intervals, merges overlapping employment periods, and computes verified total experience.
"""
import re
from datetime import datetime
from typing import List, Tuple, Dict, Any, Optional

# Month names mapping
MONTH_MAP = {
    "jan": 1, "january": 1,
    "feb": 2, "february": 2,
    "mar": 3, "march": 3,
    "apr": 4, "april": 4,
    "may": 5,
    "jun": 6, "june": 6,
    "jul": 7, "july": 7,
    "aug": 8, "august": 8,
    "sep": 9, "sept": 9, "september": 9,
    "oct": 10, "october": 10,
    "nov": 11, "november": 11,
    "dec": 12, "december": 12
}

# Regex to detect date ranges
MONTH_REGEX = r'(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)'
YEAR_REGEX = r'(?:19[7-9]\d|20[0-2]\d)'
PRESENT_REGEX = r'(?:Present|Current|Ongoing|Now|Till Date)'

DATE_RANGE_PATTERN = re.compile(
    rf'({MONTH_REGEX}\s+{YEAR_REGEX}|\d{{1,2}}/\d{{4}}|{YEAR_REGEX})'
    rf'\s*(?:-|–|—|to)\s*'
    rf'({MONTH_REGEX}\s+{YEAR_REGEX}|\d{{1,2}}/\d{{4}}|{YEAR_REGEX}|{PRESENT_REGEX})',
    re.IGNORECASE
)


class TimelineAnalyzer:
    """Calculates cumulative and deduplicated years of professional experience."""

    def __init__(self, reference_year: Optional[int] = None):
        self.reference_now = datetime.now() if not reference_year else datetime(reference_year, 1, 1)

    def parse_date_string(self, date_str: str) -> Optional[datetime]:
        """Convert a freeform date string into a datetime object."""
        date_str = date_str.strip()
        if re.match(rf'^{PRESENT_REGEX}$', date_str, re.IGNORECASE):
            return self.reference_now

        # Format: "Jan 2021" or "January 2021"
        m = re.match(rf'^({MONTH_REGEX})\s+({YEAR_REGEX})$', date_str, re.IGNORECASE)
        if m:
            month_str, year_str = m.group(1).lower(), m.group(2)
            month = MONTH_MAP.get(month_str, 1)
            return datetime(int(year_str), month, 1)

        # Format: "06/2020"
        m = re.match(r'^(\d{1,2})/(\d{4})$', date_str)
        if m:
            month, year = int(m.group(1)), int(m.group(2))
            month = max(1, min(12, month))
            return datetime(year, month, 1)

        # Format: "2020"
        m = re.match(rf'^({YEAR_REGEX})$', date_str)
        if m:
            return datetime(int(m.group(1)), 1, 1)

        return None

    def extract_intervals(self, text: str) -> List[Tuple[datetime, datetime, str]]:
        """Find all date ranges in the given text and return list of (start, end, raw_str)."""
        intervals = []
        matches = DATE_RANGE_PATTERN.finditer(text)
        for m in matches:
            raw_start, raw_end = m.group(1), m.group(2)
            dt_start = self.parse_date_string(raw_start)
            dt_end = self.parse_date_string(raw_end)

            if dt_start and dt_end:
                # If start date is after end date, swap or adjust
                if dt_start > dt_end:
                    dt_start, dt_end = dt_end, dt_start

                # Filter out unreasonable future dates or ancient dates (< 1970)
                if dt_start.year >= 1970 and dt_end <= datetime(self.reference_now.year + 2, 12, 31):
                    intervals.append((dt_start, dt_end, f"{raw_start} - {raw_end}"))

        return intervals

    def merge_intervals(self, intervals: List[Tuple[datetime, datetime]]) -> List[Tuple[datetime, datetime]]:
        """Merge overlapping or continuous date intervals to prevent double-counting."""
        if not intervals:
            return []

        # Sort by start date
        sorted_intervals = sorted(intervals, key=lambda x: x[0])
        merged = [sorted_intervals[0]]

        for current_start, current_end in sorted_intervals[1:]:
            last_start, last_end = merged[-1]
            if current_start <= last_end:
                # Overlap detected: extend end date
                merged[-1] = (last_start, max(last_end, current_end))
            else:
                merged.append((current_start, current_end))

        return merged

    def calculate_total_experience(self, text: str) -> Dict[str, Any]:
        """
        Extract date ranges, merge overlaps, and compute total verified professional experience.
        """
        raw_intervals = self.extract_intervals(text)
        if not raw_intervals:
            # Fallback: check for explicit statements like "5+ years of experience"
            exp_mention = re.search(r'(\d{1,2})\+?\s*(?:years|yrs)\s+(?:of\s+)?experience', text, re.IGNORECASE)
            if exp_mention:
                years = float(exp_mention.group(1))
                return {
                    "total_years": years,
                    "total_months": int(years * 12),
                    "timeline_breakdown": [],
                    "detected_intervals_count": 0,
                    "confidence": "Mention-based (Heuristic)"
                }
            return {
                "total_years": 0.0,
                "total_months": 0,
                "timeline_breakdown": [],
                "detected_intervals_count": 0,
                "confidence": "Undetected"
            }

        # Deduplicate and merge intervals
        pure_ranges = [(start, end) for start, end, _ in raw_intervals]
        merged_ranges = self.merge_intervals(pure_ranges)

        total_days = sum((end - start).days for start, end in merged_ranges)
        total_years = round(total_days / 365.25, 1)
        total_months = int(total_days / 30.44)

        breakdown = []
        for start, end in merged_ranges:
            span_months = int((end - start).days / 30.44)
            span_years = round((end - start).days / 365.25, 1)
            breakdown.append({
                "start": start.strftime("%b %Y"),
                "end": "Present" if end >= self.reference_now else end.strftime("%b %Y"),
                "duration_years": span_years,
                "duration_months": span_months
            })

        return {
            "total_years": total_years,
            "total_months": total_months,
            "timeline_breakdown": breakdown,
            "detected_intervals_count": len(raw_intervals),
            "merged_intervals_count": len(merged_ranges),
            "confidence": "Calculated (Timeline Intervals)"
        }

