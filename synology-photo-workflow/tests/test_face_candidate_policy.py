from app.photoworkflow import defaults
from app.familyrecognition import propose_known_face_crops
def test_face_candidates_are_disabled_and_conservative_by_default():
 c=defaults()['familyrecognition'];assert c['candidatecropsenabled'] is False;assert c['minbestsecondmargin']>0;assert c['minfacesizepx']>=80
def test_non_keep_never_proposes_face_crop():
 assert propose_known_face_crops('missing.jpg',{}, {'familyrecognition':{'candidatecropsenabled':True}},'reject')==[]
