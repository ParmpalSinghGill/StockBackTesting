from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from Prediction import CONFIG


@dataclass(frozen=True)
class BacktestRuntimeConfig:
    max_gap_down_percentage: float
    target_percent: float
    stop_loss_percent: float
    start_date: Optional[str]
    end_date: Optional[str]


def load_backtest_runtime_config() -> BacktestRuntimeConfig:
    """Single source of runtime settings while preserving existing defaults."""
    return BacktestRuntimeConfig(
        max_gap_down_percentage=CONFIG.MAXGAPDOWNBYPERCENTAGE,
        target_percent=CONFIG.TARGETPERCENT,
        stop_loss_percent=CONFIG.STOPLOSSPERCENT,
        start_date=CONFIG.STARTDATE,
        end_date=CONFIG.ENDDATE,
    )

