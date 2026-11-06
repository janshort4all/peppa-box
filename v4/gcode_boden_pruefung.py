"""G-Code-Prüfung Boden (06.11.2026): je Schicht Abstand der Außenwand zur Außenkontur (Fasen, Fuzzy-Streifen), Lüfter, Linienarten.
Aufruf: python3 gcode_boden_pruefung.py datei.gcode"""
import re, sys, math, collections
import numpy as np
GC=sys.argv[1]
rx=re.compile(r'([XYZEF])(-?[\d.]+)')
layers=[];cur=None;x=y=z=0;typ=None;fan=0;e_on=False
for line in open(GC,errors='replace'):
    if line.startswith(';LAYER_CHANGE'):
        cur={'z':None,'paths':collections.defaultdict(list),'fan':set(),'len':collections.Counter(),'seg':[]};layers.append(cur);continue
    if line.startswith(';Z:') and cur is not None: cur['z']=float(line[3:])
    if line.startswith(';TYPE:'): typ=line[6:].strip(); 
    if line.startswith('M106') and cur is not None:
        m=re.search(r'S(\d+)',line); cur['fan'].add(int(m.group(1)) if m else 0)
    if line.startswith(('G1','G0','G2','G3')):
        d=dict(rx.findall(line.split(';')[0])); nx=float(d.get('X',x)); ny=float(d.get('Y',y))
        if cur is not None and 'E' in d and float(d['E'])>0 and (nx!=x or ny!=y):
            L=math.hypot(nx-x,ny-y); cur['len'][typ]+=L
            if typ=='Outer wall': cur['seg'].append((x,y,nx,ny))
        x,y=nx,ny
# Lage: Mittelpunkt der Außenwand in der höchsten Schicht mit Außenwand
allp=np.array([(s[0],s[1]) for L in layers for s in L['seg']])
cx=(allp[:,0].min()+allp[:,0].max())/2; cy=(allp[:,1].min()+allp[:,1].max())/2
W,R=140.,16.
def dout(px,py):
    h=W/2-R; qx,qy=abs(px-cx)-h,abs(py-cy)-h
    return math.hypot(max(qx,0),max(qy,0))+min(max(qx,qy),0)-R
print('Mitte Bett',round(cx,2),round(cy,2))
for i,L in enumerate(layers,1):
    segs=L['seg']
    if segs:
        ds=np.array([dout(s[2],s[3]) for s in segs]); n=len(segs)
        outer=ds[ds>-1.5]
        if not len(outer): print(f"S{i:2d} nur innere Außenwände"); continue
        info=f"AW-Punkte {n:5d}  d mittel {outer.mean():+.2f} min {outer.min():+.2f} max {outer.max():+.2f} std {outer.std():.3f}"
    else: info='keine Außenwand'
    top={k:round(v) for k,v in L['len'].most_common(6)}
    print(f"S{i:2d} z{L['z']:.2f} fan{sorted(L['fan'])} {info} {top}")
