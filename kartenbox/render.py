"""Ansichten (PNG) der Kartenbox v2. Aufruf: python3 render.py [name ...]"""
import os, sys, math
import numpy as np
import pyvista as pv
import model as M

pv.OFF_SCREEN = True
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
ORANGE, BEIGE, CARD, STEEL = "#e9772b", "#ecdcbf", "#7fa7c9", "#b9b9be"


def poly(m):
    mesh = m.to_mesh()
    v = np.asarray(mesh.vert_properties)[:, :3]
    f = np.asarray(mesh.tri_verts)
    faces = np.hstack([np.full((len(f), 1), 3), f]).ravel()
    return pv.PolyData(v, faces)


_cache = {}


def parts():
    if not _cache:
        card = M.card_mesh()
        _cache.update(base=M.base(), lid=M.lid(), inlay=M.inlay(), cards=M.cards_stack(card),
                      pins=M.pin() + M.pin().mirror([1, 0, 0]))
    return _cache


def shot(name, ang=0.0, eye=(330, -330, 250), focus=(0, 0, 55), cards=True, lid=True, clip_x=None, zoom=1.0, size=(1500, 1100)):
    p = parts()
    pl = pv.Plotter(off_screen=True, window_size=size)
    pl.set_background("#f5f0e8")
    def add(m, col, **kw):
        if clip_x is not None:
            m = m ^ M.box(-400, -400, -400, clip_x, 400, 400)
            if m.is_empty():
                return
        pl.add_mesh(poly(m), color=col, smooth_shading=True, split_sharp_edges=True, feature_angle=35, specular=0.25, specular_power=12, **kw)
    add(p["base"], ORANGE)
    add(p["inlay"], BEIGE)
    add(p["pins"], STEEL)
    if lid:
        add(M.rot_lid(p["lid"], ang), ORANGE)
    if cards:
        add(p["cards"], CARD)
    pl.enable_lightkit()
    pl.camera_position = [eye, focus, (0, 0, 1)]
    pl.camera.zoom(zoom)
    pl.screenshot(os.path.join(OUT, name))
    pl.close()


VIEWS = {
    "v_iso_zu.png": dict(ang=0, eye=(330, -360, 260)),
    "v_iso_offen.png": dict(ang=104, eye=(300, -380, 330), focus=(0, 10, 70)),
    "v_hinten.png": dict(ang=0, eye=(-300, 380, 220), cards=False),
    "v_vorne.png": dict(ang=0, eye=(0, -520, 70), cards=False),
    "v_schnitt_seite.png": dict(ang=0, eye=(600, 0, 60), focus=(0, 0, 60), clip_x=-40.0, zoom=1.6),
    "v_schnitt_offen.png": dict(ang=104, eye=(600, 0, 80), focus=(0, 10, 80), clip_x=-40.0, zoom=1.3),
    "v_oben_offen.png": dict(ang=104, eye=(0, -140, 520), focus=(0, 0, 60)),
}

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    names = sys.argv[1:] or list(VIEWS)
    for n in names:
        shot(n, **VIEWS[n])
        print("ok", n)
