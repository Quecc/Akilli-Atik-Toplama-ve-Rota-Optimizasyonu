"""OSM yol geometrisinden yönlü grafik ve Dijkstra en kısa yolları."""

from dataclasses import dataclass
import heapq
import math

Coordinates = tuple[float, float]
Graph = dict[int, list[tuple[int, float]]]


class RoutingError(ValueError):
    """İstenen duraklara geçerli bir yol oluşturulamadı."""


def haversine(a: Coordinates, b: Coordinates) -> float:
    """İki enlem/boylam noktası arasındaki küresel mesafe, metre."""
    radians = math.pi / 180
    latitude = (b[0] - a[0]) * radians
    longitude = (b[1] - a[1]) * radians
    value = math.sin(latitude / 2) ** 2
    value += (
        math.cos(a[0] * radians)
        * math.cos(b[0] * radians)
        * math.sin(longitude / 2) ** 2
    )
    value = min(1.0, max(0.0, value))
    return 6_371_000 * 2 * math.atan2(math.sqrt(value), math.sqrt(1 - value))


def build_graph(data: dict) -> Graph:
    """Yol ardışık düğümlerini bağla; OSM tek yön etiketlerini koru.

    Dönüş yasağı ilişkileri ve kamyon kısıtları bu demo veri modelinde
    yoktur. Bu fonksiyonun çıktısı sahaya hazır navigasyon değildir.
    """
    nodes = {int(key): tuple(point) for key, point in data["nodes"].items()}
    graph: Graph = {node_id: [] for node_id in nodes}
    for road in data["roads"]:
        direction = str(road.get("oneway", "no"))
        for a, b in zip(road["nodes"], road["nodes"][1:]):
            if a not in nodes or b not in nodes:
                raise RoutingError("Yol, koordinatı bulunmayan bir düğüm içeriyor.")
            length = haversine(nodes[a], nodes[b])
            if direction != "-1":
                graph[a].append((b, length))
            if direction not in {"yes", "1", "true"}:
                graph[b].append((a, length))
    return graph


def dijkstra(
    graph: Graph, start: int, targets: set[int]
) -> tuple[dict[int, float], dict[int, int]]:
    """Negatif olmayan yol uzunluklarıyla tek başlangıçlı en kısa yol.

    heapq en küçük mevcut uzaklığı seçer. Kuyruktaki eski kayıtlar
    atlanır. Bütün hedefler kesinleşince gereksiz arama sonlandırılır.
    """
    if start not in graph:
        raise RoutingError("Başlangıç yol grafiğinde bulunamadı.")
    distances = {start: 0.0}
    previous: dict[int, int] = {}
    queue = [(0.0, start)]
    remaining = set(targets)
    while queue and remaining:
        distance, node = heapq.heappop(queue)
        if distance != distances.get(node):
            continue
        remaining.discard(node)
        for neighbor, edge_length in graph[node]:
            if not math.isfinite(edge_length) or edge_length < 0:
                raise RoutingError(
                    "Dijkstra için yol uzunlukları sonlu ve negatif olmayan sayılar olmalı."
                )
            candidate = distance + edge_length
            if candidate < distances.get(neighbor, math.inf):
                distances[neighbor] = candidate
                previous[neighbor] = node
                heapq.heappush(queue, (candidate, neighbor))
    if remaining:
        raise RoutingError("Seçilen kutulardan en az birine yönlü yol bulunamadı.")
    return distances, previous


@dataclass
class Network:
    """Araç noktası ve kutular için mesafe matrisi ve gerçek yol düğümleri."""

    graph: Graph
    points: list[int]
    matrix: list[list[float]]
    paths: list[list[list[int]]]

    @classmethod
    def from_map(cls, data: dict) -> "Network":
        graph = build_graph(data)
        points = [data["depot"]["node"], *(item["node"] for item in data["bins"])]
        matrix: list[list[float]] = []
        paths: list[list[list[int]]] = []
        for start in points:
            distances, previous = dijkstra(graph, start, set(points))
            matrix.append([distances[target] for target in points])
            row = []
            for target in points:
                route = [target]
                while route[-1] != start:
                    route.append(previous[route[-1]])
                row.append(list(reversed(route)))
            paths.append(row)
        return cls(graph, points, matrix, paths)

    def route_nodes(self, order: list[int] | tuple[int, ...]) -> list[int]:
        """Ziyaret sırasını OSM yol düğümlerinden geçen çizgiye dönüştür."""
        result: list[int] = []
        for index, (start, end) in enumerate(zip(order, order[1:])):
            result.extend(self.paths[start][end][0 if index == 0 else 1 :])
        return result
