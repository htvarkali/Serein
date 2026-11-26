import numpy as np

from serein.features.graph import add_source_edges, build_knn_graph


def test_source_nodes_only_send_and_respect_the_radius():
    # Three EPA monitors, then two fire monitors: one 11 km away, one about 330 km away.
    lat = np.array([38.0, 38.5, 39.0, 38.1, 41.0])
    lon = np.array([-121.0, -121.0, -121.0, -121.0, -121.0])
    base = build_knn_graph(lat[:3], lon[:3], k=2, max_km=300.0)
    g = add_source_edges(base, lat, lon, n_targets=3, k=5, radius_km=150.0, max_km=300.0)

    assert np.array_equal(g.src[:base.n_edges], base.src)      # EPA edges unchanged
    assert np.array_equal(g.dst[:base.n_edges], base.dst)
    new_src, new_dst = g.src[base.n_edges:], g.dst[base.n_edges:]
    assert set(new_src) == {3}                                 # the far monitor sends nothing
    assert set(new_dst) <= {0, 1, 2}                           # fire monitors never receive
    assert (g.dist_km[base.n_edges:] <= 150.0).all()
    assert g.edge_attr.shape == (g.n_edges, 4)


def test_no_sources_returns_the_same_graph():
    lat, lon = np.array([38.0, 38.5]), np.array([-121.0, -121.0])
    base = build_knn_graph(lat, lon, k=1, max_km=300.0)
    assert add_source_edges(base, lat, lon, n_targets=2, k=5, radius_km=150.0,
                            max_km=300.0) is base
