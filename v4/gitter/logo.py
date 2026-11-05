"""Peppa-Box-Logo (Vorlage Jan, Stand 05.11.2026) als Kontur.

Vorlage: peppa_box_logo.png, orange Schrift auf Creme. Gemessen wird „wie orange“ ein Pixel ist (Rot minus Blau:
Creme ca. 20, Orange ca. 205). Schwelle in der Mitte (113), leicht geglättet gegen die Papierstruktur, 4-fach
hochgerechnet für eine Kante mit Viertelpixel-Genauigkeit. Ergebnis: 11 Teile (5 Buchstaben oben, 3 Strahlen,
B, O mit Play-Dreieck, X), Innenformen (Punzen) als Löcher.
"""
import os
import cv2
import numpy as np
from manifold3d import CrossSection, FillRule

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "peppa_box_logo.png")
THR, SIGMA, UP, EPS = 113.0, 1.0, 4, 0.6     # Schwelle, Glättung (px), Hochrechnung, Vereinfachung (px hochgerechnet)


def logo_mask():
    im = cv2.imread(SRC)
    b, r = im[:, :, 0].astype(np.float32), im[:, :, 2].astype(np.float32)
    d = cv2.GaussianBlur(r - b, (0, 0), SIGMA)
    return d


def logo_polys():
    d = logo_mask()
    h, w = d.shape
    du = cv2.resize(d, (w * UP, h * UP), interpolation=cv2.INTER_CUBIC)
    m = (du > THR).astype(np.uint8) * 255
    cnts, _ = cv2.findContours(m, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    polys = []
    for c in cnts:
        if cv2.contourArea(c) < 30 * UP * UP:
            continue
        c = cv2.approxPolyDP(c, EPS, True)
        polys.append([((p[0][0] + 0.5) / UP - 0.5, -((p[0][1] + 0.5) / UP - 0.5)) for p in c])
    return polys


def logo_cs(width_mm):
    """Logo als Querschnitt, Mitte (Umriss) im Ursprung, Breite width_mm, y nach oben."""
    cs = CrossSection(logo_polys(), FillRule.EvenOdd)
    x0, y0, x1, y1 = cs.bounds()
    s = width_mm / (x1 - x0)
    return cs.translate([-(x0 + x1) / 2, -(y0 + y1) / 2]).scale([s, s])


def px_per_mm(width_mm):
    cs = CrossSection(logo_polys(), FillRule.EvenOdd)
    x0, _, x1, _ = cs.bounds()
    return (x1 - x0) / width_mm


if __name__ == "__main__":
    c = logo_cs(100)
    print([round(v, 2) for v in c.bounds()], round(c.area(), 1), "mm²", len(c.decompose()), "Teile")
