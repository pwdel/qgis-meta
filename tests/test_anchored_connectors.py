import os,subprocess,unittest
from pathlib import Path
from qgis_meta.runtime import runtime_environment
@unittest.skipUnless(os.environ.get('QGIS_META_QGIS_APP'),'explicit QGIS runtime required')
class AnchorTests(unittest.TestCase):
 def test_native_anchors(self):
  py,env=runtime_environment(qgis_app=os.environ['QGIS_META_QGIS_APP'])
  result=subprocess.run([py,str(Path(__file__).with_name('native_anchors_case.py'))],env=env,text=True,capture_output=True)
  self.assertEqual(result.returncode,0,result.stdout+result.stderr)
