"""Time-based demand control decorators and helpers."""

from __future__ import annotations

import asyncio
from datetime import datetime, time as datetime_time
from typing import Dict, Iterable, Mapping, Union

from cobald.daemon import service
from cobald.interfaces import Pool, PoolDecorator
from cobald.utility import enforce

TimeInput = Union[str, datetime_time]
Schedule = Mapping[TimeInput, float]


def str_to_time(value: str) -> datetime_time:
    """Convert a HH:MM string into a :class:`datetime.time` object."""
    hours_str, minutes_str = value.split(":")
    hours, minutes = int(hours_str), int(minutes_str)
    return datetime_time(hour=hours, minute=minutes)


def latest_timestamp(
    times: Iterable[datetime_time]
) -> datetime_time:
    """Return the latest timestamp that is not later than ``reference``."""
    ordered_times = sorted(times) # ascending
    current_time = datetime.now().time()
    for candidate in reversed(ordered_times): # descending
        if candidate <= current_time:
            return candidate
    # All configured times are in the future relative to ``current_time``.
    # return latest timestamp
    return ordered_times[-1]


@service(flavour=asyncio)
class Timer(PoolDecorator):
    """
    Decorator that adjusts demand based on a daily schedule.

    :param target: pool being decorated
    :param schedule: mapping of ``HH:MM`` times (or ``datetime.time`` instances)
                     to the demand that should become active at that time
    :param interval: interval in seconds between schedule checks
    """

    def __init__(
        self,
        target: Pool,
        schedule: Schedule,
        interval: int = 300,
    ):
        super().__init__(target)
        
        self.interval = interval

        schedule = {str_to_time(key): value for key,value in schedule.items()}
        self.schedule = schedule
        self.latest_sched_demand = self._refresh_demand()

    @property
    def demand(self) -> float:
        return self.target.demand

    @demand.setter
    def demand(self, value: float) -> None:
        # Ignore user supplied demand and always enforce the scheduled value.
        self.target.demand = self.latest_sched_demand

    async def run(self) -> None:
        """Update the demand periodically according to the schedule."""
        while True:
            self._refresh_demand()
            await asyncio.sleep(self.interval)

    def _refresh_demand(self) -> float:
        """Look up the demand that should currently be active."""
        latest_sched_time = latest_timestamp(self.schedule.keys())
        self.latest_sched_demand = self.schedule[latest_sched_time]
        self.target.demand = self.latest_sched_demand
        return self.latest_sched_demand
