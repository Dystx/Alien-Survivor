"""Motion-preview tests. All pixels are disposable fixtures, not production art."""
import base64
import copy
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('preview_artpack', ROOT/'tools/preview_artpack.py')
preview = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preview)


class MotionReviewChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.asset = {'id':'fixture','category':'actor','cell':[24,24],'pivot':[12,20], 'directions':['e','w'], 'clips':{'move':{'frames':3,'fps':12,'loop':True,'min_unique_frames':3}}}
        self.paths = {}
        for d in self.asset['directions']:
            self.paths[d] = []
            for n in range(3):
                im = Image.new('RGBA',(24,24))
                draw = ImageDraw.Draw(im)
                draw.rectangle((7,5,15,17),fill=(80+n*12,120 if d=='e' else 160,130,255))
                draw.rectangle((6+n,17,10+n,20),fill=(50,50,50,255))
                p = self.root / f'{d}_{n}.png'; im.save(p); self.paths[d].append(p)
    def tearDown(self):
        self.temp.cleanup()
    def data(self):
        return preview.prepare_clip(self.asset,'move',self.paths)
    def test_valid_review_is_not_approval(self):
        self.assertEqual(self.data()['status'],'review_only_not_approval')
    def test_pixel_preservation(self):
        encoded,_ = preview.frame_data(self.paths['e'][0],[24,24])
        restored=Image.open(io.BytesIO(base64.b64decode(encoded)))
        self.assertEqual(restored.tobytes(),Image.open(self.paths['e'][0]).tobytes())
    def test_metadata_preservation(self):
        data=self.data()
        self.assertEqual(data['pivot'],[12,20]); self.assertEqual(data['fps'],12); self.assertTrue(data['loop'])
    def test_missing_clip_rejected(self):
        with self.assertRaises(preview.ReviewError): preview.prepare_clip(self.asset,'walk',self.paths)
    def test_missing_direction_rejected(self):
        del self.paths['w']
        with self.assertRaises(preview.ReviewError): self.data()
    def test_incomplete_clip_rejected(self):
        self.paths['e'].pop()
        with self.assertRaises(preview.ReviewError): self.data()
    def test_wrong_dimensions_rejected(self):
        Image.new('RGBA',(32,32)).save(self.paths['e'][0])
        with self.assertRaises(preview.ReviewError): self.data()
    def test_empty_crop_rejected(self):
        Image.new('RGBA',(24,24)).save(self.paths['e'][0])
        with self.assertRaises(preview.ReviewError): self.data()
    def test_translated_still_rejected(self):
        original=Image.open(self.paths['e'][0]).copy()
        for n,p in enumerate(self.paths['e']):
            im=Image.new('RGBA',(24,24)); im.paste(original,(n,0)); im.save(p)
        with self.assertRaises(preview.ReviewError): self.data()
    def test_duplicate_directions_rejected(self):
        for a,b in zip(self.paths['e'],self.paths['w']): b.write_bytes(a.read_bytes())
        with self.assertRaises(preview.ReviewError): self.data()
    def test_loop_endpoint_rejected_even_when_some_holds_are_allowed(self):
        self.asset['clips']['move']['min_unique_frames']=2
        self.paths['e'][-1].write_bytes(self.paths['e'][0].read_bytes())
        with self.assertRaises(preview.ReviewError): self.data()
    def test_offline_viewer_controls_and_no_live_files(self):
        out=self.root/'view.html'; preview.write_review(self.data(),out)
        text=out.read_text()
        for marker in ['data:image/png;base64,','id="scrub"','id="bg"','id="speed"','id="dir"','requestAnimationFrame']:
            self.assertIn(marker,text)
        self.assertNotIn('<script src=',text)
    def test_no_overwrite(self):
        out=self.root/'KEEP.html'; out.write_text('keep')
        with self.assertRaises(preview.ReviewError): preview.write_review(self.data(),out)
        self.assertEqual(out.read_text(),'keep')
    def test_socket_data_included(self):
        sockets={'e':[{'muzzle':[18,12]}]*3}
        self.assertEqual(preview.prepare_clip(self.asset,'move',self.paths,sockets)['sockets'],sockets)


if __name__=='__main__':
    unittest.main(verbosity=2)
