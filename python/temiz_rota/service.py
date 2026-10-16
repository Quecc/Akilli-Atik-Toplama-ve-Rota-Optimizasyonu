"""Panelin ve terminal demosunun kullandığı ölçüm ve rota işlemleri."""

from datetime import datetime, timezone
from functools import lru_cache
import json
from pathlib import Path

from .graph import Network
from .routing import Tour, plan_tour
from .sensor import Calibration, finite_number, is_collection_candidate, parse_distance

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Planner:
    def __init__(self, data_path: Path | None = None) -> None:
        if data_path is None:
            data_path = PROJECT_ROOT / "data" / "map-data.json"

        self.data = json.loads(data_path.read_text(encoding="utf-8"))
        self.calibration = Calibration()
        self.ids = [bin_data["id"] for bin_data in self.data["bins"]]

        if len(set(self.ids)) != len(self.ids):
            raise ValueError("Kutu kimlikleri benzersiz olmalı.")

        # Yol ağı sabit. Her doluluk değişiminde tekrar hazırlamak gerekmiyor.
        self.network = Network.from_map(self.data)
        all_stops = list(range(1, len(self.ids) + 1))
        self.baseline = plan_tour(self.network.matrix, all_stops)

    def initial_bins(self) -> list[dict]:
        bins = []
        for bin_data in self.data["bins"]:
            bins.append({"id": bin_data["id"], "fill": bin_data["fill"]})
        return bins

    def measurement(self, value: object) -> dict:
        distance = parse_distance(value, self.calibration)
        fill = self.calibration.fill_percent(distance)

        return {
            "engine": "python",
            "simulation": True,
            "distanceCm": distance,
            "fillPercent": fill,
            "calibration": {
                "emptyCm": self.calibration.empty_cm,
                "fullCm": self.calibration.full_cm,
            },
        }

    def validate_bins(self, bins: object) -> dict[str, float]:
        """Her kutunun bir kez geldiğini ve doluluğun geçerli olduğunu kontrol et."""
        if not isinstance(bins, list) or len(bins) != len(self.ids):
            raise ValueError(
                f"Tam olarak {len(self.ids)} kutunun doluluğu gönderilmeli."
            )

        fills = {}
        for bin_data in bins:
            if not isinstance(bin_data, dict):
                raise ValueError("Her kutu id ve fill alanlarını içermeli.")

            bin_id = bin_data.get("id")
            if not isinstance(bin_id, str):
                raise ValueError("Her kutu id ve fill alanlarını içermeli.")
            if bin_id not in self.ids or bin_id in fills:
                raise ValueError("Bilinmeyen veya yinelenmiş kutu kimliği.")

            fill = finite_number(bin_data.get("fill"), "Doluluk")
            if not 0 <= fill <= 100:
                raise ValueError("Doluluk %0–100 arasında olmalı.")

            fills[bin_id] = fill

        return fills

    @lru_cache(maxsize=128)
    def _tour(self, required: tuple[int, ...]) -> Tour:
        # Aday kutular aynı kaldıysa daha önce hesaplanan turu kullan.
        return plan_tour(self.network.matrix, required, self.baseline.order)

    def tour_details(self, tour: Tour) -> dict:
        return {
            "order": list(tour.order),
            "meters": tour.meters,
            "pathNodes": self.network.route_nodes(tour.order),
        }

    def plan(self, bins: object = None, threshold: object = 50.0) -> dict:
        threshold = finite_number(threshold, "Eşik")
        if not 0 <= threshold <= 100:
            raise ValueError("Eşik %0–100 arasında olmalı.")

        if bins is None:
            bins = self.initial_bins()
        fills = self.validate_bins(bins)

        required = []
        candidates = []
        skipped = []
        for stop_index, bin_id in enumerate(self.ids, start=1):
            if is_collection_candidate(fills[bin_id], threshold):
                required.append(stop_index)
                candidates.append(bin_id)
            else:
                skipped.append(bin_id)

        tour = self._tour(tuple(required))
        saved_meters = max(0.0, self.baseline.meters - tour.meters)
        saving_percent = 0.0
        if self.baseline.meters > 0:
            saving_percent = 100 * saved_meters / self.baseline.meters

        return {
            "engine": "python",
            "simulation": True,
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "threshold": threshold,
            "candidateIds": candidates,
            "skippedIds": skipped,
            "baseline": self.tour_details(self.baseline),
            "tour": self.tour_details(tour),
            "metrics": {
                "savedMeters": saved_meters,
                "savingPercent": saving_percent,
            },
            "algorithm": "Çok başlangıçlı en ucuz ekleme + yönlü 2-opt; kesin optimum garantisi yok",
            "dataSource": self.data["source"],
            "dataLicense": self.data["license"],
        }
