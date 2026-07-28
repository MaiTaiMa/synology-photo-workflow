from app.calibration import _status,_trend
def test_calibration_has_progress_states():
 m={'terminalagreement':1,'rejecttokeeprate':0,'rejecttoreviewrate':0}
 assert _status([1,2],[(1,1)]*2,m,{'minimumreviewedbatches':3,'minimumreviewedimages':3},[])[0]=='learning'
 assert _status([1],[(1,1)],m,{'minimumreviewedbatches':1,'minimumreviewedimages':2},[])[0]=='collecting'
def test_trend_is_metric_delta():
 assert _trend({'terminalagreement':.9},{'metrics':{'terminalagreement':.8}})['terminalagreement']==.1
