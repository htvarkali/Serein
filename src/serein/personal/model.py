"""AirPlan: a personal, Bayesian model of one child's smoke sensitivity.

Idea in one paragraph
---------------------
Every child starts with the SAME prior belief, taken from studies of many
children ("on average, +10 µg/m³ of PM2.5 raises the odds of a symptom day by
~15%, but kids vary a lot"). Each day the family logs a 10-second check-in
(any symptoms? rescue inhaler puffs?). Bayes' rule updates the belief about
THIS child. After a few weeks the model knows if Maya reacts at 20 µg/m³ while
her brother is fine at 50, and it says how sure it is.

Math (for the Methods section)
------------------------------
  P(symptom day t) = sigmoid(x_t · β_child)
  β_child ~ Normal(μ_pop, Σ_pop)            (population prior)
Posterior via the Laplace approximation: find the most likely β with Newton's
method, then use the curvature (Hessian) there as the posterior precision.
This is exact enough for a handful of coefficients and takes milliseconds.

Features x_t (all known the evening before, from forecasts and the log):
  1                      intercept: baseline risk on a clean day
  pm0 / 10               forecast PM2.5 for day t (per 10 µg/m³)
  pm_lag12 / 10          mean PM2.5 of the 2 previous days (smoke effects lag)
  pm0 / 10 * outdoor     extra effect when the child is outdoors more (0..1)
  cold                   has a cold / virus (1/0); viruses are the #1 trigger
  missed_controller      missed daily controller medicine (1/0)
  ozone_x30_10           8-h ozone above 30 ppb, per 10 ppb (0 if unknown)
  hot_day                daily max temperature >= 32 °C / 90 °F (1/0)
  high_pollen            high pollen day, from a forecast or the family (1/0)
The last three are confounders (TODO C-10): smoke season is also ozone, heat and
pollen season, and without them the model would blame smoke for their effect.
They default to 0, so callers that don't know them get the old model.

Prior values come from published studies (TODO C-5, done 2026-11-01); see
docs/METHODS.md for the citations and caveats.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from numbers import Integral, Real
from statistics import NormalDist

import numpy as np

FEATURES = ["intercept", "pm0_10", "pm_lag12_10", "pm0_x_outdoor", "cold", "missed_controller",
            "ozone_x30_10", "hot_day", "high_pollen"]
HOT_DAY_C = 32.0  # Existing hot-day feature definition; hourly forecasts are a proxy for TMAX.


def sigmoid(z):
    return 1.0 / (1.0 + np.exp(-np.clip(z, -30, 30)))


def _validate_sample_count(n_samples):
    if (isinstance(n_samples, (bool, np.bool_))
            or not isinstance(n_samples, Integral) or n_samples < 1):
        raise ValueError("n_samples must be a positive integer")


@dataclass
class PopulationPrior:
    """Population prior (log-odds scale), FEATURES order. Sources: docs/METHODS.md#priors.

    Event studies (ER visits) measure severe outcomes; daily symptoms may react
    differently, so the SDs are deliberately wide: they say "kids vary a lot",
    which is exactly what the personal model then learns from the log.
    """
    mean: np.ndarray = field(default_factory=lambda: np.array(
        [np.log(0.12 / 0.88),  # ~12% of days with symptoms on clean days [assumption; ACBS: >=9/30 days = not well controlled]
         np.log(1.04),         # same-day, per +10 µg/m³ wildfire PM2.5: RR 1.04 (0-8%) [Sugrue 2026]
         np.log(1.03),         # lagged days: RR 1.02-1.04 at lags 3-4; 1.13 cumulative over 0-5 d [Sugrue 2026]
         np.log(1.02),         # extra when outdoors [assumption: no pediatric estimate found]
         np.log(4.0),          # respiratory virus: OR 5.6 (2.7-11.6) [Khetsuriani 2007]; 2.77 [Hong Kong study]
         np.log(1.6),          # missed controller: HR 0.61 for >75% vs <=25% ICS adherence [Williams 2011]
         np.log(1.082) / 2.92,  # ozone: warm-season RR 1.082 (1.043-1.123) per 29.2 ppb IQR,
                                # 3-day 8-h ozone, pediatric asthma ED visits [Strickland 2010]
         0.0,                  # hot day: no verified pediatric estimate [assumption: centered on no effect]
         0.0]))                # high pollen: no verified pediatric estimate [assumption: centered on no effect]
    sd: np.ndarray = field(default_factory=lambda: np.array(
        [1.0, 0.25, 0.20, 0.15, 0.5, 0.4, 0.10, 0.4, 0.4]))

    @property
    def precision(self):
        return np.diag(1.0 / self.sd ** 2)


def design_row(pm0, pm_lag1, pm_lag2, outdoor_frac, cold, missed_controller,
               ozone_ppb=None, hot_day=0, high_pollen=0):
    pm0 = np.asarray(pm0, float)
    lag = (np.asarray(pm_lag1, float) + np.asarray(pm_lag2, float)) / 2
    o3 = 0.0 if ozone_ppb is None else np.nan_to_num(np.asarray(ozone_ppb, float), nan=30.0)
    return np.stack(np.broadcast_arrays(
        np.ones_like(pm0), pm0 / 10, lag / 10, pm0 / 10 * np.asarray(outdoor_frac, float),
        np.asarray(cold, float), np.asarray(missed_controller, float),
        np.clip(o3 - 30.0, 0, None) / 10 if ozone_ppb is not None else np.zeros_like(pm0),
        np.asarray(hot_day, float), np.asarray(high_pollen, float)), -1)


@dataclass
class ChildModel:
    prior: PopulationPrior = field(default_factory=PopulationPrior)
    mean: np.ndarray | None = None
    cov: np.ndarray | None = None
    n_days: int = 0

    def fit(self, X: np.ndarray, y: np.ndarray, iters: int = 50) -> ChildModel:
        """Laplace posterior given logged days X [n, p], y [n] (0/1)."""
        X, y = np.asarray(X, dtype=float), np.asarray(y, dtype=float)
        if (X.ndim != 2 or X.shape[1] != len(FEATURES)
                or y.ndim != 1 or len(y) != len(X)):
            raise ValueError("training shapes must be X [n, len(FEATURES)] and y [n]")
        if np.any(np.isfinite(y) & (y != 0) & (y != 1)):
            raise ValueError("outcomes must be 0 or 1")
        ok = np.isfinite(y) & np.all(np.isfinite(X), 1)
        X, y = X[ok], y[ok]
        m0, P0 = self.prior.mean, self.prior.precision

        def log_post(beta):
            z = X @ beta
            ll = np.sum(y * z - np.logaddexp(0, z))
            return ll - 0.5 * (beta - m0) @ P0 @ (beta - m0)

        b = m0.copy() if self.mean is None else self.mean.copy()
        cur = log_post(b)
        for _ in range(iters):
            p = sigmoid(X @ b)
            grad = X.T @ (y - p) - P0 @ (b - m0)
            H = X.T @ (X * (p * (1 - p))[:, None]) + P0
            step = np.linalg.solve(H, grad)
            # Backtracking: big smoke days (PM/10 = 25) can make a full Newton
            # step overshoot into a flat region; halve until the posterior improves.
            t, new = 1.0, None
            while t > 1e-4:
                trial = log_post(b + t * step)
                if trial >= cur - 1e-12:
                    new = trial
                    break
                t *= 0.5
            if new is None:  # no step improves the posterior: already at the optimum
                break
            b, cur = b + t * step, new
            if np.max(np.abs(t * step)) < 1e-7:
                break
        p = sigmoid(X @ b)
        H = X.T @ (X * (p * (1 - p))[:, None]) + P0
        self.mean, self.cov, self.n_days = b, np.linalg.inv(H), len(y)
        return self

    def _params(self):
        if self.mean is None:
            return self.prior.mean, np.diag(self.prior.sd ** 2)
        return self.mean, self.cov

    def risk(self, X: np.ndarray, n_samples: int = 2000, seed: int = 0) -> dict:
        """Predicted probability of a symptom day, with a 90% credible range."""
        _validate_sample_count(n_samples)
        X = np.asarray(X, dtype=float)
        if (X.ndim not in (1, 2) or X.shape[-1] != len(FEATURES)
                or not np.isfinite(X).all()):
            raise ValueError("risk features must be finite rows with len(FEATURES) columns")
        m, C = self._params()
        rng = np.random.default_rng(seed)
        B = rng.multivariate_normal(m, C, size=n_samples)
        P = sigmoid(np.atleast_2d(X) @ B.T)  # [rows, samples]
        return {"mean": P.mean(1), "lo": np.quantile(P, 0.05, 1), "hi": np.quantile(P, 0.95, 1)}

    def risk_under_forecast(self, pm_quantiles: dict, pm_lag1: float, pm_lag2: float,
                            outdoor_frac: float, cold: int, missed: int,
                            n_samples: int = 4000, seed: int = 0, ozone_ppb=None,
                            hot_day: int = 0, high_pollen: int = 0) -> dict:
        """Integrate over BOTH the smoke forecast's uncertainty and the child model's.

        pm_quantiles: {0.05: x, 0.5: y, 0.95: z} from SmokeCast.
        Probabilities must be inside (0, 1), with finite, nonnegative,
        nondecreasing concentrations. A single quantile is a point forecast.
        Context inputs must be finite scalars; use None for unknown ozone.
        """
        _validate_sample_count(n_samples)
        context = [pm_lag1, pm_lag2, outdoor_frac, cold, missed, hot_day, high_pollen]
        if ozone_ppb is not None:
            context.append(ozone_ppb)
        if any(not isinstance(v, (Real, np.bool_)) or not np.isfinite(v) for v in context):
            raise ValueError("forecast context inputs must be finite scalars")
        if not pm_quantiles or any(
            isinstance(q, (bool, np.bool_)) or not isinstance(q, Real)
            or not np.isfinite(q) or not 0 < q < 1
            for q in pm_quantiles
        ):
            raise ValueError("forecast quantiles need probabilities inside (0, 1)")
        qs = np.array(sorted(pm_quantiles))
        concentrations = [pm_quantiles[q] for q in qs]
        if any(isinstance(v, (bool, np.bool_)) or not isinstance(v, Real)
               or not np.isfinite(v) or v < 0 for v in concentrations):
            raise ValueError("forecast quantiles need finite nonnegative concentrations")
        if np.any(np.diff(concentrations) < 0):
            raise ValueError("forecast quantiles must have nondecreasing concentrations")
        rng = np.random.default_rng(seed)
        vals = np.log1p(np.array(concentrations, dtype=float))
        # Sample the WHOLE forecast distribution, tails included: piecewise-linear in
        # log(PM) vs. normal z-score, extended past the outer quantiles with the outer
        # slopes. (Sampling only between q05 and q95 would ignore the worst 5% of days.)
        zq = np.array([NormalDist().inv_cdf(q) for q in qs])
        z = rng.standard_normal(n_samples)
        logpm = np.interp(z, zq, vals)
        if len(qs) >= 2:
            lo_slope = (vals[1] - vals[0]) / (zq[1] - zq[0])
            hi_slope = (vals[-1] - vals[-2]) / (zq[-1] - zq[-2])
            logpm = np.where(z < zq[0], vals[0] + (z - zq[0]) * lo_slope, logpm)
            logpm = np.where(z > zq[-1], vals[-1] + (z - zq[-1]) * hi_slope, logpm)
        pm = np.expm1(np.clip(logpm, 0, np.log1p(1000.0)))
        X = design_row(pm, pm_lag1, pm_lag2, outdoor_frac, cold, missed,
                       ozone_ppb, hot_day, high_pollen)
        m, C = self._params()
        B = rng.multivariate_normal(m, C, size=n_samples)
        p = sigmoid(np.sum(X * B, 1))
        return {"mean": float(p.mean()), "lo": float(np.quantile(p, 0.05)),
                "hi": float(np.quantile(p, 0.95))}

    def sensitivity(self) -> dict:
        """Odds ratio per +10 µg/m³ (same day), with 90% range. >1 = smoke-sensitive."""
        m, C = self._params()
        j = FEATURES.index("pm0_10")
        sd = np.sqrt(C[j, j])
        return {"or_per_10": float(np.exp(m[j])), "lo": float(np.exp(m[j] - 1.645 * sd)),
                "hi": float(np.exp(m[j] + 1.645 * sd))}

    def personal_threshold(self, rel_increase: float = 1.5, outdoor_frac: float = 0.3) -> float:
        """PM2.5 (µg/m³) at which this child's risk is rel_increase x their clean-air risk."""
        m, _ = self._params()
        grid = np.linspace(0, 300, 601)
        X = design_row(grid, grid, grid, outdoor_frac, 0, 0)
        p = sigmoid(X @ m)
        target = p[0] * rel_increase
        above = np.where(p >= target)[0]
        return float(grid[above[0]]) if len(above) else float("inf")
