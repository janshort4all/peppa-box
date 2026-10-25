#!/usr/bin/env python3
"""Einmalige Anmeldung bei Spotify. Start: python3 ~/peppa-box/software/spotify_login.py"""
import spotify

spotify.login_interaktiv()
print("\nGefundene Spotify-Geraete:")
for d in spotify.geraete():
    print(f"  - {d['name']} ({d['type']})" + ("  [aktiv]" if d.get("is_active") else ""))
print("\nFehlt 'Peppa Box' in der Liste: einmal in der Spotify-App unter 'Geraete' die Peppa Box auswaehlen.")
