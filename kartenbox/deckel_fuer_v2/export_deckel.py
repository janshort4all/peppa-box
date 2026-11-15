"""Druckdateien, Probedrucke, Zusammenbau und 3D-Ansicht für den neuen Deckel zur gedruckten Basis v2.
Aufruf: python3 export_deckel.py"""
import os, sys, base64
import numpy as np
import trimesh
from manifold3d import Manifold

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
import export as EX          # Hilfsfunktionen (STL prüfen, 3MF, GLB) aus kartenbox/export.py
import model_v2 as V
import deckel as D

OUT = os.path.join(HERE, "out")
DR = os.path.join(OUT, "druck")
PR = os.path.join(DR, "probedruck")
for d in (OUT, DR, PR):
    os.makedirs(d, exist_ok=True)
EX.COL.update({"einsatz": (236, 220, 191)})
ADD = V.manifold3d_op("add")


def main():
    lid, ins, clip_f = D.lid(), D.insert(), D.clip_free()[0]
    files = []
    tf = D.orient_tf("deckel", lid)
    files += [EX.stl(tf(lid), os.path.join(DR, "02n_deckel_orange_kopfueber.stl")),
              EX.stl(tf(D.fuzzy_modifier()), os.path.join(DR, "02nf_modifier_deckel_FUZZY.stl"), None)]
    files.append(EX.stl(D.orient("einsatz", ins), os.path.join(DR, "06_rasteinsatz_beige_auf_der_vorderseite.stl")))
    files.append(EX.stl(D.orient("lasche", clip_f), os.path.join(DR, "05n_klemmlasche_beige_auf_der_seite.stl")))
    p = D.orient("stift", D.clip_pin())
    files.append(EX.stl(Manifold.batch_boolean([p.translate([0, k * 10, 0]) for k in (0, 1)], ADD), os.path.join(DR, "04n_laschenstifte_2_beige.stl"), 2))

    # Probedrucke direkt an der gedruckten Basis
    yf = D.Y_PIN - 8
    kl = lid ^ V.box(-D.CHEEK_X1 - 10, yf, D.Z_S - 1, D.CHEEK_X1 + 10, -V.D_O / 2 + 10, D.Z_CPIN + 14)
    kl = EX.foot(kl, D.Z_CPIN + 14, top=True)
    files.append(EX.stl(D.orient("deckel", kl), os.path.join(PR, "N1a_lasche_deckelstueck_kopfueber.stl")))
    t0 = D.CL_T
    for t in (1.4, 1.6, 1.8):
        D.CL_T = t
        files.append(EX.stl(D.orient("lasche", D.clip_free()[0]), os.path.join(PR, f"N1b_lasche_feder_{t:.1f}.stl")))
    D.CL_T = t0
    files.append(EX.stl(D.orient("einsatz", ins), os.path.join(PR, "N1c_rasteinsatz.stl")))
    files.append(EX.stl(Manifold.batch_boolean([D.orient("stift", D.clip_pin(d)).translate([0, k * 10, 0]) for k, d in enumerate((3.9, 4.0, 4.1))], ADD),
                        os.path.join(PR, "N1d_laschenstifte_3.9_4.0_4.1.stl"), 3))
    # Ecke vorn rechts mit Stülprand (Passung an der Basis, mit Fuzzy-Modifier)
    cut = V.box(70, -200, D.Z_S - 1, 300, 10.7, V.P + 8)
    kc = lid ^ cut
    kc = EX.foot(kc, V.P + 8, top=True)
    tfc = D.orient_tf("deckel", kc)
    files.append(EX.stl(tfc(kc), os.path.join(PR, "N2_ecke_stuelprand_kopfueber.stl")))
    files.append(EX.stl(tfc(D.fuzzy_modifier() ^ cut), os.path.join(PR, "N2_ecke_stuelprand_MODIFIER_FUZZY.stl"), None))

    # Zusammenbau
    cards = V.cards_stack(V.card_mesh())
    pins2 = V.pin() + V.pin().mirror([1, 0, 0])
    asm = [("basis", V.base()), ("deckel", lid), ("inlay", V.inlay()), ("stift", pins2), ("lasche", D.clip() + D.clip_pin()), ("einsatz", ins)]
    EX.write_3mf(asm + [("karten", cards)], os.path.join(OUT, "deckel_neu_zusammenbau.3mf"))
    EX.write_glb(asm + [("karten", cards)], os.path.join(OUT, "deckel_neu.glb"))
    glb = EX._scene(asm + [("karten", cards)], simplify=0.02).export(file_type="glb")
    html = open(os.path.join(HERE, "..", "viewer_template.html"), encoding="utf-8").read()
    html = html.replace("const names=['basis','deckel','inlay','stift','lasche','karten'];", "const names=['basis','deckel','inlay','stift','lasche','einsatz','karten'];")
    rep = {"@GLB@": base64.b64encode(glb).decode(), "@YH@": f"{V.Y_H:.3f}", "@ZH@": f"{V.Z_H:.3f}", "@STOP@": "96", "@CLIPX@": "-40",
           "@H@": f"{V.H:.1f}", "@MASS@": f"{2 * D.HX_L + 2 * V.BX:.0f} × {2 * D.HY_L + 2 * V.BY:.0f} × {V.H:.0f} mm"}
    for k, v in rep.items():
        html = html.replace(k, v)
    html = html.replace("<title>Peppa Box Kartenbox 3D</title>", "<title>Peppa Box Kartenbox – neuer Deckel für Basis v2</title>")
    open(os.path.join(OUT, "viewer.html"), "w", encoding="utf-8").write(html)
    for f in files:
        print(os.path.relpath(f, HERE))


if __name__ == "__main__":
    main()
