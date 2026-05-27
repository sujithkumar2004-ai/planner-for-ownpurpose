from datetime import date
import unittest

from app.planner_engine import (
    BACKLOG_LOAD_LIMIT,
    PLANNER_START,
    ExamPlanningInput,
    TopicPlanningInput,
    calculate_backlog_pressure,
    calculate_daily_capacity,
    calculate_exam_weights,
    calculate_weakness_score,
    generate_dynamic_day_plan,
)


class PlannerEngineTests(unittest.TestCase):
    def test_daily_capacity_respects_travel_comeback_and_upper_bound(self):
        self.assertEqual(calculate_daily_capacity(10), 360)
        self.assertEqual(calculate_daily_capacity(4, travel_mode=True, travel_daily_minutes=90), 90)
        self.assertEqual(calculate_daily_capacity(4, comeback_mode=True), 180)
        self.assertEqual(calculate_daily_capacity(0), 45)

    def test_backlog_pressure_is_capped_at_twenty_percent(self):
        capacity = 300
        pressure = calculate_backlog_pressure(backlog_tasks=20, daily_capacity_minutes=capacity)
        self.assertLessEqual(pressure, int(capacity * BACKLOG_LOAD_LIMIT))
        self.assertEqual(pressure, 60)

    def test_weakness_score_prioritizes_weak_unfinished_topics(self):
        weak = TopicPlanningInput(topic_id=1, progress_percent=20, weak_score=90, difficulty=5, subject_weight=1.5)
        strong = TopicPlanningInput(topic_id=2, progress_percent=90, weak_score=10, difficulty=1, subject_weight=1.0)
        self.assertGreater(calculate_weakness_score(weak), calculate_weakness_score(strong))

    def test_exam_weights_respect_manual_priority_and_nearest_exam(self):
        target = PLANNER_START
        near_high_priority = ExamPlanningInput(
            exam_id=1,
            priority=5,
            exam_date=date(2026, 7, 1),
            topics=[TopicPlanningInput(topic_id=10, progress_percent=10, weak_score=70)],
        )
        far_low_priority = ExamPlanningInput(
            exam_id=2,
            priority=1,
            exam_date=date(2027, 2, 1),
            topics=[TopicPlanningInput(topic_id=20, progress_percent=10, weak_score=70)],
        )
        weights = calculate_exam_weights([near_high_priority, far_low_priority], target)
        self.assertGreater(weights[1], weights[2])
        self.assertAlmostEqual(sum(weights.values()), 1.0, places=3)

    def test_dynamic_day_plan_locks_before_june_first(self):
        exam = ExamPlanningInput(
            exam_id=1,
            priority=5,
            exam_date=date(2026, 7, 1),
            topics=[TopicPlanningInput(topic_id=10, progress_percent=10, weak_score=90)],
        )
        self.assertEqual(
            generate_dynamic_day_plan(
                target_date=date(2026, 5, 31),
                exams=[exam],
                available_study_hours=4,
            ),
            [],
        )

    def test_dynamic_day_plan_favors_weak_topics_without_overload(self):
        exam = ExamPlanningInput(
            exam_id=1,
            priority=5,
            exam_date=date(2026, 7, 1),
            topics=[
                TopicPlanningInput(topic_id=10, progress_percent=80, weak_score=15),
                TopicPlanningInput(topic_id=11, progress_percent=25, weak_score=95),
                TopicPlanningInput(topic_id=12, progress_percent=40, weak_score=75),
            ],
        )
        plan = generate_dynamic_day_plan(
            target_date=PLANNER_START,
            exams=[exam],
            available_study_hours=2,
            backlog_tasks=10,
        )
        self.assertTrue(plan)
        self.assertEqual(plan[0].topic_id, 11)
        self.assertLessEqual(sum(task.estimated_minutes for task in plan), calculate_daily_capacity(2))
        self.assertIn("backlog capped", plan[0].priority_reason)


if __name__ == "__main__":
    unittest.main()
