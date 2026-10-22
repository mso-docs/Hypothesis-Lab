"""The instructional example must be reproducible and safe to practice offline."""

import asyncio
from hypothesis_lab import persistence, services
from hypothesis_lab.tutorial import (
    CHAPTERS,
    DURATION,
    practice_workspace,
    captions_vtt,
    chapters_vtt,
)
from hypothesis_lab.ui.widget import (
    ResearchWorkspace,
    Request,
    analyze,
    clean_workspace,
)


def test_practice_example_is_separate_synthetic_and_reproducible():
    practice = clean_workspace(practice_workspace())
    assert practice["synthetic"] and practice["is_tutorial"]
    assert not practice["is_demo"]
    assert practice["title"] != services.demo_workspace()["title"]
    assert len(practice["publications"]) == 1
    evidence = practice["evidence"][0]
    assert evidence["excerpt"] in practice["publications"][0]["abstract"]
    assert evidence["relationship"] == "inconclusive" and evidence["requires_review"]
    result = analyze(practice)
    assert (result["alpha"], result["beta"]) == (35, 17)
    assert result["interval"][0] < 0.6 < result["interval"][1]
    practice["publications"].clear()
    assert len(practice_workspace()["publications"]) == 1


def test_chapters_and_caption_tracks_cover_the_full_video():
    assert CHAPTERS[0]["start"] == 0
    assert DURATION == 122
    assert all(
        left["end"] == right["start"] for left, right in zip(CHAPTERS, CHAPTERS[1:])
    )
    assert captions_vtt().startswith("WEBVTT\n")
    assert "00:02:02.000" in captions_vtt()
    assert "Review the source excerpt" in chapters_vtt()


def test_loading_practice_never_overwrites_a_saved_investigation(tmp_path, monkeypatch):
    monkeypatch.setattr(persistence, "DB_PATH", tmp_path / "work.sqlite3")
    value = practice_workspace()
    value["notes"] = "Keep my actual research notes."
    services.save_workspace(value["title"], value)
    component = ResearchWorkspace()
    asyncio.run(component.dispatch(Request(id="practice", type="tutorial")))
    assert component.data["workspace"]["title"] != value["title"]
    assert services.load_workspace(value["title"])["notes"] == value["notes"]
    assert component.data["workspace"]["is_tutorial"]
    assert component.data["analysis"]["ready"]
    assert component.guide["duration"] == 122


def test_video_assets_are_packaged_and_self_contained():
    import base64
    from hypothesis_lab.ui.walkthrough import walkthrough_bundle

    walkthrough_bundle.cache_clear()
    guide = walkthrough_bundle()
    assert guide["video_src"].startswith("data:video/mp4;base64,")
    video = base64.b64decode(guide["video_src"].split(",", 1)[1])
    assert video[4:8] == b"ftyp" and len(video) > 100000
    assert guide["poster_src"].startswith("data:image/jpeg;base64,")
    captions = base64.b64decode(guide["captions_src"].split(",", 1)[1]).decode()
    assert captions == captions_vtt()
    assert len(guide["chapters"]) == 8
