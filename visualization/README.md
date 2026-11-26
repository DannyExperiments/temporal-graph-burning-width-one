# One contact per round

The example uses two elements, three relays, two set vertices, a hub, one private leaf and twelve late leaves. S1 = {a, b} is chosen. Gold marks the active edge and any vertex newly reached by spread. Orange marks the ignition made after spread. Teal marks vertices already burning.

The legal strategy has 14 ignitions. All 21 vertices are burning at round 14. Round 15 is the permitted final spread and has no contact. The first late leaf contact is at round 16. The timeline extends through round 27 so the viewer can inspect every late edge. Each contact is the only appearance of its edge, and every occupied time is distinct.

Extract the ZIP and open `index.html`. Use the slider or buttons to inspect each timestep. No connection is required.

Rebuild the web fixture, ZIP and 704 × 850 GIF from the repository root with Python 3.11+ and Pillow 13.0. The renderer uses Arial if available, then Pillow’s bundled font.

```sh
python3 visualization/render.py
```

The renderer computes the shared fixture from the standard-library replay. It writes 17 frames over 15.48 seconds at the reference settings.
