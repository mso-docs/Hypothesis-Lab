"""Packaged, offline video assets for the in-app help document."""

import base64
from functools import lru_cache
from pathlib import Path
from hypothesis_lab.tutorial import CHAPTERS, DURATION, HYPOTHESIS, PUBLICATION

MEDIA = Path(__file__).parent / "frontend" / "media"


@lru_cache(maxsize=1)
def walkthrough_bundle() -> dict:
    def data_url(name: str, mime: str) -> str:
        path = MEDIA / name
        return (
            f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode()
            if path.is_file()
            else ""
        )

    return {
        "title": "From research question to reproducible report",
        "format": "Captioned illustrated walkthrough · no audio required",
        "duration": DURATION,
        "chapters": CHAPTERS,
        "hypothesis": HYPOTHESIS,
        "source": PUBLICATION,
        "video_src": data_url("getting-started.mp4", "video/mp4"),
        "poster_src": data_url("getting-started-poster.jpg", "image/jpeg"),
        "captions_src": data_url("getting-started.vtt", "text/vtt"),
        "chapters_src": data_url("getting-started-chapters.vtt", "text/vtt"),
    }
