"""Bild: Play-Knopf, was hinter der beigen Sichtfläche liegt – echter G-Code (Aufruf mit Pfad) gegen das erwartete Ergebnis mit 02m/02r (Schema)."""
import sys, math, numpy as np, matplotlib
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from shapely.geometry import Polygon, LineString, MultiLineString, Point
from shapely.ops import unary_union
from shapely import make_valid
import model as M, gcode_deckel_pruefung as G
L = G.lesen(sys.argv[1]); OX, OY = 198.0, 56.5
def shp(cs):
    g = None
    for q in cs.to_polygons():
        q = np.asarray(q)
        if len(q) < 3: continue
        q = make_valid(Polygon(q)); g = q if g is None else g.symmetric_difference(q)
    return g
holes = shp(M.pad_symbols())
px, py, d = M.PADS['play']
from shapely.geometry import box as sbox
view = sbox(px - 16.5, py - 16.5, px + 16.5, py + 16.5)
def hatch(region, ang, sp=0.42):
    a = math.radians(ang); dvec = np.array([math.cos(a), math.sin(a)]); n = np.array([-dvec[1], dvec[0]])
    c = np.array([px, py]); out = []
    for t in np.arange(-25, 25, sp):
        ln = LineString([c + n * t - dvec * 30, c + n * t + dvec * 30]).intersection(region)
        for g in getattr(ln, 'geoms', [ln]):
            if g.length > 0.05: out.append(list(g.coords))
    return out
def rings(geom):
    out = []
    for g in getattr(geom, 'geoms', [geom]):
        if g.geom_type != 'Polygon': continue
        out.append(list(g.exterior.coords)); out += [list(h.coords) for h in g.interiors]
    return out
BEIGE, BEIGE_D, OR, OR_L, RED = '#cdb27e', '#a8895a', '#ff7f0e', '#ffc58a', '#c0392b'
fig, axs = plt.subplots(2, 2, figsize=(12, 12.4), dpi=110)
def real(ax, i, colmap):
    l = L[i]
    for typ, c in colmap.items():
        segs = [((OX - a, b - OY), (OX - cc, dd - OY)) for t_, tool, a, b, cc, dd in l['segs'] if t_ == typ]
        if segs: ax.add_collection(LineCollection(segs, colors=c, linewidths=1.6))
real(axs[0, 0], 2, {'Outer wall': RED, 'Inner wall': RED, 'Internal solid infill': BEIGE, 'Gap infill': '#27ae60'})
real(axs[1, 0], 4, {'Bridge': OR, 'Internal solid infill': OR_L, 'Outer wall': OR_L, 'Inner wall': OR_L, 'Gap infill': OR_L})
# nachher Schicht 3: eine Wand um jedes Loch, Rest gerade Bahnen
beige = view.difference(holes)
ax = axs[0, 1]
ax.add_collection(LineCollection(rings(holes.buffer(0.21)), colors=RED, linewidths=1.6))
ax.add_collection(LineCollection(hatch(beige.buffer(-0.42), 135), colors=BEIGE, linewidths=1.6))
# nachher Schicht 5: Brücke nur Symbole + 0,4 mm, fest 45° (Bett) = 135° im Deckel; Rest dichte Füllung
ax = axs[1, 1]
br = holes.buffer(0.4)
ax.add_collection(LineCollection(hatch(br.intersection(view), 135, 0.42 / 1.1), colors=OR, linewidths=1.4))
ax.add_collection(LineCollection(hatch(view.difference(br).buffer(-0.05), 45), colors=OR_L, linewidths=1.6))
tit = {(0, 0): 'VORHER Schicht 3 (beige, hinter der Sichtfläche):\n3 Wandringe um jedes Loch + Lückenfüllung',
       (0, 1): 'NACHHER Schicht 3 (Modifizierer 02m, Arachne):\n1 Wand, sonst gerade Bahnen wie überall',
       (1, 0): 'VORHER Schicht 5 (erste orange, direkt hinter dem Beige):\nBrücke mit Lücken über den GANZEN Kreis',
       (1, 1): 'NACHHER Schicht 5 (Modifizierer 02r):\nBrücke nur über den Symbolen (+0,4 mm), alle 45°;\nim restlichen Kreis dichte Füllung wie außen'}
for (r, c), t in tit.items():
    a = axs[r, c]
    for h in rings(holes): a.plot(*np.array(h).T, color='#555', lw=0.5, ls=':')
    a.set_xlim(px - 16.5, px + 16.5); a.set_ylim(py - 16.5, py + 16.5); a.set_aspect('equal'); a.set_xticks([]); a.set_yticks([])
    a.set_title(t, fontsize=10.5)
fig.suptitle('Play-Knopf von oben: was hinter der beigen Sichtfläche liegt (links echter G-Code vom 05.11., rechts erwartet nach der Änderung)', fontsize=11)
fig.savefig(__import__('os').path.join(__import__('os').path.dirname(__import__('os').path.abspath(__file__)), 'out', 'deckel_vorher_nachher.png'), bbox_inches='tight'); print('ok')
