"""
Root conftest.py — makes the ``lambda`` directory importable despite
``lambda`` being a Python keyword.

We register the directory as a package named ``lbd`` (short for lambda)
so that test files can write::

    from lbd.shared.config import MAHACHAI_BBOX
"""

import importlib
import sys
from pathlib import Path

# Add the project root to sys.path so that ``lambda/`` is discoverable.
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Import the ``lambda`` directory as a package named ``lbd``.
_lambda_pkg = importlib.import_module("lambda")
sys.modules["lbd"] = _lambda_pkg

# Also register sub-packages so ``from lbd.shared.config import ...`` works.
for sub in [
    "lambda.shared",
    "lambda.shared.config",
    "lambda.shared.models",
    "lambda.shared.supabase_client",
    "lambda.data_pipeline",
    "lambda.data_pipeline.fetchers",
    "lambda.data_pipeline.validator",
    "lambda.data_pipeline.retry",
    "lambda.mangrove_monitor",
    "lambda.mangrove_monitor.ndvi_calculator",
    "lambda.mangrove_monitor.change_detector",
    "lambda.mangrove_monitor.carbon_calculator",
    "lambda.fsi_engine",
    "lambda.fsi_engine.score_functions",
    "lambda.fsi_engine.fsi_calculator",
    "lambda.fsi_engine.fsi_map",
    "lambda.fsi_engine.serializers",
    "lambda.yield_predictor",
    "lambda.yield_predictor.predictor",
    "lambda.yield_predictor.revenue_forecast",
    "lambda.yield_predictor.catch_ingestion",
    "lambda.restoration_planner",
    "lambda.restoration_planner.site_analyzer",
    "lambda.restoration_planner.seedling_tracker",
    "lambda.data_management",
    "lambda.data_management.backup",
    "lambda.data_management.archiver",
    "lambda.orchestration",
    "lambda.orchestration.eventbridge_config",
    "lambda.orchestration.pipeline_orchestrator",
]:
    try:
        mod = importlib.import_module(sub)
        alias = sub.replace("lambda", "lbd", 1)
        sys.modules[alias] = mod
    except ImportError:
        pass
