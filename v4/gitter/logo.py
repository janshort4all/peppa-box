import cv2, numpy as np
from manifold3d import CrossSection, FillRule
SRC = __import__("os").path.join(__import__("os").path.dirname(__file__), "peppa_box_logo.jpg")

def logo_cs(width_mm):
    im = cv2.imread(SRC)
    b, g, r = [im[:, :, i].astype(int) for i in range(3)]
    mask = ((r > 190) & (g < 190) & (b < 130) & (r - b > 90)).astype(np.uint8) * 255
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    cnts, hier = cv2.findContours(mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    polys = []
    for c in cnts:
        if cv2.contourArea(c) < 40:
            continue
        c = cv2.approxPolyDP(c, 0.6, True)
        polys.append([(float(p[0][0]), float(-p[0][1])) for p in c])
    cs = CrossSection(polys, FillRule.EvenOdd)
    x0, y0, x1, y1 = cs.bounds()
    s = width_mm / (x1 - x0)
    cs = cs.translate([-(x0 + x1) / 2, -(y0 + y1) / 2]).scale([s, s])
    return cs

if __name__ == "__main__":
    c = logo_cs(100)
    print(c.bounds(), c.area(), c.num_contour())
