# Ansagen der Peppa Box – Texte für eigene Aufnahmen

Die Box spricht jeden Satz sofort mit der Sprachausgabe des Pi (pico2wave). Klingt besser: die Sätze wie „Peppa Box bereit – viel Spaß!“ mit ElevenLabs aufnehmen (Stimme „Helmut“) und als WAV in diesen Ordner legen. Eine vorhandene Datei ersetzt die Sprachausgabe ohne Programmänderung.

Aufbereitung wie bei `peppa_box_bereit.wav`: Ende knapp hinter dem letzten Laut abschneiden, 80 ms ausblenden, Spitze −3 dBFS, 150 ms Stille vorne, 44,1 kHz mono, 16 Bit. Am einfachsten die MP3 aus ElevenLabs an Claude schicken.

Probehören: Eltern-Seite → Bedienung → Ansagen anhören, oder `python3 ~/peppa-box/software/toene.py --alle`.

| Datei | Text | wann |
| --- | --- | --- |
| `peppa_box_bereit.wav` | Peppa Box bereit – viel Spaß! | Spotify kennt die Box, einmal je Einschalten |
| `tschuess.wav` | Tschüss, bis bald! | Ein-Taste 2 s gehalten |
| `karte_leer.wav` | Auf dieser Karte ist noch keine Musik. | Karte ohne (Spotify-)Link |
| `karte_auflegen.wav` | Leg eine Karte auf! | derzeit nicht verwendet (abgeschaltet 08.11., Wunsch Jan) |
| `ruhezeit.wav` | Jetzt ist Ruhezeit. Gute Nacht! | Karte/Play in der Ruhezeit „keine Musik“ |
| `moment.wav` | Einen Moment, die Musik kommt gleich. | Karte wartet 8 s auf Musik |
| `kein_internet.wav` | Ich finde gerade kein Internet. Ich versuche es weiter. | Karte wartet 25 s, kein Netz |
| `anmeldung.wav` | Ich bin nicht bei Spotify angemeldet. Bitte frag Mama oder Papa. | Karte wartet 25 s, Spotify-Anmeldung abgelaufen |
| `timer_15.wav` | Schlummer-Timer: Die Musik geht in fünfzehn Minuten aus. | Mond-Feld antippen |
| `timer_30.wav` | Schlummer-Timer: Die Musik geht in dreißig Minuten aus. | Mond-Feld antippen |
| `timer_45.wav` | Schlummer-Timer: Die Musik geht in fünfundvierzig Minuten aus. | Mond-Feld antippen |
| `timer_60.wav` | Schlummer-Timer: Die Musik geht in einer Stunde aus. | Mond-Feld antippen |
| `timer_aus.wav` | Schlummer-Timer aus. | Mond-Feld nach 60 Min |
| `akku_laedt.wav` | Der Akku wird gerade geladen. | Akkustand, Netzteil steckt |
| `akku_voll.wav` | Der Akku ist voll. | Akkustand, Netzteil steckt, voll |
| `akku_schwach.wav` | Mein Akku ist fast leer. Bitte bald aufladen! | einmal bei ca. 15 % |
| `akku_leer.wav` | Mein Akku ist leer. Ich schalte mich jetzt aus. Tschüss! | bei ca. 3,3 V, danach Ausschalten |
| `akku_unbekannt.wav` | Ich kann den Akku gerade nicht messen. | Akku-Chip antwortet nicht |
| `akku_10.wav` | Akku: zehn Prozent. | Akkustand (Mond 5 s halten oder Ein-Taste kurz) |
| `akku_20.wav` | Akku: zwanzig Prozent. | Akkustand (Mond 5 s halten oder Ein-Taste kurz) |
| `akku_30.wav` | Akku: dreißig Prozent. | Akkustand (Mond 5 s halten oder Ein-Taste kurz) |
| `akku_40.wav` | Akku: vierzig Prozent. | Akkustand (Mond 5 s halten oder Ein-Taste kurz) |
| `akku_50.wav` | Akku: fünfzig Prozent. | Akkustand (Mond 5 s halten oder Ein-Taste kurz) |
| `akku_60.wav` | Akku: sechzig Prozent. | Akkustand (Mond 5 s halten oder Ein-Taste kurz) |
| `akku_70.wav` | Akku: siebzig Prozent. | Akkustand (Mond 5 s halten oder Ein-Taste kurz) |
| `akku_80.wav` | Akku: achtzig Prozent. | Akkustand (Mond 5 s halten oder Ein-Taste kurz) |
| `akku_90.wav` | Akku: neunzig Prozent. | Akkustand (Mond 5 s halten oder Ein-Taste kurz) |
| `akku_100.wav` | Akku: hundert Prozent. | Akkustand (Mond 5 s halten oder Ein-Taste kurz) |
