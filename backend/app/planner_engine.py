from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from math import ceil


PLANNER_START = date(2026, 6, 1)
MAX_DAILY_CAPACITY_MINUTES = 360
MIN_DAILY_CAPACITY_MINUTES = 45
BACKLOG_LOAD_LIMIT = 0.2


@dataclass(frozen=True)
class TopicPlanningInput:
    topic_id: int
    progress_percent: float
    weak_score: float
    difficulty: int = 3
    estimated_hours: float = 4.0
    subject_weight: float = 1.0


@dataclass(frozen=True)
class ExamPlanningInput:
    exam_id: int
    priority: int
    exam_date: date
    topics: list[TopicPlanningInput]


@dataclass(frozen=True)
class DynamicTaskSpec:
    exam_id: int
    topic_id: int
    task_type: str
    estimated_minutes: int
    priority_reason: str
    priority_score: float


def calculate_daily_capacity(
    available_study_hours: float,
    travel_mode: bool = False,
    comeback_mode: bool = False,
    travel_daily_minutes: int | None = None,
) -> int:
    base_minutes = int(max(0, available_study_hours) * 60)
    if travel_mode:
        base_minutes = min(base_minutes, travel_daily_minutes or 90)
    if comeback_mode:
        base_minutes = int(base_minutes * 0.75)
    return max(MIN_DAILY_CAPACITY_MINUTES, min(base_minutes, MAX_DAILY_CAPACITY_MINUTES))


def calculate_backlog_pressure(backlog_tasks: int, daily_capacity_minutes: int) -> int:
    if backlog_tasks <= 0 or daily_capacity_minutes <= 0:
        return 0
    capped_extra = int(daily_capacity_minutes * BACKLOG_LOAD_LIMIT)
    return min(capped_extra, backlog_tasks * 30)


def calculate_weakness_score(topic: TopicPlanningInput) -> float:
    remaining = max(0.0, min(100.0, 100.0 - topic.progress_percent)) / 100.0
    weakness = max(0.0, min(100.0, topic.weak_score)) / 100.0
    difficulty = max(1, min(topic.difficulty, 5)) / 5.0
    subject_weight = max(0.5, min(topic.subject_weight, 3.0))
    return round((weakness * 0.45 + remaining * 0.35 + difficulty * 0.2) * subject_weight * 100, 2)


def calculate_exam_weights(exams: list[ExamPlanningInput], target_date: date) -> dict[int, float]:
    raw_weights: dict[int, float] = {}
    for exam in exams:
        pending_topics = [topic for topic in exam.topics if topic.progress_percent < 100]
        if not pending_topics:
            continue
        days_left = max((exam.exam_date - target_date).days, 0)
        urgency = 1 + (180 / max(days_left, 14))
        manual_priority = max(1, exam.priority)
        syllabus_pressure = len(pending_topics) / max(len(exam.topics), 1)
        weakness_pressure = sum(calculate_weakness_score(topic) for topic in pending_topics) / max(len(pending_topics), 1) / 100
        raw_weights[exam.exam_id] = manual_priority * (urgency + syllabus_pressure + weakness_pressure)

    total = sum(raw_weights.values())
    if total <= 0:
        return {}
    return {exam_id: round(weight / total, 4) for exam_id, weight in raw_weights.items()}


def generate_dynamic_day_plan(
    *,
    target_date: date,
    exams: list[ExamPlanningInput],
    available_study_hours: float,
    travel_mode: bool = False,
    comeback_mode: bool = False,
    backlog_tasks: int = 0,
    travel_daily_minutes: int | None = None,
) -> list[DynamicTaskSpec]:
    if target_date < PLANNER_START:
        return []

    daily_capacity = calculate_daily_capacity(
        available_study_hours,
        travel_mode=travel_mode,
        comeback_mode=comeback_mode,
        travel_daily_minutes=travel_daily_minutes,
    )
    backlog_minutes = calculate_backlog_pressure(backlog_tasks, daily_capacity)
    planned_capacity = daily_capacity
    weights = calculate_exam_weights(exams, target_date)
    if not weights:
        return []

    specs: list[DynamicTaskSpec] = []
    used_minutes = 0
    exams_by_id = {exam.exam_id: exam for exam in exams}
    ordered_exams = sorted(weights.items(), key=lambda item: item[1], reverse=True)

    for exam_id, weight in ordered_exams:
        exam = exams_by_id[exam_id]
        exam_budget = max(30, int(planned_capacity * weight))
        if used_minutes + 25 > planned_capacity:
            break

        pending_topics = sorted(
            [topic for topic in exam.topics if topic.progress_percent < 100],
            key=lambda topic: (-calculate_weakness_score(topic), topic.progress_percent, -topic.difficulty, topic.topic_id),
        )
        if not pending_topics:
            continue

        exam_used = 0
        max_tasks = max(1, ceil(exam_budget / _base_task_minutes(travel_mode, comeback_mode)))
        for topic in pending_topics[:max_tasks]:
            minutes = _base_task_minutes(travel_mode, comeback_mode)
            if exam_used + minutes > exam_budget and exam_used > 0:
                break
            if used_minutes + minutes > planned_capacity:
                break
            weakness = calculate_weakness_score(topic)
            task_type = _task_type_for_topic(topic, target_date, exam.exam_date, backlog_minutes > 0)
            specs.append(
                DynamicTaskSpec(
                    exam_id=exam.exam_id,
                    topic_id=topic.topic_id,
                    task_type=task_type,
                    estimated_minutes=minutes,
                    priority_reason=_priority_reason(
                        manual_priority=exam.priority,
                        days_left=max((exam.exam_date - target_date).days, 0),
                        weakness=weakness,
                        backlog_minutes=backlog_minutes,
                    ),
                    priority_score=round((weight * 100) + weakness + max(0, exam.priority), 2),
                )
            )
            used_minutes += minutes
            exam_used += minutes

    return specs


def _base_task_minutes(travel_mode: bool, comeback_mode: bool) -> int:
    if travel_mode:
        return 30
    if comeback_mode:
        return 40
    return 55


def _task_type_for_topic(topic: TopicPlanningInput, target_date: date, exam_date: date, backlog_active: bool) -> str:
    days_left = max((exam_date - target_date).days, 0)
    if backlog_active and topic.progress_percent < 50:
        return "revision"
    if topic.weak_score >= 70:
        return "practice"
    if days_left <= 45:
        return "PYQ"
    if topic.progress_percent < 35:
        return "concept"
    return "revision"


def _priority_reason(manual_priority: int, days_left: int, weakness: float, backlog_minutes: int) -> str:
    parts = [
        f"manual priority {manual_priority}",
        f"{days_left} days left",
        f"weakness {round(weakness, 1)}",
    ]
    if backlog_minutes:
        parts.append(f"backlog capped at {backlog_minutes} min")
    return "; ".join(parts)
