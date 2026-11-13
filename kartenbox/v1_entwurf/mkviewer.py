"""Erzeugt out/viewer.html (three.js, GLB eingebettet) aus out/kartenbox.glb."""
import base64, model as M
glb = base64.b64encode(open('out/kartenbox.glb', 'rb').read()).decode()
html = open('viewer_template.html').read()
for k, v in {"@YH@": M.Y_H, "@ZH@": M.Z_H, "@LX@": M.LINER_X, "@GLB@": glb}.items():
    html = html.replace(k, str(v))
open('out/viewer.html', 'w').write(html)
print(len(html))
