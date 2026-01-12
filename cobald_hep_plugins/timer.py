"""Time-based demand control decorators and helpers."""

from __future__ import annotations

import bisect
from datetime import date, datetime, timedelta
from typing import Mapping

import trio
from cobald.daemon import service
from cobald.interfaces import Pool, Controller


Schedule = Mapping[str, float]

@service(flavour=trio)
class Timer(Controller):
    """Control pool demand based on a daily time schedule."""

    def __init__(
        self,
        target: Pool,
        schedule: Schedule,
    ) -> None:
        """Create a timer controller.

        Args:
            target: Pool whose demand is controlled by this timer.
            schedule: Mapping of "HH:MM" to demand values.
        """
        super().__init__(target=target)
        schedule = {
            datetime.strptime(key, "%H:%M").time(): value
            for key, value in schedule.items()
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
        keys = list(self.schedule)

        start_time = datetime.now().time()
        idx = bisect.bisect_right(keys, start_time) - 1
        idx %= len(keys)

        while True:
            self.target.demand = self.schedule[keys[idx]]
            
            idx = (idx + 1) % len(keys)
            if idx == 0:
                today += timedelta(days=1) 

            next_time = datetime.combine(today, keys[idx])
            sleep_seconds = max(0.0, (next_time - datetime.now()).total_seconds())
            await trio.sleep(sleep_seconds)

