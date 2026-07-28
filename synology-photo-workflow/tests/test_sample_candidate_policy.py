from app.photoworkflow import defaults
def test_sample_candidates_are_opt_in_and_conservative():
 s=defaults()['samples'];assert s['candidatesenabled'] is False;assert s['candidateratingmin']==5;assert s['candidatequalitymin']>=.75
