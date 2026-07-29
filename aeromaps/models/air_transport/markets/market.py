from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class Market:
    """Dataclass holding metadata and input parameters for a single market.

    Attributes
    ----------
    id : str
        Identifier used as the market key in YAML and in variable name templates
        (e.g. ``short_range``).
    name : str
        Easy-to-read display name (e.g. ``"Short Range"``).
    traffic_type : str
        Traffic category: ``"passenger"`` or ``"freight"``.
    traffic_unit : str
        Traffic unit: ``"RPK"`` for passenger markets, ``"RTK"`` for freight.
    inputs : dict
        Raw inputs dict as loaded from YAML.  Structure mirrors the ``inputs``
        block in ``markets.yaml`` (keys: ``initial``, ``growth``, ``covid``,
        ``measures``, ``efficiency_simple``, ``costs``).  Flattening to
        ``self.parameters`` names happens in Phase 1 (``_initialize_markets``).
    """

    id: str = None
    name: str = None
    traffic_type: str = None
    traffic_unit: str = None
    inputs: Dict[str, Any] = field(default_factory=dict)
