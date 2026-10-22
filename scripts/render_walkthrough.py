"""Render the captioned illustrated guide (not a live screen recording).

Build tools: Pillow plus GStreamer (x264enc/mp4mux), or imageio-ffmpeg.
Fallback install: `uv pip install --python .venv/bin/python pillow imageio-ffmpeg`
Run from the repository root: `.venv/bin/python scripts/render_walkthrough.py`.
The script uses only bundled public tutorial content and synthetic observations.
"""

from pathlib import Path
import math
import subprocess
import shutil
import os
from functools import lru_cache

from PIL import Image, ImageDraw, ImageFont
from scipy.stats import beta
import numpy as np

from hypothesis_lab.tutorial import (
    CHAPTERS,
    DURATION,
    HYPOTHESIS,
    PUBLICATION,
    captions_vtt,
    chapters_vtt,
)

OUT = Path("src/hypothesis_lab/ui/frontend/media")
OUT.mkdir(parents=True, exist_ok=True)
W, H, FPS = 1280, 720, 12
BG, NAV, EDITOR, RAISED = "#141419", "#1c1c22", "#202027", "#292931"
LINE, INK, MUTED, ACCENT, TEAL = "#373742", "#e6e3ee", "#a6a1b4", "#b49bf7", "#70c7b2"
FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")
GRID = np.linspace(0.001, 0.999, 240)
DENSITIES = {(a, b): beta.pdf(GRID, a, b) for a, b in [(1, 1), (35, 17)]}


@lru_cache(maxsize=32)
def font(size=16, bold=False, mono=False):
    name = "DejaVuSansMono" if mono else "DejaVuSans"
    return ImageFont.truetype(
        str(FONT_DIR / (name + ("-Bold" if bold else "") + ".ttf")), size
    )


def text(
    draw, xy, value, size=16, color=INK, bold=False, mono=False, width=None, spacing=6
):
    face = font(size, bold, mono)
    lines = []
    for paragraph in str(value).split("\n"):
        if width:
            row = ""
            for word in paragraph.split():
                candidate = (row + " " + word).strip()
                if draw.textlength(candidate, font=face) > width and row:
                    lines.append(row)
                    row = word
                else:
                    row = candidate
            lines.append(row)
        else:
            lines.append(paragraph)
    draw.multiline_text(xy, "\n".join(lines), font=face, fill=color, spacing=spacing)
    return len(lines) * (size + spacing)


def box(draw, bounds, fill=EDITOR, outline=LINE, radius=5, width=1):
    draw.rounded_rectangle(bounds, radius, fill=fill, outline=outline, width=width)


def input_box(draw, x, y, label, value, width=190, accent=False):
    text(draw, (x, y), label, 11, MUTED)
    box(draw, (x, y + 20, x + width, y + 55), BG, ACCENT if accent else LINE)
    text(draw, (x + 10, y + 28), value, 14, INK, mono=True, width=width - 18)


def cursor(draw, xy, phase):
    x, y = xy
    pulse = 14 + 3 * math.sin(phase * math.pi * 2)
    draw.ellipse((x - pulse, y - pulse, x + pulse, y + pulse), outline=ACCENT, width=2)
    draw.polygon(
        [(x, y), (x + 3, y + 23), (x + 10, y + 16), (x + 18, y + 15)],
        fill=INK,
        outline=BG,
        width=1,
    )


def shell(draw, active, title="Radish germination", has_data=False):
    box(draw, (232, 126, 1254, 576), NAV)
    draw.line((232, 158, 1254, 158), fill=LINE)
    text(draw, (248, 135), "HYPOTHESIS LAB", 11, ACCENT, bold=True)
    text(draw, (806, 135), "Search files & actions", 11, MUTED)
    box(draw, (1165, 131, 1237, 153), RAISED)
    text(draw, (1183, 136), "Save", 10)
    draw.line((410, 158, 410, 576), fill=LINE)
    draw.line((1035, 158, 1035, 576), fill=LINE)
    text(draw, (249, 178), "EXPLORER", 10, MUTED, bold=True)
    text(draw, (249, 204), title, 12, bold=True, width=145)
    rows = [
        ("hypothesis.md", "question"),
        ("literature", "sources"),
        ("evidence.json", "evidence"),
        ("analysis.py", "analysis"),
        ("research-notes.md", "notes"),
        ("report.md", "report"),
    ]
    for i, (label, key) in enumerate(rows):
        y = 251 + i * 32
        if key == active:
            box(draw, (241, y - 5, 401, y + 23), "#2d263f", None, 3)
        text(draw, (251, y), label, 11, ACCENT if key == active else MUTED, mono=True)
    draw.line((247, 470, 395, 470), fill=LINE)
    text(draw, (251, 487), "+ New investigation", 11, INK)
    text(draw, (251, 519), "Watch getting started", 10, ACCENT)
    text(
        draw,
        (430, 170),
        {
            "question": "hypothesis.md",
            "sources": "literature",
            "evidence": "evidence.json",
            "analysis": "analysis.py",
            "notes": "research-notes.md",
            "report": "report.md",
        }[active],
        11,
        ACCENT,
        mono=True,
    )
    draw.line((410, 198, 1035, 198), fill=LINE)
    text(draw, (1052, 177), "ANALYSIS SUMMARY", 10, MUTED, bold=True)
    text(draw, (1052, 220), "Starting assumption", 11, MUTED)
    text(draw, (1052, 248), "Little previous knowledge", 13, ACCENT, width=178)
    text(draw, (1052, 296), "Uniform · Beta(1, 1)", 11, MUTED)
    draw.line((1052, 328, 1235, 328), fill=LINE)
    text(draw, (1052, 351), "Current observations", 11, MUTED)
    text(
        draw,
        (1052, 378),
        "34 events / 50 trials" if has_data else "Not available yet",
        13,
        INK,
        width=180,
    )
    text(
        draw,
        (1052, 411),
        "Synthetic teaching data" if has_data else "Literature review only",
        10,
        TEAL if has_data else MUTED,
    )
    draw.line((1052, 441, 1235, 441), fill=LINE)
    text(draw, (1052, 460), "Updated estimate", 11, MUTED)
    text(draw, (1052, 485), "67.3%" if has_data else "Pending", 25, ACCENT, bold=True)
    text(
        draw,
        (1052, 530),
        "95% CI 54.1–79.2%" if has_data else "No posterior to provide",
        11,
        MUTED,
    )


def draw_frame(t):
    index = next(
        (i for i, c in enumerate(CHAPTERS) if c["start"] <= t < c["end"]),
        len(CHAPTERS) - 1,
    )
    chapter = CHAPTERS[index]
    progress = (t - chapter["start"]) / (chapter["end"] - chapter["start"])
    image = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(image)
    text(d, (28, 23), "Hypothesis Lab", 20, INK, bold=True)
    text(d, (1006, 27), "ILLUSTRATED WALKTHROUGH", 10, MUTED)
    d.line((24, 60, 1255, 60), fill=LINE)
    text(d, (249, 78), chapter["title"], 25, bold=True)
    text(d, (29, 90), "GETTING STARTED", 10, ACCENT, bold=True)
    for i, c in enumerate(CHAPTERS):
        y = 137 + i * 53
        if i == index:
            box(d, (20, y - 8, 214, y + 39), "#282134", None, 4)
        color = ACCENT if i == index else TEAL if i < index else MUTED
        d.ellipse((30, y, 50, y + 20), outline=color, width=1)
        text(d, (36, y + 2), str(i + 1), 10, color)
        text(d, (60, y), c["title"], 11, color, width=145, spacing=3)
    text(d, (28, 605), "02:02 · captions included", 10, MUTED)
    text(d, (28, 628), "No audio required", 10, MUTED)
    shell(d, chapter["page"], has_data=index >= 5)
    if index == 0:
        text(d, (446, 230), "Your first investigation", 27, bold=True)
        text(
            d,
            (446, 282),
            "From a testable question to a traceable research report.",
            18,
            MUTED,
            width=535,
        )
        for j, label in enumerate(
            ["Define", "Find papers", "Review", "Model", "Export"]
        ):
            x = 449 + j * 111
            d.ellipse((x, 367, x + 28, 395), outline=ACCENT, width=1)
            text(d, (x + 10, 373), str(j + 1), 11, ACCENT)
            text(d, (x - 4, 413), label, 11, MUTED)
        text(d, (446, 492), "Example: seed germination", 17, TEAL)
        text(
            d,
            (446, 529),
            "A real paper + synthetic observations; the app calculates the result",
            12,
            MUTED,
        )
    elif index == 1:
        box(d, (502, 229, 965, 505), RAISED, ACCENT)
        text(d, (527, 253), "New investigation", 24, bold=True)
        text(
            d, (527, 300), "Start with an empty question and source library.", 12, MUTED
        )
        value = "Radish germination"[
            : int(min(1, progress * 2.7) * len("Radish germination"))
        ]
        input_box(d, 527, 341, "Investigation name", value, 410, True)
        box(d, (527, 429, 746, 467), ACCENT, ACCENT)
        text(d, (545, 439), "Create investigation", 13, BG, bold=True)
        cursor(d, (688, 447), progress)
    elif index == 2:
        text(d, (436, 222), "Scientific hypothesis", 20, bold=True)
        box(d, (435, 266, 1012, 374), BG, ACCENT)
        typed = HYPOTHESIS[: int(min(1, progress * 2) * len(HYPOTHESIS))]
        text(d, (451, 282), typed, 17, INK, width=542)
        text(d, (436, 408), "Operational definition", 13, TEAL, bold=True)
        text(
            d,
            (436, 443),
            "Germinated = visible radicle by day seven.",
            17,
            INK,
            width=545,
        )
        text(d, (436, 495), "Keep conditions and sampling rules explicit.", 13, MUTED)
        cursor(d, (912, 344), progress)
    elif index == 3:
        text(d, (435, 220), "Attach a real source", 20, bold=True)
        input_box(
            d, 435, 261, "Add a DOI or research URL", PUBLICATION["doi"], 575, True
        )
        text(d, (436, 348), PUBLICATION["title"], 17, INK, width=567)
        text(d, (436, 430), "Shimizu & Kumakura · 2011 · OpenAlex", 12, MUTED)
        text(d, (436, 468), "Open original source ↗", 14, ACCENT)
        text(
            d,
            (436, 511),
            "Different experimental conditions: context, not direct validation.",
            12,
            TEAL,
            width=560,
        )
        cursor(d, (601, 474), progress)
    elif index == 4:
        text(d, (435, 220), "Review a verbatim excerpt", 20, bold=True)
        box(d, (435, 266, 1012, 383), BG)
        excerpt = PUBLICATION["abstract"].split(". ")[0] + "."
        text(d, (450, 281), excerpt, 14, INK, width=545)
        text(d, (435, 414), "Relationship to this hypothesis", 11, MUTED)
        box(d, (435, 438, 702, 473), BG, ACCENT)
        text(d, (450, 447), "Inconclusive", 14, ACCENT)
        text(d, (435, 504), "An annotation is not a numerical likelihood.", 14, TEAL)
        cursor(d, (659, 456), progress)
    elif index == 5:
        text(d, (435, 216), "Guided analysis setup", 21, bold=True)
        text(d, (435, 254), "1  What event are you measuring?", 13, INK, bold=True)
        text(d, (455, 282), "Visible radicle within seven days", 13, MUTED)
        text(d, (435, 321), "2  Do you have observations?", 13, INK, bold=True)
        box(d, (455, 347, 1008, 388), BG, ACCENT)
        text(
            d,
            (469, 359),
            "● I have event counts     34 events / 50 observations",
            12,
            INK,
        )
        text(d, (435, 421), "3  What do you already know?", 13, INK, bold=True)
        box(d, (455, 447, 1008, 492), "#2d263f", ACCENT)
        text(d, (469, 462), "● Little previous knowledge", 14, ACCENT)
        text(
            d, (435, 524), "Updated estimate calculated automatically: 67.3%", 14, TEAL
        )
        cursor(d, (896, 470), progress)
    elif index == 6:
        text(d, (435, 220), "Research notes", 20, bold=True)
        box(d, (435, 266, 1012, 541), BG, ACCENT)
        rows = [
            "# Methods & limitations",
            "",
            "- Visible radicle within seven days",
            "- Fixed conditions and sampling frame",
            "- 34 / 50 synthetic observations",
            "- Independent trials assumed",
            "",
            "The interval crosses 60%.",
            "Mean alone does not confirm the claim.",
        ]
        for j, row in enumerate(rows):
            text(
                d, (450, 281 + j * 26), row, 13, TEAL if j in [0, 7] else INK, mono=True
            )
        cursor(d, (959, 503), progress)
    else:
        text(d, (435, 220), "Investigation report", 23, bold=True)
        text(d, (435, 263), "Radish germination", 15, MUTED)
        for j, label in enumerate(
            [
                "Hypothesis & event definition",
                "Source metadata & review annotations",
                "Prior, observations & posterior",
                "Notes, assumptions & limitations",
            ]
        ):
            text(d, (445, 309 + j * 36), "✓", 16, TEAL)
            text(d, (474, 310 + j * 36), label, 14, INK)
        box(d, (435, 479, 674, 523), ACCENT, ACCENT)
        text(d, (450, 493), "Download Markdown", 14, BG, bold=True)
        box(d, (692, 479, 1009, 523), RAISED)
        text(d, (710, 493), "Download JSON", 14, INK)
        cursor(d, (626, 506), progress)
    box(d, (232, 594, 1254, 681), "#211c2c", None)
    text(d, (251, 610), chapter["caption"], 16, INK, width=981, spacing=6)
    d.rectangle((24, 701, 1255, 705), fill=LINE)
    d.rectangle((24, 701, 24 + 1231 * t / DURATION, 705), fill=ACCENT)
    return image


if __name__ == "__main__":
    staged_video = OUT / "getting-started.render.mp4"
    gst_available = (
        shutil.which("gst-launch-1.0")
        and shutil.which("gst-inspect-1.0")
        and all(
            subprocess.run(
                ["gst-inspect-1.0", plugin],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                env={**os.environ, "GST_REGISTRY": "/tmp/hypothesis-gst.bin"},
            ).returncode
            == 0
            for plugin in ("rawvideoparse", "videoconvert", "x264enc", "mp4mux")
        )
    )
    if gst_available:
        command = [
            "gst-launch-1.0",
            "-q",
            "fdsrc",
            "fd=0",
            "!",
            "rawvideoparse",
            "format=rgb",
            f"width={W}",
            f"height={H}",
            f"framerate={FPS}/1",
            "!",
            "videoconvert",
            "!",
            "video/x-raw,format=I420",
            "!",
            "x264enc",
            "speed-preset=veryfast",
            "pass=qual",
            "quantizer=23",
            "key-int-max=48",
            "!",
            "video/x-h264,stream-format=avc,alignment=au",
            "!",
            "mp4mux",
            "faststart=true",
            "!",
            "filesink",
            f"location={staged_video}",
        ]
    else:
        import imageio_ffmpeg

        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        command = [
            ffmpeg,
            "-y",
            "-f",
            "rawvideo",
            "-vcodec",
            "rawvideo",
            "-pix_fmt",
            "rgb24",
            "-s",
            f"{W}x{H}",
            "-r",
            str(FPS),
            "-i",
            "-",
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "23",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(staged_video),
        ]
    with (OUT / "render.log").open("w") as log:
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=log,
            stderr=log,
            env={**os.environ, "GST_REGISTRY": "/tmp/hypothesis-gst.bin"},
        )
        try:
            for frame in range(DURATION * FPS):
                image = draw_frame(frame / FPS)
                process.stdin.write(image.tobytes())
                if frame % (20 * FPS) == 0:
                    print(f"Rendered {frame // FPS}/{DURATION}s", flush=True)
            process.stdin.close()
            if process.wait():
                raise RuntimeError("Video encoding failed; inspect media/render.log")
        except BaseException:
            process.kill()
            raise
    staged_video.replace(OUT / "getting-started.mp4")
    draw_frame(6).save(OUT / "getting-started-poster.jpg", quality=90)
    for i, c in enumerate(CHAPTERS):
        draw_frame(c["start"] + (c["end"] - c["start"]) * 0.7).save(
            Path("/tmp") / f"hl-walkthrough-{i + 1}.jpg", quality=88
        )
    (OUT / "getting-started.vtt").write_text(captions_vtt())
    (OUT / "getting-started-chapters.vtt").write_text(chapters_vtt())
    (OUT / "render.log").unlink(missing_ok=True)
    print(f"Created {OUT / 'getting-started.mp4'} ({DURATION}s)")
