"""Regression on disposable image files; pass the built executable path."""
from pathlib import Path
import struct,subprocess,hashlib,json,sys,tempfile
temporary=tempfile.TemporaryDirectory(prefix='hdl-rename-')
base=Path(temporary.name)
exe=Path(sys.argv[1]).resolve()
old='Pro Evolution Soccer 2010'; new=old+' GDX'
def pname(title,prefix='PP.'):
 return prefix+'SLES-55555..'+''.join(c.upper() if c.isalnum() else '_' for c in title[:16])
def fixture(path,prefix):
 names=['__mbr',pname(old,prefix),pname('Other Game',prefix)]
 with path.open('wb') as f:
  f.truncate(40*1024**2)
  for i,name in enumerate(names):
   h=bytearray(1024); h[4:8]=b'APA\0'; struct.pack_into('<II',h,8,((i+1)%3)*16384,((i-1)%3)*16384)
   h[16:16+len(name)]=name.encode(); struct.pack_into('<IIHHI',h,64,i*16384,16384,1 if i==0 else 0x1337,0,0)
   struct.pack_into('<6BH',h,80,0,0,0,12,12,11,2026); struct.pack_into('<I',h,0,sum(struct.unpack('<256I',h))&0xffffffff)
   f.seek(i*8*1024**2); f.write(h)
   if i:
    g=bytearray(1024); struct.pack_into('<I',g,0,0xdeadfeed); title=(old if i==1 else 'Other Game').encode();g[8:8+len(title)]=title; g[0xac:0xac+11]=b'SLES_555.55';g[0xec]=0x14
    f.seek(i*8*1024**2+0x101000);f.write(g)
 return names
for prefix in ['PP.','__.']:
 path=base/'rename-regression.img'; names=fixture(path,prefix)
 before=path.read_bytes()
 r=subprocess.run([str(exe),'modify',str(path),old,new],capture_output=True,text=True)
 if '--expect-bug' in sys.argv:
  assert r.returncode!=0 and 'exists' in (r.stdout+r.stderr).lower(),(r.returncode,r.stdout,r.stderr)
  assert path.read_bytes()==before
  print('REPRODUCED:',prefix,old,'->',new,':',r.stderr.strip() or r.stdout.strip())
  path.unlink(); continue
 assert r.returncode==0,(r.returncode,r.stdout,r.stderr)
 after=path.read_bytes(); offset=8*1024**2+0x101000+8
 assert after[offset:offset+len(new)]==new.encode()
 assert after[:offset]==before[:offset] and after[offset+160:]==before[offset+160:]
 data=json.loads(subprocess.check_output([str(exe),'hdl_toc2',str(path),'--all'],text=True))
 assert data['partitions'][1]['name']==names[1] and data['partitions'][1]['game']['title']==new
 # Renaming to the same title is also a valid self-match.
 subprocess.run([str(exe),'modify',str(path),names[1],new],check=True,capture_output=True)
 # A collision with a different game must still be rejected without writing.
 before=path.read_bytes()
 r=subprocess.run([str(exe),'modify',str(path),names[1],'Other Game'],capture_output=True,text=True)
 assert r.returncode!=0 and 'exists' in (r.stdout+r.stderr).lower()
 assert path.read_bytes()==before
 # A genuinely different free partition name still renames both fields.
 subprocess.run([str(exe),'modify',str(path),names[1],'PES GDX'],check=True,capture_output=True)
 data=json.loads(subprocess.check_output([str(exe),'hdl_toc2',str(path),'--all'],text=True))
 assert data['partitions'][1]['name']==pname('PES GDX',prefix)
 assert data['partitions'][1]['game']['title']=='PES GDX'
 print('PASS:',prefix,'same partition / same title / true collision / new partition name / data preservation')
 path.unlink()

temporary.cleanup()
