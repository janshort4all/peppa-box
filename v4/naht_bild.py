"""Bild für Jan: wo die Naht aufgemalt wird (Rückansicht, rote Linie auf der hinteren linken Rundung)."""
import os
import numpy as np, trimesh, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
t = trimesh.load(os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "01_korpus_beige.stl"))
W, R = 140.0, 16.0
c = t.triangles_center
def d_out(x, y):
    h = W/2 - R; qx, qy = np.abs(x-W/2)-h, np.abs(y-W/2)-h
    return np.hypot(np.maximum(qx,0), np.maximum(qy,0)) + np.minimum(np.maximum(qx,qy),0) - R
d = d_out(c[:,0], c[:,1])
keep = (d > -1.2) & (c[:,1] > 60)            # nur Außenhaut, hintere Hälfte
tri = t.triangles[keep]; n = t.face_normals[keep]
light = np.array([0.35, 0.9, 0.45]); light /= np.linalg.norm(light)
shade = 0.45 + 0.55*np.clip(n @ light, 0, 1)
base = np.array([0.91, 0.85, 0.74])
cols = np.clip(base[None,:]*shade[:,None], 0, 1)
fig = plt.figure(figsize=(9, 7.2), dpi=110)
ax = fig.add_subplot(111, projection="3d", proj_type="ortho")
pc = Poly3DCollection(tri, facecolors=cols, edgecolors=cols, linewidths=0.4); ax.add_collection3d(pc)
a = np.radians(120); cx, cy = R, W-R
px, py = cx + (R+0.4)*np.cos(a), cy + (R+0.4)*np.sin(a)
ax.plot([px, px], [py, py], [0.2, 135.8], color="#e00000", lw=3.5, zorder=10)
ax.set_xlim(0, 140); ax.set_ylim(0, 140); ax.set_zlim(0, 136)
ax.set_box_aspect((140, 140, 136)); ax.view_init(elev=4, azim=90); ax.axis("off")
fig.text(0.5, 0.90, "So siehst du die Box in der Ansicht „Hinten“", ha="center", fontsize=14)
fig.text(0.80, 0.50, "hier malen:\nauf der Rundung,\nvon ganz unten\nbis ganz oben", ha="left", va="center", fontsize=12, color="#c00000")
ax.text(38, 150, 40, "Lüftungsschlitze", ha="center", fontsize=10, color="#555")
ax.text(112, 150, 40, "USB-C", ha="center", fontsize=10, color="#555")
fig.text(0.5, 0.10, "Rote Linie = Naht. Sie liegt auf der Rundung rechts neben den Lüftungsschlitzen,\nungefähr in der Mitte zwischen dem Ende des glatten Feldes und der Außenkante.", ha="center", fontsize=11)
fig.savefig(os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "naht_aufmalen.png"), bbox_inches="tight")
print("ok")
