from cobald_hep_plugins.timer import Timer, latest_timestamp, str_to_time
import pytest
import datetime
from datetime import time as datetime_time
from .utility import MockPool

SCHEDULE = {
    "18:03": 30.0,
    "06:59": 10.0,
    "00:30": 0.0,
    "12:38": 20.0,
}
SCHEDULE_DATETIME = {
    datetime_time(18, 3): 30.0,
    datetime_time(6, 59): 10.0,
    datetime_time(0, 30): 0.0,
    datetime_time(12, 38): 20.0,
}


def test_str_to_time():
    for str_time, expected_time in zip(SCHEDULE.keys(), SCHEDULE_DATETIME.keys()):
        assert str_to_time(str_time) == expected_time
    with pytest.raises(ValueError):
        str_to_time("invalid")
    with pytest.raises(ValueError):
        str_to_time("25:00")
    with pytest.raises(ValueError):
        str_to_time("12:60")

def test_schedule():    
    timer = Timer(target=MockPool, schedule=SCHEDULE)
    expected = {
        datetime_time(18, 3): 30.0,
        datetime_time(6, 59): 10.0,
        datetime_time(0, 30): 0.0,
        datetime_time(12, 38): 20.0,
    } 
    assert timer.schedule == expected
    

@pytest.mark.parametrize(
    "reference, expected_latest",
    [
        (datetime_time(18, 2),  datetime_time(12, 38)),
        (datetime_time(18, 3),  datetime_time(18, 3)),
        (datetime_time(18, 4),  datetime_time(18, 3)),
        (datetime_time(0, 0),   datetime_time(18, 3)),
        (datetime_time(23, 59), datetime_time(18, 3)),
        (datetime_time(7, 0),   datetime_time(6, 59)),
        (datetime_time(12, 1),  datetime_time(6, 59)),
    ],
)
def test_latest_timestamp(reference, expected_latest):
    latest = latest_timestamp(times=SCHEDULE_DATETIME.keys(), reference=reference)
    assert latest == expected_latest 

def test_demand():
    timer = Timer(target=MockPool, schedule=SCHEDULE)
    for demand in     [
        15.0,
        25.0,
        5.0,
        0.0,
        30.0,
    ]:  
        
        # set demand directly
        timer.latest_sched_demand = demand
        # ignore demand setter
        timer.demand = demand + 2.
        assert timer.demand == demand

def test_non_negative_demand():
    schedule = {
        "10:00": -5.0,
    }
    with pytest.raises(AssertionError):
        timer = Timer(target=MockPool, schedule=schedule)

