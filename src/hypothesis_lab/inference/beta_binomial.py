"""Deterministic conjugate inference. No literature or language-model dependencies."""

from dataclasses import asdict, dataclass
import math
from scipy.stats import beta
from hypothesis_lab.models import Observation


@dataclass(frozen=True)
class Result:
    alpha: float
    beta: float
    mean: float
    interval: tuple[float, float]

    def to_dict(self):
        return asdict(self)


def estimate(
    alpha: float,
    beta_prior: float,
    observations: list[Observation],
    credibility: float = 0.95,
) -> Result:
    if not all(math.isfinite(v) and v > 0 for v in (alpha, beta_prior)):
        raise ValueError("Prior parameters must be finite and positive")
    if not 0 < credibility < 1:
        raise ValueError("Credibility must be between zero and one")
    a = alpha + sum(o.successes for o in observations)
    b = beta_prior + sum(o.trials - o.successes for o in observations)
    tail = (1 - credibility) / 2
    return Result(
        a, b, a / (a + b), tuple(float(x) for x in beta.ppf([tail, 1 - tail], a, b))
    )


def compare(p0: float, p1: float, observations: list[Observation]) -> float:
    """Log Bayes factor H1:H0 for explicitly specified simple binomial models."""
    if not all(math.isfinite(p) and 0 < p < 1 for p in (p0, p1)):
        raise ValueError("Probabilities must be strictly between zero and one")
    k = sum(o.successes for o in observations)
    n = sum(o.trials for o in observations)
    return k * math.log(p1 / p0) + (n - k) * math.log((1 - p1) / (1 - p0))


def sequence(alpha, beta_prior, observations):
    return [
        estimate(alpha, beta_prior, observations[:i])
        for i in range(len(observations) + 1)
    ]
