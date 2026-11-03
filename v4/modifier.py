"""Modifier-Körper für den Slicer: in diesen Bereichen KEIN Fuzzy Skin (Passungen und Löcher bleiben maßhaltig)."""
import os as _os
ROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))

import trimesh, numpy as np
import model as M
from model import box, cyl_x, cyl_y, U


def ohne_fuzzy():
    """Alle glatten Flächen: genau die vertieften Flächen des Korpus, um FUZZ_RIM erweitert (die Stufe selbst bleibt glatt).
    Dazu der Gitter-Sitz vorne mit Fase und Wänden."""
    e = M.FUZZ_RIM
    sx0, sx1, sz0, sz1 = M.SEAT
    c = M.SEAT_CH + e
    px0, pz0, px1, pz1, pr = M.BACK_PANEL
    parts = {
        "front_gittersitz": M.ext_xz(M.rr(sx0 - c, sz0 - c, sx1 + c, sz1 + c, M.SEAT_R + c), -2, 10),
        "rechts_drehgeber": cyl_x(M.W - 6, M.W + 2, M.ENC_Y, M.ENC_Z, M.ENC_SPOT / 2 + e),
        "rechts_klinke": cyl_x(M.W - 6, M.W + 2, M.JK_Y, M.JK_Z, M.JK_SPOT / 2 + e),
        "hinten_anschlussfeld": M.ext_xz(M.rr(px0 - e, pz0 - e, px1 + e, pz1 + e, pr + e), M.W - 6, M.W + 2),
        "links_riemen": cyl_x(-2, 6, M.STRAP_Y, M.STRAP_Z, 6),
        "hinten_deckelschrauben": U([cyl_y(M.W - 6, M.W + 2, x, M.LS_Z, M.LS_SPOT / 2 + e) for x in M.LS_X]),
    }
    return U(list(parts.values()))


if __name__ == "__main__":
    m = ohne_fuzzy().to_mesh()
    t = trimesh.Trimesh(np.asarray(m.vert_properties)[:, :3], np.asarray(m.tri_verts))
    t.export(_os.path.join(ROOT, "v4/out/01m_modifier_korpus_OHNE_fuzzy.stl"))
    print(t.bounds)
