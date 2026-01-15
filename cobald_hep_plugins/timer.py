"""Time-based demand control decorators and helpers."""

from __future__ import annotations

import asyncio
import bisect
from datetime import date, datetime, timedelta
from typing import Mapping

from cobald.daemon import service
from cobald.interfaces import Pool, Controller

@service(flavour=asyncio)
class Timer(Controller):
    """Control pool demand based on a daily time schedule."""

    def __init__(
        self,
        target: Pool,
        schedule: Mapping[str, float],
    ) -> None:
        """Create a timer controller.

        Args:
            target: Pool whose demand is controlled by this timer.
            schedule: Mapping of "HH:MM" to demand values.
        """
        super().__init__(target=target)
        schedule = {
            datetime.strptime(time, "%H:%M").time(): demand
            for time, demand in schedule.items()
        }
        schedule = dict(sorted(schedule.items(), key=lambda item: item[0]))
        assert len(schedule) > 0, "Schedule must contain at least one entry."
        assert all(
            demand >= 0 for demand in schedule.values()
        ), "All scheduled demands must be non-negative."
        self.schedule = schedule
    
    async def run(self) -> None:
        """Update the demand periodically according to the schedule."""
        today = date.today()
        sched_times = list(self.schedule)

        start_time = datetime.now().time()
        idx = bisect.bisect_right(sched_times, start_time) - 1
        idx %= len(sched_times)

        while True:
            self.target.demand = self.schedule[sched_times[idx]]

            idx = (idx + 1) % len(sched_times)
            if idx == 0:
                today += timedelta(days=1) 

            next_time = datetime.combine(today, sched_times[idx])
            sleep_seconds = (next_time - datetime.now()).total_seconds()
            await asyncio.sleep(sleep_seconds)

