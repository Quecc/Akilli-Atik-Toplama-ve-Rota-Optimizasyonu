"""Durak ziyaret sırası: çok başlangıçlı ekleme ve yönlü maliyetli 2-opt.

Bu sezgisel bir iyileştirmedir; mutlak en kısa tur garantisi vermez.
Başlangıç/dönüş araç noktası matrisin sıfırıncı satırıdır.
"""

from dataclasses import dataclass
import math
from .graph import RoutingError


@dataclass(frozen=True)
class Tour:
    order: tuple[int, ...]
    meters: float


def tour_length(order: list[int] | tuple[int, ...], matrix: list[list[float]]) -> float:
    total = 0.0
    for a, b in zip(order, order[1:]):
        total += matrix[a][b]
    return total


def improve(order: list[int], matrix: list[list[float]]) -> Tour:
    """Bir segmenti ters çevirerek turu iyileştir.

    Tek yönlü ağda a→b ve b→a maliyetleri eşit olmak zorunda değildir.
    Bu nedenle yalnızca iki dış kenar yerine bütün aday tur hesaplanır.
    """
    route = list(order)
    length = tour_length(route, matrix)
    for _ in range(12):
        best, best_length = route, length
        for i in range(1, len(route) - 2):
            for j in range(i + 1, len(route) - 1):
                candidate = route[:i] + list(reversed(route[i:j + 1])) + route[j + 1:]
                candidate_length = tour_length(candidate, matrix)
                if candidate_length < best_length - 0.001:
                    best, best_length = candidate, candidate_length
        if best_length >= length - 0.001:
            break
        route, length = best, best_length
    return Tour(tuple(route), length)


def plan_tour(matrix: list[list[float]], required: list[int] | tuple[int, ...], seed_tour: tuple[int, ...] | None = None) -> Tour:
    """Bütün gerekli durakları bir kez ziyaret edip araç noktasına dön.

    Her olası ilk durak denenir. Kalan duraklar turdaki ek maliyeti
    en az olan yere eklenir. Ardından yönlü 2-opt uygulanır.
    Karşılaştırma turu verilirse onun seçili duraklara indirgenmiş hali
    de değerlendirilir; seçili tur için iyi bir üst sınır sağlar.
    """
    size = len(matrix)
    if not size or any(len(row) != size for row in matrix):
        raise RoutingError("Mesafe matrisi boş olmayan kare bir matris olmalı.")
    if any(not math.isfinite(value) or value < 0 for row in matrix for value in row):
        raise RoutingError("Mesafe matrisinde geçersiz veya ulaşılamayan yol var.")
    if any(type(item) is not int or not 0 < item < size for item in required):
        raise RoutingError("Geçersiz durak indeksi.")
    selected = sorted(set(required))
    if not selected:
        return Tour((0,), 0.0)
    best = Tour((), math.inf)
    if seed_tour:
        allowed = {0, *selected}
        projected = [item for item in seed_tour if item in allowed]
        if projected and projected[0] == projected[-1] == 0 and set(projected[1:-1]) == set(selected) and len(projected) == len(selected) + 2:
            best = improve(projected, matrix)
    for first in selected:
        order = [0, first, 0]
        remaining = [item for item in selected if item != first]
        while remaining:
            delta, chosen, position = math.inf, None, None
            for item in remaining:
                for p in range(1, len(order)):
                    cost = matrix[order[p - 1]][item] + matrix[item][order[p]] - matrix[order[p - 1]][order[p]]
                    if cost < delta:
                        delta, chosen, position = cost, item, p
            if chosen is None or position is None:
                raise RoutingError("Ulaşılabilir tur oluşturulamadı.")
            order.insert(position, chosen)
            remaining.remove(chosen)
        candidate = improve(order, matrix)
        if candidate.meters < best.meters:
            best = candidate
    return best
