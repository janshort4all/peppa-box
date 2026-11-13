"""Exportiert Druckdateien, Modifier, Probedruck-Teile, Zusammenbau, STEP und GLB nach kartenbox/out/.

Aufruf: python3 export.py
"""
import os, math, shutil
import numpy as np, trimesh
import cadquery as cq
import model as M
import build as B

OUT = B.OUT
PR = os.path.join(OUT, "druck")
os.makedirs(PR, exist_ok=True)


def flip_lid(m):
    """Deckel kopfüber: Dach auf das Druckbett, Mitte in x/y, z=0 unten."""
    m = m.copy()
    m.apply_transform(trimesh.transformations.rotation_matrix(math.pi, [1, 0, 0]))
    b = m.bounds
    m.apply_translation([-(b[0][0] + b[1][0]) / 2, -(b[0][1] + b[1][1]) / 2, -b[0][2]])
    return m


def to_bed(m):
    m = m.copy()
    b = m.bounds
    m.apply_translation([-(b[0][0] + b[1][0]) / 2, -(b[0][1] + b[1][1]) / 2, -b[0][2]])
    return m


def ring(w_out, d_out, r_out, w_in, d_in, r_in, z0, z1):
    return M.rr(w_out, d_out, r_out, z0, z1).cut(M.rr(w_in, d_in, r_in, z0 - 1, z1 + 1))


def main():
    base_cq, lid_cq, inlay_cq = M.basis(), M.deckel(), M.inlay()
    base, lid, inlay = B.to_mesh(base_cq), B.to_mesh(lid_cq), B.to_mesh(inlay_cq)

    # --- Druckdateien (Orientierung wie gedruckt) ---
    # Basis und Inlay behalten ihre Koordinaten; Deckel kopfüber. Für ElegooSlicer gemeinsam laden NICHT nötig, je Teil ein Auftrag.
    shift_b = -(base.bounds[0] + base.bounds[1]) / 2
    shift_b[2] = -base.bounds[0][2]
    out = {}
    out["01_basis_orange.stl"] = to_bed(base)
    out["02_deckel_orange_kopfueber.stl"] = flip_lid(lid)
    out["03_inlay_beige.stl"] = to_bed(inlay)
    for n, m in out.items():
        m.export(os.path.join(PR, n))
        print(n, m.extents.round(1), "wasserdicht", m.is_watertight)

    # --- Fuzzy-Modifier (nur die Mantelstreifen; gleiche Verschiebung wie das Teil) ---
    # Basis: Streifen von 1,5 mm außerhalb bis 1,0 mm innerhalb der Außenwand, z 3,5…93; Scharnierbereich hinten, Rastzone vorn und Ösen ausgespart
    zf0, zf1 = 3.5, 93.0
    fb = ring(M.W_B + 3.0, M.D_B + 3.0, M.R_OUT + 1.5, M.W_B - 2.0, M.D_B - 2.0, M.R_OUT - 1.0, zf0, zf1)
    fb = fb.cut(M.box(-200, 200, M.D_B - 4.0, M.D_B + 20, -1, 200))                                    # Scharnierzone hinten
    fb = fb.cut(M.box(-(M.TW / 2 + 8), (M.TW / 2 + 8), -20, 6, M.Z_RIM + M.TONGUE_Z0 - 4, 200))        # Rastnut vorn
    fb = fb.cut(M.box(-200, 200, -20, M.D_B + 20, M.Z_RIM - 40, 200) if False else M.box(-200, 200, M.YC - 14, M.YC + 14, M.LUG_Z - 12, M.LUG_Z + 12))  # Ösen
    fbm = B.to_mesh(fb)
    fbm.apply_translation(shift_b)
    fbm.export(os.path.join(PR, "01f_modifier_basis_FUZZY.stl"))
    # Deckel: Wandstreifen oberhalb der Basisfuge bis unter die Dachkante, in Druckausrichtung gespiegelt
    z0, z1 = M.Z_RIM + 1.0, M.Z_RIM + M.LID_TOP - M.ROOF_CH - M.ROOF_R1 - 0.5
    fl = ring(M.W_L + 3.0, M.D_L + 3.0, M.R_L + 1.5, M.W_L - 2.0, M.D_L - 2.0, M.R_L - 1.0, z0, z1)
    fl = fl.cut(M.box(-200, 200, M.D_B - 4.0, M.D_B + 40, -1, 400))
    fl = fl.cut(M.box(-(M.TW / 2 + M.SLIT + 8), (M.TW / 2 + M.SLIT + 8), -30, 8, -1, 400))
    flm = B.to_mesh(fl)
    # gleiche Transformation wie der Deckel: Drehung 180° um x, dann Verschiebung
    Tm = trimesh.transformations.rotation_matrix(math.pi, [1, 0, 0])
    lid_f = lid.copy(); lid_f.apply_transform(Tm)
    b = lid_f.bounds
    sh = [-(b[0][0] + b[1][0]) / 2, -(b[0][1] + b[1][1]) / 2, -b[0][2]]
    flm.apply_transform(Tm); flm.apply_translation(sh)
    flm.export(os.path.join(PR, "02f_modifier_deckel_FUZZY.stl"))

    # --- Zusammenbau (nur Ansicht) ---
    pin = B.to_mesh(M.pin())
    asm = trimesh.util.concatenate([base, lid, inlay, pin])
    asm.export(os.path.join(OUT, "00_zusammenbau_NICHT_DRUCKEN.stl"))
    pin.export(os.path.join(OUT, "04_stahlstift_3x90_ATTRAPPE_NICHT_DRUCKEN.stl"))

    # --- Probedrucke ---
    PC = os.path.join(PR, "probedruck")
    os.makedirs(PC, exist_ok=True)
    keep = {}
    # K1 Scharnier: hinterer Streifen von Basis und Deckel mit Knöcheln, je 3 Bohrungs-Varianten
    for tag, bb, bl in (("A", 2.9, 3.2), ("B", 3.0, 3.35), ("C", 3.1, 3.5)):
        M.BORE_BASE, M.BORE_LID = bb, bl
        bcq, lcq = M.basis(), M.deckel()
        crop = M.box(-60, 60, M.Y_H - 9, M.Y_H + 9, M.Z_RIM - 9, M.Z_RIM + 12)
        bm = B.to_mesh(bcq.intersect(crop))
        lm = B.to_mesh(lcq.intersect(crop))
        to_bed(bm).export(os.path.join(PC, f"K1{tag}_scharnier_basis_bohrung{bb}.stl"))
        to_bed(lm).export(os.path.join(PC, f"K1{tag}_scharnier_deckel_bohrung{bl}.stl"))
    M.BORE_BASE, M.BORE_LID = 3.0, 3.5
    # K2 Rastung: Vorderstreifen mit Nut bzw. Zunge, 3 Vorspannungen
    for pre in (0.05, 0.15, 0.30):
        M.PRELOAD = pre
        bcq, lcq = M.basis(), M.deckel()
        crop = M.box(-30, 30, -12, 12, M.Z_RIM - 36, M.Z_RIM + 6)
        to_bed(B.to_mesh(bcq.intersect(crop))).export(os.path.join(PC, f"K2_rastung_basis_vorspannung{pre}.stl"))
    M.PRELOAD = 0.15
    lcq = M.deckel()
    crop = M.box(-30, 30, -12, 12, M.Z_RIM - 12, M.Z_RIM + M.LID_TOP + 1)
    lcm = B.to_mesh(lcq.intersect(M.box(-30, 30, -12, 12, M.Z_RIM - 36, M.Z_RIM + M.LID_TOP + 1)))
    flip_lid(lcm).export(os.path.join(PC, "K2_rastung_deckel_kopfueber.stl"))
    print("Probedrucke:", sorted(os.listdir(PC)))

    # --- STEP + GLB ---
    base_cq, lid_cq, inlay_cq = M.basis(), M.deckel(), M.inlay()
    asm_cq = cq.Assembly(name="Kartenbox")
    asm_cq.add(base_cq, name="basis", color=cq.Color(0.93, 0.45, 0.10))
    asm_cq.add(lid_cq, name="deckel", color=cq.Color(0.93, 0.45, 0.10))
    asm_cq.add(inlay_cq, name="inlay", color=cq.Color(0.90, 0.82, 0.66))
    asm_cq.add(M.pin(), name="stahlstift", color=cq.Color(0.6, 0.6, 0.65))
    asm_cq.save(os.path.join(OUT, "kartenbox_zusammenbau.step"))
    for n, s in (("basis", base_cq), ("deckel", lid_cq), ("inlay", inlay_cq)):
        cq.exporters.export(s, os.path.join(OUT, f"kartenbox_{n}.step"))
    # GLB mit Farben (Netze)
    sc = trimesh.Scene()
    cols = {"basis": [237, 115, 26, 255], "deckel": [237, 115, 26, 255], "inlay": [230, 209, 168, 255], "stift": [150, 150, 160, 255]}
    for n, m in (("basis", base), ("deckel", lid), ("inlay", inlay), ("stift", pin)):
        mm = m.copy()
        mm.visual.face_colors = cols[n]
        sc.add_geometry(mm, node_name=n)
    sc.export(os.path.join(OUT, "kartenbox.glb"))
    print("STEP/GLB fertig")


if __name__ == "__main__":
    main()
