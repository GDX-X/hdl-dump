"""Regression on disposable image files; pass the built executable path."""
from pathlib import Path
import struct,subprocess,json,hashlib,sys,tempfile
temporary=tempfile.TemporaryDirectory(prefix='hdl-test-')
base=Path(temporary.name); exe=Path(sys.argv[1]).resolve()
def header(index,count,name,kind,sub=False):
 h=bytearray(1024); h[4:8]=b'APA\0'
 struct.pack_into('<II',h,8,((index+1)%count)*16384,((index-1)%count)*16384)
 h[16:16+len(name)]=name
 struct.pack_into('<IIHHI',h,64,index*16384,16384,kind,int(sub),1 if index==1 and count==3 else 0)
 struct.pack_into('<6BH',h,80,0,0,0,12,11,11,2026)
 if sub: struct.pack_into('<II',h,88,16384,1)
 if index==1 and count==3: struct.pack_into('<II',h,512,32768,16384)
 struct.pack_into('<I',h,0,sum(struct.unpack('<256I',h))&0xffffffff)
 return h
for count in [1,3]:
 image=base/f'inventory-fixture-{count}.img'
 with image.open('wb') as f:
  f.truncate(64*1024**2)
  for i in range(count):
   f.seek(i*8*1024**2); f.write(header(i,count,b'__mbr' if i==0 else b'__.CUSTOM' if i==1 else b'',1 if i==0 else 0x1337,i==2))
  if count>1:
   game=bytearray(1024); title=b'Test "quotes"; tab\t and \\ slash'; game[8:8+len(title)]=title
   game[0xac:0xac+11]=b'SLES_123.45'; game[0xec]=0x14
   f.seek(8*1024**2+0x101000); f.write(game)
 before=hashlib.sha256(image.read_bytes()).hexdigest()
 r=subprocess.run([str(exe),'hdl_toc2',str(image),'--all'],capture_output=True,text=True)
 assert r.returncode==0,(r.stdout,r.stderr)
 data=json.loads(r.stdout); assert len(data['partitions'])==count
 if count>1:
  assert data['partitions'][1]['game']['title']==title.decode()
  assert data['partitions'][1]['size_kb']==16384
  assert data['partitions'][2]['name']==''
 for command in ['hdl_toc','hdl_toc2']:
  for extra in [[],['--csv']]:
   a=subprocess.run([str(exe),command,str(image),*extra],capture_output=True)
   assert a.returncode==0, a.stderr
   if count>1 and command=='hdl_toc2':
    assert b'__.CUSTOM' in a.stdout
 assert hashlib.sha256(image.read_bytes()).hexdigest()==before
 print('PASS fixture',count,': JSON, escaped title, sizes, sub-segments, text/CSV output, no image writes.')
 image.unlink()

temporary.cleanup()
