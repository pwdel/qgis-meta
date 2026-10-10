import copy,unittest
from qgis_meta.research import validate_research,check_research_publication
class ResearchTests(unittest.TestCase):
 def record(self):
  return {'version':1,'focus_location_id':'test','candidates':[{'id':'test','title':'Study','stage':'researching','publish':False,'location':None,'jurisdiction':'unknown','hypothesis':'A path may exist','claims':[{'activity':'walking','status':'unknown','scope':'study area','evidence_ids':['trace']}],'evidence':[{'id':'trace','kind':'activity_trace','url':'https://www.strava.com/maps','checked_on':'2026-10-10','summary':'Pending login, no observation','supports':['activity_presence']}],'questions':['Who manages access?'],'observations':[],'review':None}]}
 def test_unknown_valid(self):self.assertEqual(validate_research(self.record()),[])
 def test_trace_cannot_grant_permission(self):
  r=self.record();r['candidates'][0]['claims'][0]['status']='allowed';self.assertTrue(validate_research(r))
 def test_promotion_needs_review(self):
  r=self.record();r['candidates'][0]['stage']='promoted';self.assertTrue(validate_research(r))
 def test_no_publication(self):
  r=self.record();r['candidates'][0]['publish']=True;self.assertTrue(validate_research(r))
 def test_missing_reference(self):
  r=self.record();r['candidates'][0]['claims'][0]['evidence_ids']=['absent'];self.assertTrue(validate_research(r))
 def test_authority_scoped_to_activity(self):
  r=self.record();c=r['candidates'][0];c['evidence'][0].update(kind='authority',supports=['walking']);c['claims'][0]['status']='allowed';self.assertFalse(validate_research(r));c['claims'][0]['activity']='camping';self.assertTrue(validate_research(r))
 def test_layout_boundary(self):
  class Item:
   def __init__(self,props):self.props=props
   def customProperty(self,k,d=None):return self.props.get(k,d)
   def id(self):return 'draft'
   def name(self):return 'atlas'
  errors=[];layer=Item({'qgis_meta/research_only':True});check_research_publication(Item({}),[layer],errors);self.assertTrue(errors)
  errors=[];check_research_publication(Item({'qgis_meta/layout_purpose':'research'}),[layer],errors);self.assertFalse(errors)
