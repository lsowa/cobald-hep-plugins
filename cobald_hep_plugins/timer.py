"""Time-based demand control decorators and helpers."""

from __future__ import annotations


import trio
import bisect

from datetime import datetime
from datetime import date, timedelta
from typing import Mapping

from cobald.daemon import service
from cobald.interfaces import Pool, Controller



Schedule = Mapping[str, float]

@service(flavour=trio)
class Timer(Controller):
    def __init__(
        self,
        target: Pool,
        schedule: Schedule,
    ):
        super().__init__(target=target)
        # convert schedule keys to time objects
        schedule = {datetime.strptime(key, '%H:%M').time(): value for key,value in schedule.items()}
        
        # ensure schedule is sorted and valid
        schedule = dict(sorted(schedule.items(), key=lambda item: item[0]))
        assert len(schedule) > 0 , "Schedule must contain at least one entry."
        assert all(demand >= 0 for demand in schedule.values()) , "All scheduled demands must be non-negative."
        self.schedule = schedule
    
    async def run(self) -> None:
        """Update the demand periodically according to the schedule."""
        today = date.today()
        keys = list(self.schedule)

        # find starting index
        idx = bisect.bisect_right(keys, datetime.now().time()) - 1
        idx = idx % len(keys)

        while True:
            self.target.demand = self.schedule[keys[idx]]
            
            # setup next index and sleep until then
            idx = (idx + 1) % len(keys)
            if idx == 0:
                today += timedelta(days=1) 

            time_delta = datetime.combine(today, keys[idx]) - datetime.now()
            time_delta = max(0, time_delta.total_seconds())
            await trio.sleep(time_delta)


