"""Erzeugt STL (Druckausrichtung), Zusammenbau, STEP/GLB und Ansichten der Kartenbox."""
import os, sys
import numpy as np, trimesh
import cadquery as cq
import model as M

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
os.makedirs(OUT, exist_ok=True)
TOL = 0.01


def to_mesh(shape, tol=TOL, ang=0.1):
    """Netz über den OCC-STL-Export (gemeinsame Kantendiskretisierung → wasserdicht)."""
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "x.stl")
        cq.exporters.export(shape, p, "STL", tolerance=tol, angularTolerance=ang)
        m = trimesh.load(p, process=True)
    m.merge_vertices()
    return m


def save(mesh, name):
    p = os.path.join(OUT, name)
    mesh.export(p)
    return p


if __name__ == "__main__":
    parts = {"basis": M.basis(), "deckel": M.deckel(), "inlay": M.inlay()}
    meshes = {k: to_mesh(v) for k, v in parts.items()}
    for k, m in meshes.items():
        print(k, "wasserdicht", m.is_watertight, "Tris", len(m.faces), "Vol cm3", round(m.volume / 1000, 1))
    for k, m in meshes.items():
        m.export(os.path.join(OUT, f"_use_{k}.stl"))
