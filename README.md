# Peppa Box

DIY-Toniebox-Alternative: Eine NFC-Karte mit Cover startet eine Spotify-Playlist. Raspberry Pi 3A+, Akku-Board Waveshare UPS HAT (D), gedrucktes Gehäuse 140 × 140 × 140 mm (PETG, Elegoo Centauri Carbon 2).

- **[STECKBRIEF.md](STECKBRIEF.md)** – alle Entscheidungen, aktueller Stand, offene Punkte, Links. Zuerst lesen.
- `v4/` – parametrisches 3D-Modell (`model.py`), Prüfungen (`check.py`), Export (`build_all.py`), Coupons, Doku-Generator
- `v4/out/` – aktuelle STL-Dateien, Ansichten, PARAMETER.md, PRUEFBERICHT.md, README zum Druck
- `v3/concept3.py` – Software-Renderer für die Ansichten
- `plan/` – Verdrahtungsplan (Generator + HTML) und Einkaufsliste

## Lokal ausführen

Die Skripte erwarten das Repository unter `/home/claude/musikbox` (Pfade sind dort fest eingetragen):

```
git clone https://github.com/janshort4all/peppa-box /home/claude/musikbox
pip install manifold3d trimesh numpy pillow matplotlib opencv-python
cd /home/claude/musikbox/v4 && python3 check.py && python3 build_all.py && python3 docs.py
```
