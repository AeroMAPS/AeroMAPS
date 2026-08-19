"""Criterion 5: establish the exact rejection condition of _wrap_top_level_model.

Probes the guard with synthetic models that differ in one attribute at a time,
without building a full MultiRegionalProcess (the guard is a pure function of
the model instance).
"""

import types

import pandas as pd

from aeromaps.core.multi_regional_process import MultiRegionalProcess
from aeromaps.models.base import AeroMAPSModel
from spike_unified_mda.step1_plumbing import SPIKE_PARAMETERS


class _Probe(AeroMAPSModel):
    def __init__(self, name, **attrs):
        super().__init__(name=name, model_type="custom")
        self.input_names = {"x": pd.Series([0.0])}
        self.output_names = {"y": pd.Series([0.0])}
        for k, v in attrs.items():
            setattr(self, k, v)

    def compute(self, input_data):
        return {"y": input_data["x"]}


def _with_custom_setup(model):
    model.custom_setup = types.MethodType(lambda self: None, model)
    return model


def probe(label, model):
    """Run only _wrap_top_level_model against a stub 'self'."""
    stub = types.SimpleNamespace(parameters=SPIKE_PARAMETERS)
    try:
        disc = MultiRegionalProcess._wrap_top_level_model(stub, model)
        return label, "ACCEPTED", type(disc).__name__
    except NotImplementedError as exc:
        return label, "REJECTED", str(exc).split(" requires ")[1].split(", which")[0]
    except Exception as exc:  # noqa: BLE001
        return label, "ERROR", f"{type(exc).__name__}: {exc}"


CASES = [
    ("plain custom model", lambda: _Probe("plain")),
    ("+ custom_setup only", lambda: _with_custom_setup(_Probe("cs"))),
    ("+ pathways_manager=None only", lambda: _Probe("pm", pathways_manager=None)),
    (
        "+ pathways_manager=None AND custom_setup",
        lambda: _with_custom_setup(_Probe("pmcs", pathways_manager=None)),
    ),
    ("+ climate_historical_data=None", lambda: _Probe("chd", climate_historical_data=None)),
    (
        "+ markets=None AND custom_setup (markets pattern)",
        lambda: _with_custom_setup(_Probe("mk", markets=None)),
    ),
    ("+ fleet_model=None", lambda: _Probe("fm", fleet_model=None)),
]

if __name__ == "__main__":
    print(f"{'probe model':>48} {'verdict':>10}  detail")
    print("-" * 100)
    for label, factory in CASES:
        lab, verdict, detail = probe(label, factory())
        print(f"{lab:>48} {verdict:>10}  {detail}")

    print("\n--- Does _wrap_top_level_model call custom_setup()? ---")
    calls = []
    m = _Probe("probe_cs")
    m.custom_setup = types.MethodType(lambda self: calls.append("called"), m)
    stub = types.SimpleNamespace(parameters=SPIKE_PARAMETERS)
    MultiRegionalProcess._wrap_top_level_model(stub, m)
    print(f"custom_setup() called: {bool(calls)}")

    print("\n--- Does it inject `markets` / a config handle? ---")
    m2 = _Probe("probe_markets", markets="SENTINEL_NOT_REPLACED")
    m2.custom_setup = types.MethodType(lambda self: None, m2)
    MultiRegionalProcess._wrap_top_level_model(stub, m2)
    print(f"model.markets after wrapping: {m2.markets!r}")
