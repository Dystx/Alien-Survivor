"""Small synthetic fixtures exercise validation; they are never production art."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from PIL import Image

MODULE=Path(__file__).resolve().parents[1]/'tools/artpack.py'
spec=importlib.util.spec_from_file_location('artpack',MODULE)
a=importlib.util.module_from_spec(spec); spec.loader.exec_module(a)

class ContractTests(unittest.TestCase):
    def test_exact_scope(self):
        contract, assets=a.load_contract()
        self.assertEqual(len(assets),91)
        self.assertEqual(sum(len(list(a.slots(v))) for v in assets.values()),1134)
        self.assertEqual(sum(len(list(a.slots(assets[k],set(contract['batch_001']['stages'])))) for k in contract['batch_001']['assets']),212)
    def test_empty_pack_is_not_ready(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            (root/'pack.json').write_bytes((a.PACK/'pack.json').read_bytes())
            report=a.audit(root)
            self.assertEqual(sum(r['present'] for r in report),0)
            self.assertFalse(any(r['status']=='approved' for r in report))

class DeliveryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.root=Path(self.temp.name)
        self.asset={'id':'runner','category':'actor','cell':[16,16],'pivot':[8,13], 'directions':['e','s','w','n'],'source_required':True, 'clips':{'move':{'frames':2,'fps':12,'loop':True,'min_unique_frames':2,'stage':'base'}}}
        profile={k:v for k,v in self.asset.items() if k!='id'}; profile['ids']=['runner']
        contract={'schema_version':1,'state':'specification_baseline_art_not_approved','batch_001':{'assets':['runner']},'asset_groups':[profile], 'image_contract':{'atlas_gutter_pixels':2,'max_atlas_size':64}}
        (self.root/'pack.json').write_text(json.dumps(contract))
        self.required=list(a.slots(self.asset))
        for index,(_,_,_,rel) in enumerate(self.required):
            p=self.root/rel;p.parent.mkdir(parents=True,exist_ok=True)
            image=Image.new('RGBA',(16,16))
            for y in range(5,12):
                for x in range(5,11): image.putpixel((x,y),(40+index*8,60,90,255))
            image.save(p)
        source=self.root/'families/runner/source/fixture.txt';source.parent.mkdir(parents=True);source.write_text('SYNTHETIC UNIT TEST ONLY. NOT CHARACTER ART.')
        self.delivery={'asset_id':'runner','status':'review','spec_sha256':a.digest(self.root/'pack.json'),'sources':[{'path':source.relative_to(self.root).as_posix(),'sha256':a.digest(source),'provenance':'Synthetic test fixture'}],'frame_sha256':{}, 'review':{},'public_source_permission':False}
        self.save_delivery()
    def tearDown(self): self.temp.cleanup()
    def save_delivery(self):
        self.delivery['frame_sha256']={r:a.digest(self.root/r) for _,_,_,r in self.required if (self.root/r).exists()}
        (self.root/'families/runner/delivery.json').write_text(json.dumps(self.delivery))
    def first(self): return self.root/self.required[0][3]
    def approve_fixture(self):
        self.delivery['status']='approved'
        self.delivery['review']={key:True for key in a.REVIEWS}
        self.delivery['owner_approval']={'reviewer':'synthetic-test-only','date':'fixture-date','evidence':'unit-test-fixture; no real owner approval asserted'}
        self.delivery['public_source_permission']=True
        self.save_delivery()
    def test_valid_review_does_not_become_approved(self):
        report=a.check_delivery(self.root,self.asset,require_complete=True)
        self.assertEqual(report['status'],'review')
    def test_export_requires_owner_approval(self):
        with self.assertRaises(a.PackError): a.export_family(self.root,self.asset,self.root/'out')
    def test_missing_frame_rejected(self):
        self.first().unlink();self.save_delivery()
        with self.assertRaises(a.PackError): a.check_delivery(self.root,self.asset,require_complete=True)
    def test_missing_delivery_rejected(self):
        (self.root/'families/runner/delivery.json').unlink()
        with self.assertRaises(a.PackError): a.check_delivery(self.root,self.asset)
    def test_transparent_frame_rejected(self):
        Image.new('RGBA',(16,16)).save(self.first());self.save_delivery()
        with self.assertRaisesRegex(a.PackError,'invisible'): a.check_delivery(self.root,self.asset)
    def test_wrong_cell_rejected(self):
        Image.new('RGBA',(20,16),(1,1,1,255)).save(self.first());self.save_delivery()
        with self.assertRaisesRegex(a.PackError,'expected RGBA'): a.check_delivery(self.root,self.asset)
    def test_wrong_mode_rejected(self):
        Image.new('RGB',(16,16),(20,30,40)).save(self.first());self.save_delivery()
        with self.assertRaises(a.PackError): a.check_delivery(self.root,self.asset)
    def test_edge_clipping_rejected(self):
        with Image.open(self.first()) as im: image=im.copy()
        image.putpixel((0,8),(20,30,40,255));image.save(self.first());self.save_delivery()
        with self.assertRaisesRegex(a.PackError,'border'): a.check_delivery(self.root,self.asset)
    def test_duplicate_motion_rejected(self):
        (self.root/self.required[1][3]).write_bytes(self.first().read_bytes());self.save_delivery()
        with self.assertRaisesRegex(a.PackError,'duplicated'): a.check_delivery(self.root,self.asset)
    def test_unannounced_new_frame_rejected(self):
        p=self.first().parent/'099.png';p.write_bytes(self.first().read_bytes())
        with self.assertRaisesRegex(a.PackError,'undeclared'): a.check_delivery(self.root,self.asset)
    def test_hash_binds_content(self):
        self.first().write_bytes(self.first().read_bytes()+b'new-bytes')
        with self.assertRaisesRegex(a.PackError,'changed since'): a.check_delivery(self.root,self.asset)
    def test_changed_source_rejected(self):
        (self.root/'families/runner/source/fixture.txt').write_text('changed')
        with self.assertRaisesRegex(a.PackError,'source missing or modified'): a.check_delivery(self.root,self.asset)
    def test_path_escape_rejected(self):
        for p in ['../outside.txt','/absolute.txt','foo\\bar']:
            with self.assertRaises(a.PackError): a.safe(self.root,p)
    def test_stale_spec_rejected(self):
        self.delivery['spec_sha256']='0'*64;self.save_delivery()
        with self.assertRaisesRegex(a.PackError,'specification'): a.check_delivery(self.root,self.asset)
    def test_approval_without_review_rejected(self):
        self.delivery['status']='approved';self.save_delivery()
        with self.assertRaisesRegex(a.PackError,'review'): a.check_delivery(self.root,self.asset)
    def test_incomplete_approved_rejected(self):
        self.approve_fixture();self.first().unlink();self.save_delivery()
        with self.assertRaises(a.PackError): a.check_delivery(self.root,self.asset)
    def test_export_pixel_regions_and_pivot(self):
        self.approve_fixture()
        result=a.export_family(self.root,self.asset,self.root/'out')
        folder=self.root/'out/runner'
        self.assertTrue((folder/'sprite_frames.tres').is_file())
        self.assertIn('offset = Vector2(0.0, -5.0)',(folder/'sprite.tscn').read_text())
        for record,(_,_,_,rel) in zip(result['frames'],self.required):
            page=result['pages'][record['page']]['file'];x,y,w,h=record['region']
            with Image.open(folder/page) as image,Image.open(self.root/rel) as src:
                self.assertEqual(image.crop((x,y,x+w,y+h)).tobytes(),src.tobytes())
        with self.assertRaises(a.PackError): a.export_family(self.root,self.asset,self.root/'out')
    def test_invalid_pivot_rejected(self):
        c=json.loads((self.root/'pack.json').read_text());c['asset_groups'][0]['pivot']=[8,16]
        (self.root/'pack.json').write_text(json.dumps(c))
        with self.assertRaises(a.PackError): a.load_contract(self.root)
    def test_duplicate_id_rejected(self):
        c=json.loads((self.root/'pack.json').read_text());c['asset_groups'][0]['ids'].append('runner')
        (self.root/'pack.json').write_text(json.dumps(c))
        with self.assertRaises(a.PackError): a.load_contract(self.root)
    def test_floor_diamond_and_raised_lip(self):
        p=self.root/'floor.png';image=Image.new('RGBA',(96,48))
        for y in range(48):
            for x in range(96):
                if abs(x+.5-48)/48+abs(y+.5-24)/24<=1: image.putpixel((x,y),(70,70,70,255))
        image.save(p);asset={'category':'floor','cell':[96,48]}
        a.check_png(p,asset)
        for x in range(32,64): image.putpixel((x,47),(60,60,60,255))
        image.save(p)
        with self.assertRaisesRegex(a.PackError,'diamond'): a.check_png(p,asset)

if __name__=='__main__': unittest.main(verbosity=2)
