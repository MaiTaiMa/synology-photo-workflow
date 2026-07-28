import time,pytest
from app.runtime import RunBudget,PauseRequested

def test_expired_budget_requests_pause():
 b=RunBudget(0);time.sleep(.001)
 with pytest.raises(PauseRequested,match='timebudgetexceeded:next'):b.checkpoint('next')
def test_explicit_stop_requests_pause():
 b=RunBudget(1);b.request_stop()
 with pytest.raises(PauseRequested,match='stoprequested:work'):b.checkpoint('work')
