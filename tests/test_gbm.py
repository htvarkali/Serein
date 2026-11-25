import numpy as np

from serein.models.gbm import GBM_QUANTILES, QuantileGBM


def data(n=1500, seed=0):
    rng = np.random.default_rng(seed)
    X = rng.normal(size=(n, 3))
    y = np.stack([2 * X[:, 0], -X[:, 1]], 1) + rng.normal(size=(n, 2))
    y[::4, 1] = np.nan  # lead 1 has no observation on a quarter of the rows
    return X, y


def test_gbm_fits_each_lead_on_its_observed_rows_and_spreads_its_quantiles():
    X, y = data()
    gbm = QuantileGBM(max_iter=100).fit(X, y)
    assert sorted(gbm.models) == sorted((lead, q) for lead in (0, 1) for q in GBM_QUANTILES)

    out = gbm.predict(X, 2)
    assert out.shape == (len(X), 2, len(GBM_QUANTILES)) and out.dtype == np.float32
    # Unit noise: the true 5% to 95% range is 3.29 wide, centered on the signal.
    width = (out[..., 2] - out[..., 0]).mean(0)
    assert ((width > 2.5) & (width < 4.0)).all()
    assert np.abs(out[:, 0, 1] - 2 * X[:, 0]).mean() < 0.6
    assert np.abs(out[:, 1, 1] + X[:, 1]).mean() < 0.6


class _Constant:
    def __init__(self, value):
        self.value = value

    def predict(self, X):
        return np.full(len(X), self.value)


def test_gbm_quantiles_never_cross():
    gbm = QuantileGBM()
    gbm.models = {(0, 0.05): _Constant(3.0), (0, 0.5): _Constant(1.0), (0, 0.95): _Constant(2.0)}
    out = gbm.predict(np.zeros((4, 3)), 1)
    np.testing.assert_array_equal(out, np.tile([1.0, 2.0, 3.0], (4, 1, 1)))
