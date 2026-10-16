"""Kutuların ziyaret sırasını hesapla. Araç noktası her zaman 0'dır."""

from dataclasses import dataclass
import math

from .graph import RoutingError


@dataclass(frozen=True)
class Tour:
    order: tuple[int, ...]
    meters: float


def tour_length(order: list[int] | tuple[int, ...], matrix: list[list[float]]) -> float:
    total = 0.0
    for start, end in zip(order, order[1:]):
        total += matrix[start][end]
    return total


def validate_inputs(
    matrix: list[list[float]], required: list[int] | tuple[int, ...]
) -> None:
    size = len(matrix)
    if size == 0:
        raise RoutingError("Mesafe matrisi boş olamaz.")

    for row in matrix:
        if len(row) != size:
            raise RoutingError("Mesafe matrisi kare olmalı.")
        for distance in row:
            if not math.isfinite(distance) or distance < 0:
                raise RoutingError(
                    "Mesafe matrisinde geçersiz veya ulaşılamayan yol var."
                )

    for stop in required:
        if type(stop) is not int or not 0 < stop < size:
            raise RoutingError("Geçersiz durak indeksi.")


def cheapest_insertion(
    first: int,
    selected: list[int],
    matrix: list[list[float]],
) -> list[int]:
    """Kalan her kutuyu, tura en az ek yol getiren konuma yerleştir."""
    order = [0, first, 0]
    remaining = [stop for stop in selected if stop != first]

    while remaining:
        best_cost = math.inf
        best_stop = None
        best_position = None

        for stop in remaining:
            for position in range(1, len(order)):
                previous_stop = order[position - 1]
                next_stop = order[position]

                # Eski bağlantı yerine yeni kutudan geçen iki bağlantı geliyor.
                extra_distance = (
                    matrix[previous_stop][stop]
                    + matrix[stop][next_stop]
                    - matrix[previous_stop][next_stop]
                )
                if extra_distance < best_cost:
                    best_cost = extra_distance
                    best_stop = stop
                    best_position = position

        if best_stop is None or best_position is None:
            raise RoutingError("Ulaşılabilir tur oluşturulamadı.")

        order.insert(best_position, best_stop)
        remaining.remove(best_stop)

    return order


def improve(order: list[int], matrix: list[list[float]]) -> Tour:
    """2-opt: ziyaret sırasının bir bölümünü ters çevirip daha kısa tur ara."""
    route = list(order)
    length = tour_length(route, matrix)

    for _ in range(12):
        best_route = route
        best_length = length

        for start in range(1, len(route) - 2):
            for end in range(start + 1, len(route) - 1):
                reversed_part = list(reversed(route[start : end + 1]))
                candidate = route[:start] + reversed_part + route[end + 1 :]

                # Tek yönler yüzünden yalnızca değişen uçları hesaplamak yetmez.
                candidate_length = tour_length(candidate, matrix)
                if candidate_length < best_length - 0.001:
                    best_route = candidate
                    best_length = candidate_length

        if best_length >= length - 0.001:
            break

        route = best_route
        length = best_length

    return Tour(tuple(route), length)


def plan_tour(
    matrix: list[list[float]],
    required: list[int] | tuple[int, ...],
    seed_tour: tuple[int, ...] | None = None,
) -> Tour:
    """Farklı başlangıçları dene ve bulunan en kısa turu döndür."""
    validate_inputs(matrix, required)
    selected = sorted(set(required))

    if not selected:
        return Tour((0,), 0.0)

    best = Tour((), math.inf)

    # Bütün kutuların turundan yalnızca seçilen kutuları bırakarak da dene.
    if seed_tour:
        allowed = {0, *selected}
        projected = [stop for stop in seed_tour if stop in allowed]
        starts_and_ends_at_depot = projected and projected[0] == projected[-1] == 0
        visits_each_stop_once = (
            set(projected[1:-1]) == set(selected)
            and len(projected) == len(selected) + 2
        )
        if starts_and_ends_at_depot and visits_each_stop_once:
            best = improve(projected, matrix)

    for first in selected:
        order = cheapest_insertion(first, selected, matrix)
        candidate = improve(order, matrix)

        if candidate.meters < best.meters:
            best = candidate

    # Bu bir sezgisel çözüm; bütün olası turların tarandığı anlamına gelmez.
    return best
