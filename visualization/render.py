"""Generate the shared schedule fixture, phone GIF, and offline explorer ZIP."""

import argparse
import json
from pathlib import Path
import re
import runpy
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
W, H = 704, 850
BG, PANEL, INK = "#0a1624", "#13263c", "#f4f5f4"
QUIET, LINE = "#a9bed0", "#516a80"
CYAN, GOLD, ORANGE = "#70e1cb", "#ffe198", "#ffae78"
POINTS = {
    "S1": (115, 93), "S2": (115, 233),
    "R1a": (352, 87), "R1b": (352, 159), "R2b": (352, 231),
    "a": (588, 94), "b": (588, 187), "C": (215, 251), "P": (488, 251),
    **{f"T{n+1}": (85 + (n % 6)*107, 381 + (n//6)*62) for n in range(12)},
}


def inputs():
    replay = runpy.run_path(str(HERE.parent / "verification/src/replay.py"))
    instance, rounds = replay["worked_example"]()
    assert set(POINTS) == set(instance.names)
    for t in range(instance.h + 2, max(instance.contacts) + 1):
        rounds.append({
            "time": t, "phase": "After deadline", "edge": [instance.names[i] for i in instance.contacts[t]],
            "new": [], "ignition": None, "burned": rounds[-1]["burned"],
        })
    assert len(rounds) == 28 and len({tuple(sorted(row["edge"])) for row in rounds if row["edge"]}) == 24
    return rounds


def fonts():
    def open_font(bold, size):
        try:
            return ImageFont.truetype("Arial Bold.ttf" if bold else "Arial.ttf", size)
        except OSError:
            return ImageFont.load_default(size=size)
    return {k: open_font(bold, size) for k, bold, size in (
        ("title", True, 49), ("label", True, 28), ("header", True, 30),
        ("body", False, 29), ("small", False, 24), ("hint", True, 25),
    )}


def render(row, font):
    im = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(im)

    def text(x, y, content, key, fill=INK, anchor="lt"):
        assert draw.textlength(content, font=font[key]) <= W - 64, content
        draw.text((x, y), content, fill=fill, font=font[key], anchor=anchor)

    text(32, 24, "TEMPORAL GRAPH BURNING", "hint", QUIET)
    text(32, 62, "One contact per round", "title")
    text(32, 123, "S1 = {a, b}    S2 = {b}    Budget: one set", "body", QUIET)
    text(32, 176, f"ROUND {row['time']:02d}   ·   {row['phase'].upper()}", "header", GOLD)
    draw.rounded_rectangle((24, 214, 680, 695), radius=18, fill=PANEL)
    offset = 218
    text(115, offset+23, "Sets", "label", QUIET, "mm")
    text(352, offset+23, "Relays", "label", QUIET, "mm")
    text(588, offset+23, "Elements", "label", QUIET, "mm")
    text(352, offset+334, "Late leaves", "label", QUIET, "mm")
    if row["edge"]:
        start, end = [POINTS[node] for node in row["edge"]]
        if row["time"] <= 15:
            draw.line((start[0], start[1]+offset, end[0], end[1]+offset), fill=GOLD, width=7)
        else:
            for step in range(0, 14, 2):
                pair = [(x+(u-x)*s/14, y+(v-y)*s/14+offset) for s in (step, step+1)
                        for (x, y), (u, v) in ((start, end),)]
                draw.line(pair, fill=GOLD, width=5)
    burning = set(row["burned"])
    for name, (x, y) in POINTS.items():
        y += offset
        late = name.startswith("T")
        color = ORANGE if name == row["ignition"] else GOLD if name in row["new"] else CYAN if name in burning else LINE
        if late:
            draw.rounded_rectangle((x-33,y-24,x+33,y+24), radius=8, fill=color)
        else:
            draw.ellipse((x-33,y-33,x+33,y+33), fill=color)
        text(x, y, name, "label" if not late else "hint", BG if name in burning else INK, "mm")

    if row["time"] > 15:
        top, bottom = "First late contact is after the deadline.", "Each late leaf needed its own ignition."
    else:
        edge = " — ".join(row["edge"]) if row["edge"] else "none"
        top = f"Active contact  {edge}"
        bottom = f"Then ignite {row['ignition']}." if row["ignition"] else "No ignition this round."
        if row["new"]:
            top += f"   ·   lights {row['new'][0]}"
        if row["time"] == 15:
            bottom = "All 21 vertices are already burning."
    text(32, 713, top, "body", GOLD)
    text(32, 759, bottom, "body", ORANGE if row["ignition"] else INK)
    text(32, 809, "One timestamp per edge   ·   Width 1", "small", QUIET)
    return im


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=HERE)
    output = parser.parse_args().output
    output.mkdir(parents=True, exist_ok=True)
    rounds = inputs()
    source_html = (HERE / "index.html").read_text()
    fixture = json.dumps({"rounds": rounds, "points": POINTS}, separators=(",", ":"))
    embed = re.compile(r'(<script type="application/json" id="schedule">).*?(</script>)', re.S)
    page, count = embed.subn(lambda match: match[1] + fixture + match[2], source_html)
    assert count == 1
    (output / "index.html").write_text(page)
    entry = ZipInfo("index.html", date_time=(2026, 11, 27, 0, 0, 0))
    entry.create_system, entry.external_attr = 3, 0o100644 << 16
    with ZipFile(output / "burning-schedule-explorer.zip", "w") as archive:
        archive.writestr(entry, page.encode(), compress_type=ZIP_DEFLATED, compresslevel=9)

    font = fonts()
    frames = [render(row, font) for row in rounds[:17]]
    palette = frames[3].quantize(colors=64, dither=Image.Dither.NONE)
    frames = [frame.quantize(palette=palette, dither=Image.Dither.NONE) for frame in frames]
    durations = [1000, 900, 1100] + [730]*11 + [1200, 1450, 1800]
    assert len(frames) == len(durations)
    frames[0].save(output / "burning-schedule.gif", save_all=True, append_images=frames[1:],
                   duration=durations, loop=0, disposal=1, optimize=True)
    print(f"Exact schedule embedded. {len(frames)} frames at {W} × {H} over {sum(durations)/1000:g} seconds.")


if __name__ == "__main__":
    main()
