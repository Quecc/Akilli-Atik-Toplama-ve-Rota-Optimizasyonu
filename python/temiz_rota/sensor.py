"""Mesafe ölçümünü doğrulama ve kutuya göre doluluk hesabı.

Sensör kutunun tepesinde aşağı bakar: mesafe azaldıkça doluluk artar.
Varsayılan 200 / 20 cm değerleri yalnızca mevcut simülasyon örneğidir.
"""

from dataclasses import dataclass
import math
import re


class MeasurementError(ValueError):
    """Ölçüm geçersizdir; bu durum boş kutu olarak yorumlanmamalıdır."""


def finite_number(value: object, label: str) -> float:
    """JSON true/false dahil, sayısal olmayan ve sonsuz değerleri reddet."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} sonlu bir sayı olmalı.")
    try:
        number = float(value)
    except (OverflowError, ValueError) as error:
        raise ValueError(f"{label} sonlu bir sayı olmalı.") from error
    if not math.isfinite(number):
        raise ValueError(f"{label} sonlu bir sayı olmalı.")
    return number


@dataclass(frozen=True)
class Calibration:
    """Sensör yüzeyinden boş tabana ve dolu seviyeye olan mesafeler."""

    empty_cm: float = 200.0
    full_cm: float = 20.0
    min_cm: float = 2.0
    max_cm: float = 400.0

    def __post_init__(self) -> None:
        empty = finite_number(self.empty_cm, "Boş mesafesi")
        full = finite_number(self.full_cm, "Dolu mesafesi")
        minimum = finite_number(self.min_cm, "En küçük mesafe")
        maximum = finite_number(self.max_cm, "En büyük mesafe")
        if not 0 < minimum <= full < empty <= maximum:
            raise ValueError(
                "Kalibrasyonda 0 < alt sınır ≤ dolu < boş ≤ üst sınır olmalı."
            )

    def fill_percent(self, distance_cm: object) -> float:
        """Geçerli mesafeden %0–100 arasında yaklaşık seviye üret.

        Geçersiz okumada hata yükseltilir. 200 cm'den uzak ama sensörün
        ölçüm aralığındaki bir hedef, bu örnek kalibrasyonda %0'a kırpılır.
        """
        try:
            distance = finite_number(distance_cm, "Mesafe")
        except ValueError as error:
            raise MeasurementError(str(error)) from error
        if not self.min_cm <= distance <= self.max_cm:
            raise MeasurementError(
                f"Mesafe {self.min_cm:g}–{self.max_cm:g} cm arasında olmalı."
            )
        fill = 100.0 * (self.empty_cm - distance) / (self.empty_cm - self.full_cm)
        return min(100.0, max(0.0, fill))


def parse_distance(value: object, calibration: Calibration | None = None) -> float:
    """80, '80,5' veya 'Mesafe: 80.0 cm | ...' girdisini cm olarak oku.

    Tinkercad'in 'in' etiketi inçtir. İnç yazılı girdiler cm sanılarak
    kabul edilmez. Tam seri monitör satırından yalnızca Mesafe alanı alınır.
    """
    calibration = calibration or Calibration()
    if isinstance(value, str):
        text = value.strip()
        match = re.fullmatch(r"\d+(?:[.,]\d+)?", text)
        if match:
            distance = float(text.replace(",", "."))
        else:
            match = re.search(r"Mesafe\s*:\s*(\d+(?:[.,]\d+)?)\s*cm\b", text, re.I)
            if not match:
                raise MeasurementError(
                    "Santimetre cinsinden sayı veya 'Mesafe: 80.0 cm' satırı girin."
                )
            distance = float(match.group(1).replace(",", "."))
    else:
        try:
            distance = finite_number(value, "Mesafe")
        except ValueError as error:
            raise MeasurementError(str(error)) from error
    calibration.fill_percent(distance)
    return distance


def is_collection_candidate(fill: object, threshold: object = 50.0) -> bool:
    """Kural kesinlikle 'eşikten büyük'tür; tam %50, %50 eşiğini aşmaz."""
    fill_value = finite_number(fill, "Doluluk")
    threshold_value = finite_number(threshold, "Eşik")
    if not 0 <= fill_value <= 100 or not 0 <= threshold_value <= 100:
        raise ValueError("Doluluk ve eşik %0–100 arasında olmalı.")
    return fill_value > threshold_value
