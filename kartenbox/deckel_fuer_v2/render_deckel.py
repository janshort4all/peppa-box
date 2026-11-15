"""Ansichten des neuen Deckels an der Basis v2. Aufruf: python3 render_deckel.py"""
import os, sys
import pyvista as pv
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
import render as R
import model_v2 as V
import deckel as D
pv.OFF_SCREEN = True
OUT = os.path.join(HERE, "out")
P = dict(base=V.base(), inlay=V.inlay(), cards=V.cards_stack(V.card_mesh()), pins=V.pin() + V.pin().mirror([1, 0, 0]),
         lid=D.lid(), clip=D.clip(), cpin=D.clip_pin(), ins=D.insert())


def shot(name, ang=0, eye=(330, -360, 260), focus=(0, 0, 55), cards=True, clip_x=None, zoom=1.0):
    pl = pv.Plotter(off_screen=True, window_size=(1500, 1100))
    pl.set_background("#f5f0e8")
    def add(m, col):
        if clip_x is not None:
            m = m ^ V.box(-400, -400, -400, clip_x, 400, 400)
            if m.is_empty():
                return
        pl.add_mesh(R.poly(m), color=col, smooth_shading=True, split_sharp_edges=True, feature_angle=35, specular=0.25, specular_power=12)
    add(P["base"], R.ORANGE); add(P["inlay"], R.BEIGE); add(P["pins"], R.STEEL); add(P["ins"], R.BEIGE)
    add(V.rot_lid(P["lid"], ang), R.ORANGE); add(V.rot_lid(P["clip"], ang), R.BEIGE); add(V.rot_lid(P["cpin"], ang), R.STEEL)
    if cards:
        add(P["cards"], R.CARD)
    pl.enable_lightkit()
    pl.camera_position = [eye, focus, (0, 0, 1)]
    pl.camera.zoom(zoom)
    pl.screenshot(os.path.join(OUT, name))
    pl.close()


VIEWS = {
    "n_iso_zu.png": dict(),
    "n_halb_offen.png": dict(ang=35, eye=(330, -360, 230)),
    "n_offen.png": dict(ang=96, eye=(300, -380, 330), focus=(0, 10, 70)),
    "n_hinten.png": dict(eye=(-300, 380, 220), cards=False),
    "n_verschluss.png": dict(eye=(160, -240, 75), focus=(0, -50, 72), cards=False, zoom=2.4),
    "n_schnitt_verschluss.png": dict(eye=(400, -50, 72), focus=(0, -50, 72), clip_x=0.0, cards=False, zoom=3.0),
    "n_schnitt_seite.png": dict(eye=(600, 0, 70), focus=(0, 0, 70), clip_x=-40.0, zoom=1.5),
}
if __name__ == "__main__":
    for n in (sys.argv[1:] or VIEWS):
        shot(n, **VIEWS[n])
        print("ok", n)
