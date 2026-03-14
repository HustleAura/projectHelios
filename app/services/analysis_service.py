from app.models.daily_log import DailyLog
from app.schemas.analysis import (
    DailyAnalysisResponse,
    HabitIndicators,
    MetricAnalysis,
)


class AnalysisService:
    """Stateless computation of daily analysis from a DailyLog row."""

    @staticmethod
    def compute(log: DailyLog) -> DailyAnalysisResponse:
        """
        Compute the daily analysis for a given log.

        Rules per metric:
          delta  = actual - target_snapshot
          status = "no_data" if actual is None
                 = "met"     if actual >= target_snapshot
                 = "under"   if actual < target_snapshot
        """

        print(f"[COMPUTE] Computing analysis for log_id={log.id}, date={log.date}")

        def _analyze(actual, target) -> MetricAnalysis:
            if actual is None:
                return MetricAnalysis(
                    actual=None,
                    target=target,
                    delta=None,
                    status="no_data",
                )
            delta = actual - target
            status = "met" if actual >= target else "under"
            return MetricAnalysis(
                actual=actual,
                target=target,
                delta=delta,
                status=status,
            )

        result = DailyAnalysisResponse(
            date=log.date,
            metrics={
                "calories": _analyze(log.calories_actual, log.calorie_target_snapshot),
                "protein": _analyze(log.protein_actual, log.protein_target_snapshot),
                "sleep": _analyze(log.sleep_actual, log.sleep_target_snapshot),
            },
            habits=HabitIndicators(
                workout_completed=log.workout_completed,
                is_period_day=log.is_period_day,
            ),
        )
        print(f"[COMPUTE] Done — calories={result.metrics['calories'].status}, protein={result.metrics['protein'].status}, sleep={result.metrics['sleep'].status}")
        return result
