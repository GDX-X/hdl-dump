"""Regression on disposable image files; pass the built executable path."""
from pathlib import Path
import struct,subprocess,sys,tempfile
temporary=tempfile.TemporaryDirectory(prefix='hdl-test-')
base=Path(temporary.name); exe=Path(sys.argv[1]).resolve(); image=base/'short-rename-test.img'
name=b'PP.SLES-50507..HALF_LIFE'
with image.open('wb') as f:
 f.truncate(64*1024**2)
 for i,n in enumerate([b'__mbr',name]):
  h=bytearray(1024); h[4:8]=b'APA\0';struct.pack_into('<II',h,8,(1-i)*16384,(1-i)*16384);h[16:16+len(n)]=n
  struct.pack_into('<IIHHI',h,64,i*16384,16384,1 if i==0 else 0x1337,0,0)
  if not i:
   h[256:288]=b'Sony Computer Entertainment Inc.'; struct.pack_into('<II',h,288,2,131072)
  struct.pack_into('<I',h,0,sum(struct.unpack('<256I',h))&0xffffffff);f.seek(i*8*1024**2);f.write(h)
  if i:
   g=bytearray(1024);g[8:17]=b'Half-Life';g[0xac:0xb7]=b'SLES_505.07';g[0xec]=0x14;f.seek(8*1024**2+0x101000);f.write(g)
for a,b in [('Half-Life','Half-Life GDX'),('Half-Life GDX','Half-Life')]:
 r=subprocess.run([str(exe),'modify',str(image),a,b],capture_output=True,text=True);assert r.returncode==0,(r.stdout,r.stderr)
with image.open('rb') as f:
 f.seek(8*1024**2+16);raw=f.read(32)
print('APA ID bytes after round trip:',repr(raw));assert raw==name.ljust(32,b'\0')
r=subprocess.run([str(Path(sys.argv[2]).resolve())],input=f'device "{image}"\nrmpart "{name.decode()}"\nexit\n',text=True,capture_output=True)
assert '(!)' not in r.stdout+r.stderr,(r.stdout,r.stderr)
assert 'Half-Life' not in subprocess.check_output([str(exe),'hdl_toc',str(image)],text=True)
print('PASS: Half-Life -> Half-Life GDX -> Half-Life -> PFSShell deletion.')
image.unlink()

temporary.cleanup()
