"""Web arayüzü ve terminal demosunun kullandığı ortak Python servisi."""

from datetime import datetime, timezone
from functools import lru_cache
import json
from pathlib import Path
from .graph import Network
from .routing import Tour, plan_tour
from .sensor import Calibration, finite_number, is_collection_candidate, parse_distance

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Planner:
    """Sabit yol ağını bir kez hazırla; değişen doluluklara göre tur seç."""

    def __init__(self, data_path: Path | None = None) -> None:
        self.data = json.loads((data_path or PROJECT_ROOT / "data" / "map-data.json").read_text(encoding="utf-8"))
        self.calibration = Calibration()
        self.network = Network.from_map(self.data)
        self.ids = [item["id"] for item in self.data["bins"]]
        if len(set(self.ids)) != len(self.ids):
            raise ValueError("Kutu kimlikleri benzersiz olmalı.")
        self.baseline = plan_tour(self.network.matrix, list(range(1, len(self.ids) + 1)))

    @lru_cache(maxsize=128)
    def _tour(self, required: tuple[int, ...]) -> Tour:
        return plan_tour(self.network.matrix, required, self.baseline.order)

    def initial_bins(self) -> list[dict]:
        return [{"id": item["id"], "fill": item["fill"]} for item in self.data["bins"]]

    def measurement(self, value: object) -> dict:
        """Bir seri monitör satırını Python ile doğrula ve yüzdeye çevir."""
        distance = parse_distance(value, self.calibration)
        return {"engine": "python", "simulation": True, "distanceCm": distance,
                "fillPercent": self.calibration.fill_percent(distance),
                "calibration": {"emptyCm": self.calibration.empty_cm, "fullCm": self.calibration.full_cm}}

    def plan(self, bins: object = None, threshold: object = 50.0) -> dict:
        """Eksik, yinelenmiş veya geçersiz kutu verisini sessizce boş sayma."""
        threshold_value = finite_number(threshold, "Eşik")
        if not 0 <= threshold_value <= 100:
            raise ValueError("Eşik %0–100 arasında olmalı.")
        if bins is None:
            bins = self.initial_bins()
        if not isinstance(bins, list) or len(bins) != len(self.ids):
            raise ValueError(f"Tam olarak {len(self.ids)} kutunun doluluğu gönderilmeli.")
        values: dict[str, float] = {}
        for item in bins:
            if not isinstance(item, dict) or not isinstance(item.get("id"), str):
                raise ValueError("Her kutu id ve fill alanlarını içermeli.")
            identifier = item["id"]
            if identifier not in self.ids or identifier in values:
                raise ValueError("Bilinmeyen veya yinelenmiş kutu kimliği.")
            fill = finite_number(item.get("fill"), "Doluluk")
            if not 0 <= fill <= 100:
                raise ValueError("Doluluk %0–100 arasında olmalı.")
            values[identifier] = fill
        required = tuple(i + 1 for i, identifier in enumerate(self.ids) if is_collection_candidate(values[identifier], threshold_value))
        tour = self._tour(required)
        saved = max(0.0, self.baseline.meters - tour.meters)
        candidates = [self.ids[i - 1] for i in required]
        return {"engine": "python", "simulation": True,
                "generatedAt": datetime.now(timezone.utc).isoformat(), "threshold": threshold_value,
                "candidateIds": candidates, "skippedIds": [identifier for identifier in self.ids if identifier not in candidates],
                "baseline": {"order": list(self.baseline.order), "meters": self.baseline.meters,
                             "pathNodes": self.network.route_nodes(self.baseline.order)},
                "tour": {"order": list(tour.order), "meters": tour.meters,
                         "pathNodes": self.network.route_nodes(tour.order)},
                "metrics": {"savedMeters": saved, "savingPercent": 100 * saved / self.baseline.meters if self.baseline.meters else 0.0},
                "algorithm": "Çok başlangıçlı en ucuz ekleme + yönlü 2-opt; kesin optimum garantisi yok",
                "dataSource": self.data["source"], "dataLicense": self.data["license"]}
