"""FININT OMEGA — Research module."""

from core.research.benchmark import BenchmarkRunner
from core.research.deliverables import DeliverableGenerator
from core.research.grid import GridGenerator, GridPlanner
from core.research.memory import ResearchMemoryStore
from core.research.reports import ReportGenerator
from core.research.scheduled import ResearchScheduler, ScheduledExecutor
from core.research.watchlist import WatchlistResearchEngine
from core.research.workflows import ResearchWorkflowEngine

__all__ = [
    "BenchmarkRunner",
    "DeliverableGenerator",
    "GridGenerator",
    "GridPlanner",
    "ResearchMemoryStore",
    "ReportGenerator",
    "ResearchScheduler",
    "ScheduledExecutor",
    "WatchlistResearchEngine",
    "ResearchWorkflowEngine",
]

# Re-export deep research for convenience
from core.research import deep_research  # noqa: F401, E402
