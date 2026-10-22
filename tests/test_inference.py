import math
import pytest
from pydantic import ValidationError
from hypothesis_lab.models import Observation
from hypothesis_lab.inference import estimate, compare, sequence


def obs(k=20, n=100):
    return Observation(experiment_id="test", successes=k, trials=n)


def test_reference_posterior():
    r = estimate(2, 8, [obs()])
    assert (r.alpha, r.beta, r.mean) == (22, 88, 0.2)
    assert r.interval[0] == pytest.approx(0.1310239762, abs=1e-9)
    assert r.interval[0] < r.mean < r.interval[1]


@pytest.mark.parametrize("a,b", [(0, 8), (-1, 8), (2, float("nan")), (float("inf"), 8)])
def test_invalid_prior(a, b):
    with pytest.raises(ValueError):
        estimate(a, b, [obs()])


@pytest.mark.parametrize("k,n", [(21, 20), (-1, 20), (0, 0), (1.5, 20)])
def test_invalid_observations(k, n):
    with pytest.raises(ValidationError):
        obs(k, n)


def test_sequential_equals_pooled_and_order_invariant():
    batches = [obs(3, 25), obs(4, 25), obs(6, 25), obs(7, 25)]
    assert sequence(2, 8, batches)[-1] == estimate(2, 8, [obs()])
    assert estimate(2, 8, batches) == estimate(2, 8, list(reversed(batches)))


def test_log_bayes_factor():
    assert compare(0.1, 0.2, [obs()]) == pytest.approx(
        20 * math.log(2) + 80 * math.log(0.8 / 0.9)
    )
    assert compare(0.2, 0.2, [obs()]) == 0


def test_extreme_counts_remain_finite():
    for k in [0, 100]:
        r = estimate(2, 8, [obs(k, 100)])
        assert 0 < r.mean < 1
        assert 0 < r.interval[0] < r.interval[1] < 1


def test_no_observations_retains_prior():
    r = estimate(2, 8, [])
    assert (r.alpha, r.beta, r.mean) == (2, 8, 0.2)
