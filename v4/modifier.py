"""Modifier-Körper für den Slicer: in diesen Bereichen KEIN Fuzzy Skin (Passungen und Löcher bleiben maßhaltig)."""
import trimesh, numpy as np
import model as M
from model import box, cyl_x, cyl_y, U


def ohne_fuzzy():
    sx0, sx1, sz0, sz1 = M.SEAT
    ux, uz = M.usb_panel()
    r = M.USB_PANEL["loch"] / 2 + 5
    parts = {
        "front_stoffrahmen": box(sx0 + 0.2, -2, sz0 + 0.2, sx1 - 0.2, 10, sz1 - 0.2),
        "rechts_drehgeber": cyl_x(M.W - 6, M.W + 2, M.ENC_Y, M.ENC_Z, 12),
        "rechts_klinke": cyl_x(M.W - 6, M.W + 2, M.JK_Y, M.JK_Z, 9),
        "hinten_usbc": cyl_y(M.W - 6, M.W + 2, ux, uz, r),
        "links_riemen": cyl_x(-2, 6, M.STRAP_Y, M.STRAP_Z, 6),
        "hinten_deckelschrauben": U([cyl_y(M.W - 6, M.W + 2, x, M.LS_Z, 6) for x in M.LS_X]),
    }
    return U(list(parts.values()))


if __name__ == "__main__":
    m = ohne_fuzzy().to_mesh()
    t = trimesh.Trimesh(np.asarray(m.vert_properties)[:, :3], np.asarray(m.tri_verts))
    t.export("/home/claude/musikbox/v4/out/01m_modifier_korpus_OHNE_fuzzy.stl")
    print(t.bounds)
