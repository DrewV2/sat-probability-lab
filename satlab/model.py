"""Finite probability calculations; SAT point conversions are illustrative only.

No fitted College Board item parameters or empirical calibration data are included.
The answer model assumes independent Bernoulli outcomes conditional on supplied p.
"""
from dataclasses import asdict, dataclass, fields
from collections import defaultdict
from math import comb, exp, isfinite


@dataclass(frozen=True)
class Counts:
    confident: int = 0
    guess2: int = 0
    guess3: int = 0
    guess4: int = 0
    fill_right: int = 0
    fill_wrong: int = 0
    fill_uncertain: int = 0
    wrong: int = 0

    def validate(self, section):
        if section not in ("rw", "math"):
            raise ValueError("section must be 'rw' or 'math'")
        values = asdict(self).values()
        if any(type(v) is not int or v < 0 for v in values):
            raise ValueError("Counts must be nonnegative integers.")
        n = 27 if section == "rw" else 22
        if sum(values) != n:
            raise ValueError(f"{section} requires exactly {n} questions per module.")
        if section == "rw" and (self.fill_right + self.fill_wrong + self.fill_uncertain):
            raise ValueError("Fill-in categories are only available in Math.")

    def probabilities(self, settings):
        ps = (settings.confidence, .5, 1/3, .25, 1., 0., settings.fill_probability, 0.)
        return [p for field, p in zip(fields(self), ps)
                for _ in range(getattr(self, field.name))]


@dataclass(frozen=True)
class Settings:
    confidence: float = .99
    fill_probability: float = .25
    coverage: float = .90
    routing_midpoint: float = .70
    routing_width: float = .07
    easy_cap: int = 600
    hard_floor: int = 200
    noise_radius: int = 40

    def __post_init__(self):
        for key in ("confidence", "fill_probability", "routing_midpoint"):
            value = getattr(self, key)
            if not isfinite(value) or not 0 <= value <= 1:
                raise ValueError(f"{key} must be between 0 and 1.")
        if not isfinite(self.coverage) or not 0 < self.coverage < 1:
            raise ValueError("coverage must be strictly between 0 and 1.")
        if not isfinite(self.routing_width) or self.routing_width < .001:
            raise ValueError("routing_width must be at least .001.")
        for key, low, high in (("easy_cap", 200, 800), ("hard_floor", 200, 800), ("noise_radius", 0, 200)):
            value = getattr(self, key)
            if type(value) is not int or not low <= value <= high or value % 10:
                raise ValueError(f"{key} must be an integer multiple of 10 in [{low}, {high}].")


def poisson_binomial(probabilities):
    """P(sum X_i = k) via exact recurrence; O(n²) work, O(n) memory."""
    pmf = [1.]
    for p in probabilities:
        if not isfinite(p) or not 0 <= p <= 1:
            raise ValueError("Each probability must lie in [0, 1].")
        next_pmf = [0.] * (len(pmf) + 1)
        for k, mass in enumerate(pmf):
            next_pmf[k] += mass * (1 - p)
            next_pmf[k + 1] += mass * p
        pmf = next_pmf
    return dict(enumerate(pmf))


def convolve(a, b):
    """Sum two independent integer-valued distributions."""
    result = defaultdict(float)
    for x, p in a.items():
        for y, q in b.items():
            result[x + y] += p * q
    return dict(result)


def quantile(pmf, probability):
    if not 0 < probability < 1:
        raise ValueError("Quantile probability must be strictly between 0 and 1.")
    cumulative = 0.
    for value, mass in sorted(pmf.items()):
        cumulative += mass
        if cumulative + 1e-12 >= probability:
            return value
    raise ValueError("Distribution is empty or not normalized.")


def summarize(pmf, coverage=.90):
    if not 0 < coverage < 1:
        raise ValueError("coverage must be strictly between 0 and 1.")
    tail = (1 - coverage) / 2
    low, high = quantile(pmf, tail), quantile(pmf, 1-tail)
    mean = sum(k*p for k, p in pmf.items())
    return dict(low=low, median=quantile(pmf, .5), high=high, mean=mean,
                variance=sum(p*(k-mean)**2 for k, p in pmf.items()),
                interval_mass=sum(p for k,p in pmf.items() if low <= k <= high))


def scored_distribution(raw, pretest=2):
    """Marginalize uniform unknown pretest positions (an approximation).

    Real pretest placement is constrained. Uniform selection here is a teaching
    assumption, not College Board's test assembly procedure.
    """
    n = max(raw)
    if type(pretest) is not int or not 0 <= pretest <= n:
        raise ValueError("Invalid pretest count.")
    result = defaultdict(float)
    for correct, mass in raw.items():
        for removed in range(pretest+1):
            if removed <= correct and pretest-removed <= n-correct:
                weight = comb(correct, removed)*comb(n-correct, pretest-removed)/comb(n, pretest)
                result[correct-removed] += mass*weight
    return dict(result)


def hard_route_probability(correct, total, settings):
    z = (correct/total-settings.routing_midpoint)/settings.routing_width
    return 1/(1+exp(-max(-700, min(700, z))))


def illustrative_points(first, second, operational, route, settings):
    """Toy linear score mapping with routing mixture and triangular uncertainty."""
    if route not in ("unknown", "hard", "easy"):
        raise ValueError("route must be unknown, hard, or easy")
    result, harder_probability = defaultdict(float), 0.
    radius = settings.noise_radius//10
    weights = {j*10: radius+1-abs(j) for j in range(-radius, radius+1)}
    normalizer = sum(weights.values())
    for k, p in first.items():
        hard = (hard_route_probability(k, operational, settings) if route == "unknown"
                else float(route == "hard"))
        harder_probability += p*hard
        for l, q in second.items():
            fraction = (k+l)/(2*operational)
            for route_weight, floor, cap in ((hard, settings.hard_floor, 800),
                                             (1-hard, 200, settings.easy_cap)):
                base = floor+(cap-floor)*fraction
                for noise, weight in weights.items():
                    score = max(floor, min(cap, 10*round((base+noise)/10)))
                    result[score] += p*q*route_weight*weight/normalizer
    return dict(result), harder_probability


def predict_section(module1, module2, section, *, route="unknown", settings=None,
                    include_illustrative_scores=False):
    settings = settings or Settings()
    if route not in ("unknown", "hard", "easy"):
        raise ValueError("route must be unknown, hard, or easy")
    for counts in (module1, module2):
        counts.validate(section)
    raw = [poisson_binomial(c.probabilities(settings)) for c in (module1, module2)]
    total = convolve(*raw)
    result = dict(raw_pmf=total, raw_summary=summarize(total, settings.coverage),
                  module_summaries=[summarize(d, settings.coverage) for d in raw],
                  score_status="not_calibrated", score_pmf=None, score_summary=None)
    if include_illustrative_scores:
        points, hard = illustrative_points(*[scored_distribution(d) for d in raw],
                                          25 if section == "rw" else 20, route, settings)
        result.update(score_pmf=points, score_summary=summarize(points, settings.coverage),
                      harder_route_probability=hard, score_status="illustrative_only")
    return result


def predict_test(rw, math, *, routes=None, settings=None, include_illustrative_scores=False):
    settings, routes = settings or Settings(), routes or {}
    if len(rw) != 2 or len(math) != 2:
        raise ValueError("Supply exactly two modules per section.")
    sections = {section: predict_section(*modules, section, route=routes.get(section, "unknown"),
                settings=settings, include_illustrative_scores=include_illustrative_scores)
                for section, modules in (("rw", rw), ("math", math))}
    total = convolve(sections["rw"]["score_pmf"], sections["math"]["score_pmf"]) if include_illustrative_scores else None
    return dict(sections=sections, total_score_pmf=total,
                total_score_summary=summarize(total, settings.coverage) if total else None,
                settings=asdict(settings), score_status="illustrative_only" if total else "not_calibrated")
