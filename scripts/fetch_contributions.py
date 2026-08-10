from __future__ import annotations

import argparse
import json
import os
import re
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup


def parse_days(html: str) -> list[dict[str, object]]:
    soup = BeautifulSoup(html, "html.parser")
    cells = soup.select(".ContributionCalendar-day[data-date]")
    days: list[dict[str, object]] = []

    for cell in cells:
        date_text = cell.get("data-date")
        if not date_text:
            continue
        level_text = cell.get("data-level", "0")
        days.append(
            {
                "date": date_text,
                "level": int(level_text),
                "count": int(level_text),
            }
        )

    days.sort(key=lambda item: item["date"])
    return days


def compute_streaks(days: list[dict[str, object]]) -> tuple[int, int]:
    parsed = [
        {
            "date": datetime.strptime(str(day["date"]), "%Y-%m-%d").date(),
            "count": int(day["count"]),
        }
        for day in days
    ]

    longest = 0
    current = 0
    previous: date | None = None

    for item in parsed:
        if item["count"] > 0:
            if previous and (item["date"] - previous).days == 1:
                current += 1
            else:
                current = 1
            longest = max(longest, current)
            previous = item["date"]
        else:
            current = 0
            previous = item["date"]

    latest = parsed[-1]["date"] if parsed else None
    current_streak = 0
    if latest is not None:
        cursor = latest
        for item in reversed(parsed):
            if item["date"] != cursor:
                break
            if item["count"] <= 0:
                current_streak = 0
                break
            current_streak += 1
            cursor = cursor - timedelta(days=1)

    return current_streak, longest


def build_payload(days: list[dict[str, object]]) -> dict[str, object]:
    total = sum(int(day["count"]) for day in days)
    best_day = max(days, key=lambda item: int(item["count"]), default=None)
    current_streak, longest_streak = compute_streaks(days)

    monthly_totals: dict[str, int] = defaultdict(int)
    for day in days:
        month = str(day["date"])[:7]
        monthly_totals[month] += int(day["count"])

    return {
        "source": "https://github.com/users/{username}/contributions",
        "total": total,
        "days": days,
        "streaks": {
            "current": current_streak,
            "longest": longest_streak,
        },
        "best_day": best_day,
        "monthly_totals": [
            {"month": month, "count": monthly_totals[month]}
            for month in sorted(monthly_totals)
        ],
        "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch public GitHub contribution data.")
    parser.add_argument("--username", default=os.environ.get("GITHUB_REPOSITORY_OWNER", "MustafaBhewala"), help="GitHub username")
    parser.add_argument("--output", type=Path, default=Path("data/contributions.json"), help="Output JSON path")
    args = parser.parse_args()

    url = f"https://github.com/users/{args.username}/contributions"
    response = requests.get(url, timeout=30, headers={"Accept": "text/html"})
    response.raise_for_status()

    days = parse_days(response.text)
    payload = build_payload(days)
    payload["source"] = url
    payload["username"] = args.username

    summary_match = re.search(r'js-contribution-activity-description[^>]*>\s*(\d+)\s+contributions', response.text)
    if summary_match:
        payload["total"] = int(summary_match.group(1))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()