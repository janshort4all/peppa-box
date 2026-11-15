"""Erzeugt alle Dateien der Kartenbox v3 (Stülpdeckel, Klemmlasche) in out/:
  druck/      STL in Druckausrichtung (+ Fuzzy-Modifier in gleicher Lage)
  druck/probedruck/  Coupons K1 (Scharnier), K2 (Klemmlasche), K3 (Stülpdeckel/Hals, Ecke)
  kartenbox_zusammenbau.3mf   farbiger Zusammenbau (ElegooSlicer, Windows 3D-Viewer)
  kartenbox.glb               farbiger Zusammenbau (jeder 3D-Viewer, Handy)
  viewer.html                 3D-Ansicht mit Deckelregler (wird als Artefakt veröffentlicht)
Aufruf: python3 export.py"""
import base64, io, json, math, os, zipfile
import numpy as np
import trimesh
from manifold3d import Manifold
import model as M

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
DR = os.path.join(OUT, "druck")
PR = os.path.join(DR, "probedruck")
for d in (OUT, DR, PR):
    os.makedirs(d, exist_ok=True)

COL = {"basis": (233, 119, 43), "deckel": (233, 119, 43), "inlay": (236, 220, 191), "stift": (236, 220, 191), "lasche": (236, 220, 191), "karten": (127, 167, 201)}


def tm(m):
    mesh = m.to_mesh()
    return trimesh.Trimesh(np.asarray(mesh.vert_properties)[:, :3].astype(np.float64), np.asarray(mesh.tri_verts), process=False)


def stl(m, path, bodies=1):
    """STL schreiben; entartete Dreiecke (Fläche 0) vorher entfernen, Ergebnis muss wasserdicht und ein Körper sein."""
    raw = tm(m.simplify(1e-3))                     # Splitterdreiecke zusammenfassen (Volumen unverändert, siehe Prüfung)
    t = trimesh.Trimesh(raw.vertices, raw.faces, process=True)
    t2 = t.copy()
    t2.update_faces(t2.area_faces > 1e-9)
    t2.remove_unreferenced_vertices()
    if t2.is_watertight:                           # entartete Dreiecke nur entfernen, wenn das Netz dicht bleibt
        t = t2
    t.export(path)
    back = trimesh.load(path)
    parts = back.split(only_watertight=False)
    assert back.is_watertight and (bodies is None or len(parts) == bodies) and abs(back.volume - m.volume()) < 0.002 * m.volume() + 0.5, (path, back.is_watertight, len(parts))
    return path


def foot(m, z_cut, top=False, h=1.6):
    """Standplatte unter dem Schnitt eines Coupons (damit dünne Wandstücke sicher stehen)."""
    b = m.bounding_box()
    if top:
        return m + M.box(b[0], b[1], z_cut - 0.01, b[3], b[4], z_cut + h)
    return m + M.box(b[0], b[1], z_cut - h, b[3], b[4], z_cut + 0.01)


def main():
    base, lid, inl = M.base(), M.lid(), M.inlay()
    fz_b, fz_l = M.fuzzy_modifier("basis"), M.fuzzy_modifier("deckel")
    files = []

    # ---------------------------------------------------------------- Hauptteile
    tf = M.orient_tf("basis", base)
    files += [stl(tf(base), os.path.join(DR, "01_basis_orange.stl")),
              stl(tf(fz_b), os.path.join(DR, "01f_modifier_basis_FUZZY.stl"), None)]
    tf = M.orient_tf("deckel", lid)
    files += [stl(tf(lid), os.path.join(DR, "02_deckel_orange_kopfueber.stl")),
              stl(tf(fz_l), os.path.join(DR, "02f_modifier_deckel_FUZZY.stl"), None)]
    files.append(stl(M.orient("inlay", inl), os.path.join(DR, "03_inlay_beige.stl")))
    cf = M.clip_free()[0]
    files.append(stl(M.orient_tf("lasche", cf)(cf), os.path.join(DR, "05_klemmlasche_beige_auf_der_seite.stl")))
    p = M.orient("stift", M.pin())
    pc = M.orient("stift", M.clip_pin())
    pins = Manifold.batch_boolean([p.translate([0, k * 10, 0]) for k in (-1, 0, 1)] + [pc.translate([0, k * 10, 0]) for k in (2, 3)], M.manifold3d_op("add"))
    files.append(stl(pins, os.path.join(DR, "04_stifte_beige_3_scharnier_2_lasche.stl"), 5))

    # ---------------------------------------------------------------- Probedrucke
    # K1 Scharnier rechts: Basisstück + Deckelstück + 3 Stifte Ø 3,9 / 4,0 / 4,1
    xa, xb = M.PX - M.POD / 2 - 3, M.PX + M.POD / 2 + 3
    yb = M.Y_BACK_PX - 14
    kb = base ^ M.box(xa, yb, M.Z_H - 22, xb, M.Y_H + 15, M.P + 1)
    kb = foot(kb, M.Z_H - 22)
    kl = lid ^ M.box(xa, yb, M.Z_H - 8, xb, M.Y_H + 15, M.Z_H + 24)
    kl = foot(kl, M.Z_H + 24, top=True)
    files.append(stl(M.orient("basis_k", kb), os.path.join(PR, "K1a_scharnier_basis.stl")))
    files.append(stl(M.orient("deckel", kl), os.path.join(PR, "K1b_scharnier_deckel_kopfueber.stl")))
    tp = [M.orient("stift", M.pin(d)).translate([0, k * 10, 0]) for k, d in enumerate((3.9, 4.0, 4.1))]
    files.append(stl(Manifold.batch_boolean(tp, M.manifold3d_op("add")), os.path.join(PR, "K1c_stifte_3.9_4.0_4.1.stl"), 3))
    # K2 Klemmlasche: Basis-Vorderstück mit Stufe, Hals und Nut; Deckel-Vorderstück mit Lagerböcken; Laschen mit Federdicke 1,8 / 2,0 / 2,2
    yf = M.Y_OUT_F - 3
    xw = M.CHEEK_X1 + 8
    kb = base ^ M.box(-xw, yf, M.Z_GRIP - 6, xw, -M.D_O / 2 + 12, M.P + 1)
    kb = foot(kb, M.Z_GRIP - 6)
    kl = lid ^ M.box(-xw, yf - 12, M.Z_L - 2, xw, -M.D_O / 2 + 12, M.Z_CPIN + 12)
    kl = foot(kl, M.Z_CPIN + 12, top=True)
    files.append(stl(M.orient("basis_k", kb), os.path.join(PR, "K2a_lasche_basis.stl")))
    files.append(stl(M.orient("deckel", kl), os.path.join(PR, "K2b_lasche_deckel_kopfueber.stl")))
    t0 = M.CL_T
    for t in (1.6, 1.8, 2.0):
        M.CL_T = t
        cf = M.clip_free()[0]
        files.append(stl(M.orient_tf("lasche", cf)(cf), os.path.join(PR, f"K2c_lasche_feder_{t:.1f}.stl")))
    M.CL_T = t0
    files.append(stl(Manifold.batch_boolean([M.orient("stift", M.clip_pin(d)).translate([0, k * 10, 0]) for k, d in enumerate((3.9, 4.0, 4.1))], M.manifold3d_op("add")),
                     os.path.join(PR, "K2d_laschenstifte_3.9_4.0_4.1.stl"), 3))
    # K3 Passung: rechtes Ende (x > 90), Basis/Inlay/Deckel um die Teilungsebene, mit Fuzzy-Modifier
    cut = M.box(90, -200, -1, 300, 200, 300)
    kb = base ^ cut ^ M.box(-300, -200, M.Z_L - 8, 300, 200, M.P + 1)
    ki = inl ^ cut ^ M.box(-300, -200, M.Z_L - 8, 300, 200, M.P + 6)
    kl = lid ^ cut ^ M.box(-300, -200, M.Z_L - 1, 300, 200, M.P + 10)
    tfb, tfl = M.orient_tf("basis_k", kb), M.orient_tf("deckel", kl)
    files.append(stl(tfb(kb), os.path.join(PR, "K3a_passung_basis.stl")))
    files.append(stl(tfb(fz_b ^ cut ^ M.box(-300, -200, M.Z_L - 8, 300, 200, M.P + 1)), os.path.join(PR, "K3a_passung_basis_MODIFIER_FUZZY.stl"), None))
    files.append(stl(M.orient("inlay", ki), os.path.join(PR, "K3b_passung_inlay.stl")))
    files.append(stl(tfl(kl), os.path.join(PR, "K3c_passung_deckel_kopfueber.stl")))
    files.append(stl(tfl(fz_l ^ cut ^ M.box(-300, -200, M.Z_L - 1, 300, 200, M.P + 10)), os.path.join(PR, "K3c_passung_deckel_MODIFIER_FUZZY.stl"), None))

    # ---------------------------------------------------------------- Zusammenbau (Einbaulage)
    card = M.card_mesh()
    cards = M.cards_stack(card)
    pins2 = M.pin() + M.pin().mirror([1, 0, 0])
    asm = [("basis", base), ("deckel", lid), ("inlay", inl), ("stift", pins2), ("lasche", M.clip() + M.clip_pin())]
    write_3mf(asm + [("karten", cards)], os.path.join(OUT, "kartenbox_zusammenbau.3mf"))
    write_glb(asm + [("karten", cards)], os.path.join(OUT, "kartenbox.glb"))
    write_viewer(asm, cards)
    for f in files:
        print(os.path.relpath(f, HERE))


def write_3mf(parts, path):
    """3MF mit Farben je Objekt (Basismaterialien)."""
    res, items = [], []
    mats = "".join(f'<base name="{n}" displaycolor="#{r:02X}{g:02X}{b:02X}FF"/>' for n, (r, g, b) in ((n, COL[n]) for n, _ in parts))
    for i, (n, m) in enumerate(parts):
        t = tm(m)
        v = "".join(f'<vertex x="{x:.4f}" y="{y:.4f}" z="{z:.4f}"/>' for x, y, z in t.vertices)
        f = "".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in t.faces)
        res.append(f'<object id="{i + 2}" name="{n}" type="model" pid="1" pindex="{i}"><mesh><vertices>{v}</vertices><triangles>{f}</triangles></mesh></object>')
        items.append(f'<item objectid="{i + 2}"/>')
    model = ('<?xml version="1.0" encoding="UTF-8"?>'
             '<model unit="millimeter" xml:lang="de-DE" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">'
             f'<metadata name="Title">Peppa Box Kartenbox v3</metadata><resources><basematerials id="1">{mats}</basematerials>'
             + "".join(res) + '</resources><build>' + "".join(items) + '</build></model>')
    ct = ('<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
          '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
          '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
    rels = ('<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", ct)
        z.writestr("_rels/.rels", rels)
        z.writestr("3D/3dmodel.model", model)


def _scene(parts, simplify=None):
    sc = trimesh.Scene()
    for n, m in parts:
        if simplify:
            m = m.simplify(simplify)
        t = tm(m)
        r, g, b = COL[n]
        t.visual = trimesh.visual.TextureVisuals(material=trimesh.visual.material.PBRMaterial(
            name=n, baseColorFactor=[r / 255, g / 255, b / 255, 1.0], metallicFactor=0.0, roughnessFactor=0.6))
        # Koordinaten für glTF: y nach oben (z -> y, y -> -z)
        t.apply_transform(np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, -1, 0, 0], [0, 0, 0, 1]], dtype=float))
        sc.add_geometry(t, node_name=n, geom_name=n)
    return sc


def write_glb(parts, path):
    _scene(parts).export(path)


def write_viewer(asm, cards):
    glb = _scene(asm + [("karten", cards)], simplify=0.02).export(file_type="glb")
    html = open(os.path.join(HERE, "viewer_template.html"), encoding="utf-8").read()
    rep = {"@GLB@": base64.b64encode(glb).decode(), "@YH@": f"{M.Y_H:.3f}", "@ZH@": f"{M.Z_H:.3f}",
           "@STOP@": "95", "@CLIPX@": "-40", "@H@": f"{M.H:.1f}",
           "@MASS@": f"{M.W_O + 2 * (M.BX + M.S_N):.0f} × {M.D_O + 2 * (M.BY + M.S_N):.0f} × {M.H:.0f} mm"}
    for k, v in rep.items():
        html = html.replace(k, v)
    open(os.path.join(OUT, "viewer.html"), "w", encoding="utf-8").write(html)
    print("viewer.html", round(len(html) / 1e6, 2), "MB")


if __name__ == "__main__":
    main()
