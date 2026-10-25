#!/usr/bin/env python3
"""Zeigt die Spotify-Geraete, die die Web API gerade sieht. Start: python3 ~/peppa-box/software/geraete.py"""
import spotify

liste = spotify.geraete()
if not liste:
    print("Keine Geraete gefunden.")
for d in liste:
    print(f"  - {d['name']} ({d['type']})" + ("  [aktiv]" if d.get("is_active") else ""))
