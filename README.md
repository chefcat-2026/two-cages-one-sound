# two-cages-one-sound

Website zum Buch (GitHub Pages). Spiele: `game.html` (Camden Clicker), `camden-walk.html` (Camden Walk), `camden-command.html` (Camden Command, 3D-Echtzeitstrategie mit Three.js, acht Missionen entlang der Kapitel).

Figuren für Camden Command: `tools/figures.py` baut sie in Blender (auch headless mit `pip install bpy`: `python3 tools/figures.py -- img`) und schreibt `img/models.json`, die das Spiel lädt.

`lib/` enthält Three.js 0.152.2 (MIT) als ES-Modul samt den genutzten Zusatzmodulen (Nachbearbeitung, Umgebungslicht, Himmel). Das Spiel lädt sie per Import-Map.

Straßenset: `tools/bake_textures.py` backt die PBR-Materialien nach `img/tex/`, `tools/camden_set.py` baut Reihenhäuser und Straßenmöbel und exportiert `img/set/camden.json` (glTF mit eingebettetem Puffer). Beide laufen headless mit `pip install bpy`.

Eigene Figuren: GLB ins Repo legen, mit `python3 tools/glb2json.py Datei.glb img/set/name.json` umwandeln; das Spiel lädt `img/set/john.json` und `img/set/theo.json` als Heldenmodelle (Kopf nach +Z, Maße in Metern, Skalierung im Lader).
