"""Gegenprüfung der Druckdateien mit einer zweiten, unabhängigen Methode: Schichtweise schneiden wie ein Slicer
(0,2 mm), dann je Schicht
  - freie Flächen: was in Schicht n nicht auf Schicht n-1 (um 0,2 mm = 45° erweitert) steht → Überhang/Brücke/Insel
  - zu schmale Stellen: was beim Ab- und Wiederaufweiten um 0,21 mm verschwindet (schmaler als 0,42 mm Linienbreite)
Liest die fertigen STL aus out/druck (nicht das Modell) und hängt das Ergebnis an out/PRUEFBERICHT.md an."""
import glob, os
import numpy as np
import trimesh
from manifold3d import Manifold, Mesh, CrossSection, JoinType

HERE = os.path.dirname(os.path.abspath(__file__))
LAYER = 0.2
LW = 0.42


def load(path):
    t = trimesh.load(path)
    return Manifold(Mesh(vert_properties=np.asarray(t.vertices, dtype=np.float32), tri_verts=np.asarray(t.faces, dtype=np.uint32)))


def analyse(path):
    m = load(path)
    b = m.bounding_box()
    zs = np.arange(LAYER / 2, b[5], LAYER)
    prev = None
    free, thin = [], []
    for z in zs:
        cs = m.slice(z)
        if prev is not None:
            sup = prev.offset(LAYER, JoinType.Round)
            f = cs - sup
            a = f.area()
            if a > 0.5:
                bb = f.bounds()
                free.append((z, a, bb))
        op = cs.offset(-LW / 2, JoinType.Round).offset(LW / 2, JoinType.Round)
        a = (cs - op).area()
        if a > 2.0:
            thin.append((z, a))
        prev = cs
    return free, thin, len(zs)


def group(rows, key=lambda r: r[0], gap=0.5):
    out = []
    for r in rows:
        if out and key(r) - key(out[-1][-1]) <= gap:
            out[-1].append(r)
        else:
            out.append([r])
    return out


def main():
    lines = ["", "## 10. Gegenprüfung (zweite Methode: Schichten wie im Slicer, 0,2 mm, aus den fertigen STL)",
             "Freie Fläche = Teil einer Schicht, der nicht auf der Schicht darunter (um 0,2 mm = 45° erweitert) steht. "
             "Schmal = Stellen unter 0,42 mm Linienbreite."]
    for path in sorted(glob.glob(os.path.join(HERE, "out", "druck", "**", "*.stl"), recursive=True)):
        name = os.path.relpath(path, os.path.join(HERE, "out", "druck"))
        if "MODIFIER" in name or "modifier" in name:
            continue
        free, thin, n = analyse(path)
        tot = sum(a for _, a, _ in free)
        lines.append(f"- **{name}** ({n} Schichten): frei {tot:.0f} mm² in {len(free)} Schichten; schmal {sum(a for _, a in thin):.0f} mm² in {len(thin)} Schichten")
        for g in group(free):
            a = sum(r[1] for r in g)
            if a < 5:
                continue
            x0 = min(r[2][0] for r in g); y0 = min(r[2][1] for r in g); x1 = max(r[2][2] for r in g); y1 = max(r[2][3] for r in g)
            lines.append(f"    z {g[0][0]:.1f}–{g[-1][0]:.1f}: {a:.0f} mm² (x {x0:.0f}…{x1:.0f}, y {y0:.0f}…{y1:.0f})")
        for g in group(thin, gap=0.5):
            a = sum(r[1] for r in g)
            if a < 10:
                continue
            lines.append(f"    schmal z {g[0][0]:.1f}–{g[-1][0]:.1f}: {a:.0f} mm²")
    txt = "\n".join(lines) + "\n"
    print(txt)
    rep = os.path.join(HERE, "out", "PRUEFBERICHT.md")
    body = open(rep, encoding="utf-8").read().split("\n## 10.")[0].rstrip("\n") + "\n"
    open(rep, "w", encoding="utf-8").write(body + txt)


if __name__ == "__main__":
    main()
