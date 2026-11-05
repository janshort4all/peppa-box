"""G-Code-Prüfung Deckel (kopfüber, zweifarbig): Farbwechsel-Schicht, erste Schicht, Brücken über den Symbolen,
Fahrwege über den Vertiefungen (Fäden), Naht. Aufruf: python3 gcode_deckel_pruefung.py deckel.gcode
Lage auf dem Bett wird aus der Außenwand von Schicht 2 bestimmt (Deckel um y gedreht, wie M.deckel_kopfueber)."""
import re, sys, math, collections, json
f = sys.argv[1]
layers = []; cur = None; tool = None; x = y = z = 0.0; e_rel = True; typ = None; F = 0
for ln in open(f, encoding='utf-8', errors='ignore'):
    if ln.startswith(';LAYER_CHANGE'):
        cur = dict(z=None, tool=tool, types=collections.defaultdict(float), speeds=collections.defaultdict(list), fan=[], travels_over=0, n=len(layers)+1, segs=collections.defaultdict(list), tools=set([tool]))
        layers.append(cur); continue
    if ln.startswith(';Z:') and cur is not None: cur['z'] = float(ln[3:]); continue
    if ln.startswith(';TYPE:'): typ = ln[6:].strip(); continue
    m = re.match(r'^T(\d+)', ln)
    if m:
        tool = int(m.group(1))
        if cur: cur['tools'].add(tool); cur['tool'] = tool
        continue
    if ln.startswith('M106') and cur is not None:
        s = re.search(r'S(\d+)', ln); p = re.search(r'P(\d+)', ln)
        if s and not p: cur['fan'].append(int(s.group(1)))
        continue
    if ln.startswith('G1') or ln.startswith('G0') or ln.startswith('G2') or ln.startswith('G3'):
        d = dict((k, float(v)) for k, v in re.findall(r'([XYZEF])(-?[\d.]+)', ln.split(';')[0]))
        nx, ny = d.get('X', x), d.get('Y', y)
        if 'Z' in d: z = d['Z']
        if 'F' in d: F = d['F']
        L = math.hypot(nx - x, ny - y)
        if cur is not None and L > 0:
            if d.get('E', 0) > 0:
                cur['types'][typ] += L; cur['speeds'][typ].append(F / 60)
                cur['segs'][typ].append((x, y, nx, ny, d['E']))
            else:
                cur['segs']['_travel'].append((x, y, nx, ny, 0))
        x, y = nx, ny
if False: json.dump([dict(n=l['n'], z=l['z'], tools=sorted(t for t in l['tools'] if t is not None), types={k: round(v) for k, v in l['types'].items()},
                vmin={k: round(min(v)) for k, v in l['speeds'].items()}, vmax={k: round(max(v)) for k, v in l['speeds'].items()},
                fan=sorted(set(l['fan']))) for l in layers], open('schichten.json', 'w'), indent=0)
if False: pickle.dump([dict(n=l['n'], z=l['z'], segs=dict(l['segs'])) for l in layers], open('segs.pkl', 'wb'))

import numpy as np
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
import model as M
from shapely.geometry import Polygon, LineString
from shapely.ops import unary_union
from shapely import make_valid
print(f"Schichten {len(layers)}")
for l in layers[:6]:
    print(f"  Schicht {l['n']} z {l['z']}: Filament {sorted(t for t in l['tools'] if t is not None)} {dict((k, round(v)) for k, v in l['types'].items())}")
ow = np.array([(a, b, c_, d) for a, b, c_, d, e in layers[1]['segs']['Outer wall']])
cx = (ow[:, [0, 2]].min() + ow[:, [0, 2]].max()) / 2; cy = (ow[:, [1, 3]].min() + ow[:, [1, 3]].max()) / 2
lb = M.LID_CS.bounds(); lx, ly = (lb[0] + lb[2]) / 2, (lb[1] + lb[3]) / 2      # Deckel ist symmetrisch: Mitte ↔ Mitte
OX = cx + lx; OY = cy - ly
print(f"Lage: Bett X = {OX:.2f} − x, Bett Y = y + {OY:.2f}")
fx = lambda x, y: (OX - x, y + OY)
def cs2shp(cs):
    g = None
    for q in cs.to_polygons():
        q = np.asarray(q)
        if len(q) < 3: continue
        q = make_valid(Polygon([fx(*a) for a in q])); g = q if g is None else g.symmetric_difference(q)
    return g
sym, sym_only = cs2shp(M.pad_symbols()), cs2shp(M.pad_symbols(rings=False))
tool1 = [l['n'] for l in layers if len([t for t in l['tools'] if t is not None]) > 1]
print("Farbwechsel in Schicht", tool1, "(soll 5: Schicht 1–4 beige = 0,8 mm)")
first = layers[0]['types']
print("Schicht 1:", "Rand/Umrandung vorhanden!" if any(k in ('Brim', 'Skirt') for k in first) else "keine Umrandung", "| Innenwand:", round(first.get('Inner wall', 0)), "mm (soll 0)")
inner = sym.buffer(-0.15)
for l in layers[1:4]:
    tr = [LineString([(a, b), (c_, d)]) for a, b, c_, d, e in l['segs'].get('_travel', [])]
    hit = [t for t in tr if t.intersects(inner)]
    print(f"Schicht {l['n']}: Fahrwege über Symbolen/Ringen {len(hit)}, längste Strecke über Luft {max([t.intersection(inner).length for t in hit] or [0]):.1f} mm")
l5 = layers[4]
br = [LineString([(a, b), (c_, d)]) for a, b, c_, d, e in l5['segs'].get('Bridge', [])]
cov = sym.intersection(unary_union([b.buffer(0.21, cap_style=2) for b in br])).area / sym.area if br else 0
print(f"Schicht 5: Vertiefungen zu {cov*100:.0f} % als Brücke")
for g in (sym_only.geoms if hasattr(sym_only, 'geoms') else [sym_only]):
    bb = [b for b in br if b.intersects(g)]
    cx, cy = g.centroid.x, g.centroid.y
    print(f"  Symbol bei Deckel-x {OX - cx:.0f}, y {cy - OY:.0f}: längste Brückenbahn über Luft {max([b.intersection(g).length for b in bb] or [0]):.1f} mm")
seam = []
for l in layers:
    segs = l['segs'].get('Outer wall', [])
    if not segs: continue
    loops, cur_ = [], [segs[0]]
    for s0, s1 in zip(segs, segs[1:]):
        if math.hypot(s1[0] - s0[2], s1[1] - s0[3]) > 0.5: loops.append(cur_); cur_ = []
        cur_.append(s1)
    loops.append(cur_)
    big = max(loops, key=lambda lp: sum(math.hypot(q[2] - q[0], q[3] - q[1]) for q in lp))
    seam.append((round(OX - big[0][0], 1), round(big[0][1] - OY, 1)))
xs_, ys_ = [a for a, b in seam], [b for a, b in seam]
print(f"Naht Außenkontur (Deckelkoordinaten, y 0 = vorne): x {min(xs_)}–{max(xs_)}, y {min(ys_)}–{max(ys_)}")
