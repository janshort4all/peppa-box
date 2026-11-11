"""Schnelle Ansichten (PNG) der Kartenbox mit pyvista, Deckel wahlweise geöffnet."""
import os, sys, numpy as np, trimesh, pyvista as pv
import model as M
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
pv.OFF_SCREEN = True

def load(n): return trimesh.load(os.path.join(OUT, f"_use_{n}.stl"))

def rot_lid(m, ang):
    """Deckel um die Scharnierachse (y=Y_H, z=Z_H, Achse x) öffnen: Vorderkante nach oben/hinten."""
    m = m.copy()
    a = np.radians(ang)
    T = np.eye(4)
    c, s = np.cos(a), np.sin(a)
    # (y,z) rel. -> (y c + z s, -y s + z c)
    T[1,1]=c; T[1,2]=s; T[2,1]=-s; T[2,2]=c
    T[1,3] = M.Y_H - (c*M.Y_H + s*M.Z_H)
    T[2,3] = M.Z_H - (-s*M.Y_H + c*M.Z_H)
    m.apply_transform(T)
    return m

def cards(n_per=(10,10,10)):
    bs=[]
    for k,n in enumerate(n_per):
        xc0 = -M.LINER_X/2 + M.DIV + k*(M.SLOT_W+M.DIV)
        for i in range(n):
            x0 = xc0 + i*M.CARD_T + 0.5
            b = trimesh.creation.box(extents=(M.CARD_T-0.1, M.CARD_W, M.CARD_H))
            b.apply_translation((x0+M.CARD_T/2, M.YC, M.CARD_Z0+M.CARD_H/2))
            bs.append(b)
    return trimesh.util.concatenate(bs)

def to_pv(m): return pv.wrap(m)

def shot(name, lid_ang=0, with_cards=True, cam="iso", size=(1400,1000), cutaway=False):
    pl = pv.Plotter(off_screen=True, window_size=size)
    pl.set_background("#f4efe6")
    basis, lid, inlay = load("basis"), load("deckel"), load("inlay")
    pl.add_mesh(to_pv(basis), color="#e8742a", smooth_shading=True, split_sharp_edges=True, specular=0.2)
    pl.add_mesh(to_pv(inlay), color="#eadbc0", smooth_shading=True, split_sharp_edges=True)
    pl.add_mesh(to_pv(rot_lid(lid, lid_ang)), color="#e8742a", smooth_shading=True, split_sharp_edges=True, specular=0.2)
    if with_cards:
        pl.add_mesh(to_pv(cards()), color="#8fb8de", smooth_shading=False)
    cx, cy, cz = 0, M.D_B/2, 62
    views = {
      "iso": ((330, -300, 260)), "iso_back": ((-300, 380, 260)), "front": ((0, -520, 110)),
      "top": ((0, M.D_B/2, 560)), "side": ((560, M.D_B/2, 80)), "back": ((0, 560, 110)),
    }
    eye = views[cam]
    pl.camera_position = [eye, (cx, cy, cz), (0,0,1) if cam!="top" else (0,1,0)]
    pl.camera.zoom(1.15)
    pl.screenshot(os.path.join(OUT, name))
    pl.close()

if __name__ == "__main__":
    shot("v_iso_zu.png", 0, True, "iso")
    shot("v_iso_offen.png", 100, True, "iso")
    shot("v_hinten_zu.png", 0, False, "iso_back")
    shot("v_oben_offen.png", 100, True, "top")
