import json
from hypothesis_lab.demo import HYPOTHESIS, OBSERVATIONS, PUBLICATIONS
from hypothesis_lab.inference import estimate
from hypothesis_lab.reporting import snapshot, markdown
from hypothesis_lab import persistence


def test_reproducible_snapshot_and_sqlite_roundtrip(tmp_path, monkeypatch):
    result = estimate(2, 8, OBSERVATIONS)
    payload = snapshot(HYPOTHESIS, 2, 8, OBSERVATIONS, result, PUBLICATIONS, [])
    assert json.loads(json.dumps(payload))["posterior"]["mean"] == 0.2
    assert "synthetic" in markdown(payload)
    assert all(o["synthetic"] for o in payload["observations"])
    monkeypatch.setattr(persistence, "DB_PATH", tmp_path / "test.sqlite3")
    persistence.save("researcher's investigation", payload)
    loaded = persistence.load("researcher's investigation")
    assert loaded["prior"] == {"alpha": 2, "beta": 8}
    reproduced = estimate(
        loaded["prior"]["alpha"], loaded["prior"]["beta"], OBSERVATIONS
    )
    assert reproduced == result
