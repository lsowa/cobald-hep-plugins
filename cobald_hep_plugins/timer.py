from cobald.interfaces import Pool, PoolDecorator

from cobald.utility import enforce

from tardis.interfaces.executor import Executor
from tardis.utilities.executors.shellexecutor import ShellExecutor

import asyncio
import time
from cobald.daemon import service


def str_to_time(time: str):
    hh, mm = time.split(":")
    hh, mm = int(hh), int(mm)
    return time(hh, mm)

def latest_timestamp(times: Iterable):
    now = time.time()
    non_future_candidates = [time for time in times if time <= now]
    if not non_future_candidates:
        raise ValueError(f"Could not match {now} to a non-future time in {times}")
    return max(non_future_candidates)


@service(flavour=asyncio)
class Stopper(PoolDecorator):
    """
    Decorator that sets demand dependent on time.

    :param target: the pool
    :param interval: interval in seconds between update steps.

    If there are pending jobs on the partition, the demand is not modified.
    The demand is set to 0 as long as no pending jobs are detected.

    The default interval is 300 (5 minutes). The script has to be specified.
    """

    def __init__(
        self,
        target: Pool,
        schedule: dict,
        interval: int = 300,
    ):
        super().__init__(target)
        enforce(interval > 0, ValueError("interval must be positive"))
        self.schedule = schedule
        self.interval = interval
        self.latest_sched_demand = None 

    @property
    def demand(self) -> float:
        return self.target.demand

    @demand.setter
    def demand(self, value: float):
        # ignore value
        self.target.demand = self.latest_sched_demand

    async def run(self):
        """Retrieve the number of pending jobs"""
        while True:
            latest_sched_time = latest_timestamp(self.schedule.keys())
            self.latest_sched_demand = self.schedule[latest_sched_time]
            await asyncio.sleep(self.interval)

    
