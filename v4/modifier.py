"""Modifier für den Slicer.

NEU (04.11.2026): `01f_modifier_korpus_FUZZY_aussenhaut.stl` – eine 1 mm dünne Haut nur an den Außenflächen.
Im Slicer: Prozess Fuzzy Skin „Nur lackiert“ (ohne Bemalung = kein Fuzzy; „Deaktiviert“ wirkt gleich, blendet aber die Werte aus), dieser Modifier Fuzzy Skin „Kontur“.
Der Slicer verfuzzt dann nur Wandstücke, die in dieser Haut liegen. Die Innenseite liegt 2–3 mm tiefer und
bekommt nie Fuzzy – auch nicht in den Schichten, in denen Löcher den Wandring aufschneiden (Ursache der Bänder
innen und der Linien außen beim Druck vom 04.11.).

ALT (bis 03.11.): `01m_…OHNE_fuzzy` (Objekt „Kontur“, Modifier „keine“). Nicht mehr verwenden.
`ohne_fuzzy()` bleibt als Geometrie der glatten Flächen erhalten (wird aus der Haut ausgespart).
"""
import os as _os
ROOT = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))

import trimesh, numpy as np
import model as M
from model import box, cyl_x, cyl_y, U, slab
from manifold3d import JoinType


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
        "links_riemen": cyl_x(-2, 6, M.STRAP_Y, M.STRAP_Z, M.STRAP_HOLE / 2 + 0.6),   # nur die Bohrung, Rand liegt unter dem Riemen
        "hinten_deckelschrauben": U([cyl_y(M.W - 6, M.W + 2, x, M.LS_Z, M.LS_SPOT / 2 + e) for x in M.LS_X]),
    }
    return U(list(parts.values()))


def aussenhaut():
    """Fuzzy-Bereich: Ring von 1,5 mm vor der Außenfläche bis FUZZ_SHELL hinein, zwischen den Fasen unten und oben,
    ohne die glatten Flächen (ohne_fuzzy)."""
    z0, z1 = M.FUZZ_Z
    ring = M.OUT.offset(1.5, JoinType.Round) - M.OUT.offset(-M.FUZZ_SHELL, JoinType.Round)
    ring = ring.simplify(0.001)                      # doppelte Punkte aus dem Offset entfernen (sonst STL nicht dicht)
    return slab(ring, z0, z1) - ohne_fuzzy()


def boden_aussenhaut():
    """Fuzzy am Boden-Rand (06.11.2026), passend zum Korpus: nur der senkrechte Streifen zwischen der Fase unten
    (Standkante, BASE_CHAMF) und der Fase oben (V-Fuge, EDGE_V). Beide Fasen bleiben glatt wie am Korpus."""
    ring = M.OUT.offset(1.5, JoinType.Round) - M.OUT.offset(-M.FUZZ_SHELL, JoinType.Round)
    ring = ring.simplify(0.001)
    return slab(ring, M.BASE_CHAMF, M.BASE_T - M.EDGE_V)


def _export(m, name, shift):
    mm = m.translate(shift).to_mesh()
    t = trimesh.Trimesh(np.asarray(mm.vert_properties)[:, :3], np.asarray(mm.tri_verts))
    t.export(_os.path.join(ROOT, "v4/out", name))
    return t


if __name__ == "__main__":
    # gleich verschieben wie 01_korpus_beige.stl (Druckausrichtung, Ecke auf 0) → im Slicer deckungsgleich
    import check as K
    bb = K.orient("korpus", M.korpus()).bounding_box()
    kb = M.korpus().bounding_box()
    shift = [bb[0] - kb[0], bb[1] - kb[1], bb[2] - kb[2]]
    t = _export(aussenhaut(), "01f_modifier_korpus_FUZZY_aussenhaut.stl", shift)
    print("01f Außenhaut", t.bounds.round(2).tolist(), "wasserdicht", t.is_watertight)
    bb = K.orient("boden", M.boden()).bounding_box()
    kb = M.boden().bounding_box()
    shift = [bb[0] - kb[0], bb[1] - kb[1], bb[2] - kb[2]]
    t = _export(boden_aussenhaut(), "05f_modifier_boden_FUZZY_rand.stl", shift)
    print("05f Boden-Rand", t.bounds.round(2).tolist(), "wasserdicht", t.is_watertight)
    alt = _os.path.join(ROOT, "v4/out/01m_modifier_korpus_OHNE_fuzzy.stl")
    if _os.path.exists(alt):
        _os.remove(alt)
        print("alter Modifier 01m entfernt")
