from __future__ import annotations

import csv
import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Dict, List


DATA_FILE = Path("checkins_raw.csv")
OUTPUT_FILE = Path("insights_output.json")
DATE_FORMAT = "%Y-%m-%d"

STRESS_SCORES: Dict[str, int] = {
    "Very calm": 3,
    "A bit stressed": 2,
    "Very stressed": 1,
}

FOCUS_SCORES: Dict[str, int] = {
    "Sharp and clear": 3,
    "A bit scattered": 2,
    "Very distracted": 1,
}

SLEEP_SCORES: Dict[str, int] = {
    "Well rested": 3,
    "A bit tired": 2,
    "Poorly": 1,
}


@dataclass(frozen=True)
class CheckIn:
    date: datetime
    stress: str
    focus: str
    sleep: str
    screen_time_hours: float
    notifications: int
    focus_window: str


@dataclass(frozen=True)
class DailyInsight:
    day: str
    stress_score: int
    focus_score: int
    sleep_score: int
    screen_time_score: int
    notifications_score: int
    wellbeing_score: float
    screen_time_hours: float
    notifications: int
    focus_window: str


def score_screen_time(hours: float) -> int:
    if hours <= 4.5:
        return 3
    if hours <= 6.0:
        return 2
    return 1


def score_notifications(count: int) -> int:
    if count <= 10:
        return 3
    if count <= 15:
        return 2
    return 1


def classify_wellbeing(score: float) -> str:
    if score >= 7.5:
        return "Balanced"
    if score >= 5.5:
        return "Moderate strain"
    return "High strain"


def build_reflection(score: float, avg_screen_time: float, peak_notifications: int) -> str:
    category = classify_wellbeing(score)

    if category == "Balanced":
        if avg_screen_time > 6:
            return "Your wellbeing is fairly stable overall, although your screen time is still quite high."
        return "Your weekly pattern looks fairly balanced overall."

    if category == "Moderate strain":
        if peak_notifications >= 16:
            return "Your recent check-ins suggest some digital strain this week, especially on higher-interruption days."
        return "Your recent check-ins suggest some digital strain this week."

    return "Your recent check-ins suggest higher digital pressure and lower recovery."


def read_checkins(path: Path) -> List[CheckIn]:
    checkins: List[CheckIn] = []

    with path.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)

        required_columns = {
            "date",
            "stress",
            "focus",
            "sleep",
            "screen_time_hours",
            "notifications",
            "focus_window",
        }

        missing = required_columns.difference(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Missing required columns: {sorted(missing)}")

        for row in reader:
            checkins.append(
                CheckIn(
                    date=datetime.strptime(row["date"], DATE_FORMAT),
                    stress=row["stress"],
                    focus=row["focus"],
                    sleep=row["sleep"],
                    screen_time_hours=float(row["screen_time_hours"]),
                    notifications=int(row["notifications"]),
                    focus_window=row["focus_window"],
                )
            )

    return checkins


def calculate_daily_insight(checkin: CheckIn) -> DailyInsight:
    stress_score = STRESS_SCORES[checkin.stress]
    focus_score = FOCUS_SCORES[checkin.focus]
    sleep_score = SLEEP_SCORES[checkin.sleep]
    screen_time_score = score_screen_time(checkin.screen_time_hours)
    notifications_score = score_notifications(checkin.notifications)

    total_score = (
        stress_score
        + focus_score
        + sleep_score
        + screen_time_score
        + notifications_score
    )

    wellbeing_score = round((total_score / 15) * 10, 1)

    return DailyInsight(
        day=checkin.date.strftime("%a"),
        stress_score=stress_score,
        focus_score=focus_score,
        sleep_score=sleep_score,
        screen_time_score=screen_time_score,
        notifications_score=notifications_score,
        wellbeing_score=wellbeing_score,
        screen_time_hours=checkin.screen_time_hours,
        notifications=checkin.notifications,
        focus_window=checkin.focus_window,
    )


def calculate_best_focus_time(daily: List[DailyInsight]) -> str:
    grouped: Dict[str, List[int]] = defaultdict(list)
    for item in daily:
        grouped[item.focus_window].append(item.focus_score)
    return max(grouped.items(), key=lambda item: mean(item[1]))[0]


def calculate_peak_notifications_day(daily: List[DailyInsight]) -> str:
    return max(daily, key=lambda item: item.notifications).day


def build_output(daily: List[DailyInsight]) -> dict:
    overall_wellbeing = round(mean(item.wellbeing_score for item in daily), 1)
    avg_screen_time = round(mean(item.screen_time_hours for item in daily), 1)
    peak_notifications_value = max(item.notifications for item in daily)

    return {
        "summary": {
            "overall_wellbeing": f"{overall_wellbeing}/10",
            "classification": classify_wellbeing(overall_wellbeing),
            "average_screen_time": f"{avg_screen_time} hrs/day",
            "best_focus_time": calculate_best_focus_time(daily),
            "peak_notifications": calculate_peak_notifications_day(daily),
            "reflection": build_reflection(
                overall_wellbeing,
                avg_screen_time,
                peak_notifications_value,
            ),
        },
        "calculation_method": {
            "wellbeing_formula": "((stress + focus + sleep + screen_time + notifications) / 15) * 10",
            "score_scale": "Each factor is scored from 1 to 3",
            "screen_time_thresholds": {
                "<= 4.5 hours": 3,
                "4.6 to 6.0 hours": 2,
                "> 6.0 hours": 1,
            },
            "notification_thresholds": {
                "<= 10 notifications": 3,
                "11 to 15 notifications": 2,
                "> 15 notifications": 1,
            },
        },
        "daily_breakdown": [
            {
                "day": item.day,
                "stress_score": item.stress_score,
                "focus_score": item.focus_score,
                "sleep_score": item.sleep_score,
                "screen_time_score": item.screen_time_score,
                "notifications_score": item.notifications_score,
                "wellbeing_score": item.wellbeing_score,
                "screen_time_hours": item.screen_time_hours,
                "notifications": item.notifications,
                "focus_window": item.focus_window,
            }
            for item in daily
        ],
        "wellbeing_chart": [
            {"day": item.day, "wellbeing_score": item.wellbeing_score}
            for item in daily
        ],
        "screen_time_chart": [
            {"day": item.day, "screen_time_hours": item.screen_time_hours}
            for item in daily
        ],
    }


def save_output(path: Path, payload: dict) -> None:
    with path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, indent=4)


def main() -> None:
    checkins = read_checkins(DATA_FILE)
    daily_insights = [calculate_daily_insight(item) for item in checkins]
    result = build_output(daily_insights)
    save_output(OUTPUT_FILE, result)

    summary = result["summary"]

    print("ResetU Insights Backend Output")
    print("------------------------------")
    print("Overall Well-being:", summary["overall_wellbeing"])
    print("Classification:", summary["classification"])
    print("Average Screen Time:", summary["average_screen_time"])
    print("Best focus time:", summary["best_focus_time"])
    print("Peak notifications:", summary["peak_notifications"])
    print("Reflection:", summary["reflection"])
    print(f"\nSaved detailed output to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
