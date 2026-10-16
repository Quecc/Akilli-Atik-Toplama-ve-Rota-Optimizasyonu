(function (root) {
  "use strict";
  const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));
  function fillFromDistance(distance, empty = 200, full = 20) {
    if (!Number.isFinite(distance) || distance < 2 || distance > 400)
      return null;
    if (!(empty > full && full >= 2 && empty <= 400)) return null;
    return clamp((100 * (empty - distance)) / (empty - full), 0, 100);
  }
  function parseDistance(text) {
    const value = String(text).trim();
    const match =
      value.match(/^\d+(?:[.,]\d+)?$/) ||
      value.match(/Mesafe\s*:\s*(\d+(?:[.,]\d+)?)\s*cm/i);
    if (!match) return null;
    const n = Number((match[1] || match[0]).replace(",", "."));
    return fillFromDistance(n) === null ? null : n;
  }
  function haversine(a, b) {
    const rad = Math.PI / 180,
      lat = (b[0] - a[0]) * rad,
      lon = (b[1] - a[1]) * rad;
    const v =
      Math.sin(lat / 2) ** 2 +
      Math.cos(a[0] * rad) * Math.cos(b[0] * rad) * Math.sin(lon / 2) ** 2;
    return (
      6371000 * 2 * Math.atan2(Math.sqrt(v), Math.sqrt(Math.max(0, 1 - v)))
    );
  }
  function buildGraph(data) {
    const graph = new Map(
      Object.keys(data.nodes).map((id) => [Number(id), []]),
    );
    for (const road of data.roads) {
      for (let i = 1; i < road.nodes.length; i++) {
        const a = road.nodes[i - 1],
          b = road.nodes[i];
        if (!graph.has(a) || !graph.has(b)) continue;
        const length = haversine(data.nodes[a], data.nodes[b]);
        if (road.oneway !== "-1") graph.get(a).push([b, length]);
        if (!["yes", "1", "true"].includes(road.oneway))
          graph.get(b).push([a, length]);
      }
    }
    return graph;
  }
  // Dijkstra, sıradaki en yakın noktayı bu kuyruktan alır.
  class MinHeap {
    constructor() {
      this.items = [];
    }

    push(value) {
      const items = this.items;
      items.push(value);
      let index = items.length - 1;

      while (index > 0) {
        const parent = Math.floor((index - 1) / 2);
        if (items[parent][0] <= items[index][0]) break;

        [items[parent], items[index]] = [items[index], items[parent]];
        index = parent;
      }
    }

    pop() {
      const items = this.items;
      const nearest = items[0];
      const last = items.pop();

      if (items.length === 0) return nearest;
      items[0] = last;
      let index = 0;

      while (true) {
        let smallest = index;
        const left = index * 2 + 1;
        const right = left + 1;

        if (left < items.length && items[left][0] < items[smallest][0]) {
          smallest = left;
        }
        if (right < items.length && items[right][0] < items[smallest][0]) {
          smallest = right;
        }
        if (smallest === index) break;

        [items[index], items[smallest]] = [items[smallest], items[index]];
        index = smallest;
      }
      return nearest;
    }
  }

  function dijkstra(graph, start, targets) {
    const distances = new Map([[start, 0]]);
    const previous = new Map();
    const queue = new MinHeap();
    const remaining = new Set(targets);
    queue.push([0, start]);

    while (queue.items.length && remaining.size) {
      const [distance, node] = queue.pop();

      // Daha kısa bir yol bulunduysa eski kuyruk kaydını atla.
      if (distance !== distances.get(node)) continue;
      remaining.delete(node);

      for (const [neighbor, edgeLength] of graph.get(node) || []) {
        const candidate = distance + edgeLength;
        if (candidate < (distances.get(neighbor) ?? Infinity)) {
          distances.set(neighbor, candidate);
          previous.set(neighbor, node);
          queue.push([candidate, neighbor]);
        }
      }
    }
    return { dist: distances, prev: previous };
  }
  function makeNetwork(data) {
    const graph = buildGraph(data),
      points = [data.depot.node, ...data.bins.map((b) => b.node)];
    const matrix = [],
      paths = [];
    for (const start of points) {
      const { dist, prev } = dijkstra(graph, start, points),
        row = [],
        pathRow = [];
      for (const target of points) {
        if (!dist.has(target))
          throw new Error("Seçilen kutular arasında bağlı yol bulunamadı.");
        row.push(dist.get(target));
        const nodes = [target];
        let v = target;
        while (v !== start) {
          v = prev.get(v);
          if (v === undefined) throw new Error("Yol geri oluşturulamadı.");
          nodes.push(v);
        }
        pathRow.push(nodes.reverse());
      }
      matrix.push(row);
      paths.push(pathRow);
    }
    return { graph, points, matrix, paths };
  }
  function tourLength(order, matrix) {
    let total = 0;
    for (let i = 1; i < order.length; i++)
      total += matrix[order[i - 1]][order[i]];
    return total;
  }
  function improve(order, matrix) {
    let route = order.slice(),
      length = tourLength(route, matrix);
    for (let round = 0; round < 12; round++) {
      let best = route,
        bestLength = length;
      for (let i = 1; i < route.length - 2; i++)
        for (let j = i + 1; j < route.length - 1; j++) {
          const candidate = [
            ...route.slice(0, i),
            ...route.slice(i, j + 1).reverse(),
            ...route.slice(j + 1),
          ];
          const nextLength = tourLength(candidate, matrix); // Tek yönlü yollarda tüm ters segment yeniden değerlendirilir.
          if (nextLength < bestLength - 0.001) {
            best = candidate;
            bestLength = nextLength;
          }
        }
      if (bestLength >= length - 0.001) break;
      route = best;
      length = bestLength;
    }
    return { order: route, meters: length };
  }
  function planTour(matrix, required, seedTour) {
    const selected = [...new Set(required)].sort((a, b) => a - b);
    if (
      selected.some((i) => !Number.isInteger(i) || i <= 0 || i >= matrix.length)
    )
      throw new Error("Geçersiz durak.");
    if (!selected.length) return { order: [0], meters: 0 };
    let best = { order: [], meters: Infinity };
    if (seedTour) {
      const allowed = new Set([0, ...selected]),
        projected = seedTour.filter((i) => allowed.has(i));
      if (
        projected[0] === 0 &&
        projected.at(-1) === 0 &&
        selected.every((i) => projected.includes(i))
      )
        best = improve(projected, matrix);
    }
    for (const first of selected) {
      const order = [0, first, 0],
        remaining = selected.filter((i) => i !== first);
      while (remaining.length) {
        let delta = Infinity,
          bestNode = -1,
          position = -1;
        for (const node of remaining)
          for (let p = 1; p < order.length; p++) {
            const cost =
              matrix[order[p - 1]][node] +
              matrix[node][order[p]] -
              matrix[order[p - 1]][order[p]];
            if (cost < delta) {
              delta = cost;
              bestNode = node;
              position = p;
            }
          }
        if (bestNode < 0 || !Number.isFinite(delta))
          throw new Error("Ulaşılabilir rota bulunamadı.");
        order.splice(position, 0, bestNode);
        remaining.splice(remaining.indexOf(bestNode), 1);
      }
      const candidate = improve(order, matrix);
      if (candidate.meters < best.meters) best = candidate;
    }
    return best;
  }
  function routeNodes(order, paths) {
    const result = [];
    for (let i = 1; i < order.length; i++)
      result.push(...paths[order[i - 1]][order[i]].slice(i === 1 ? 0 : 1));
    return result;
  }
  const api = {
    fillFromDistance,
    parseDistance,
    haversine,
    buildGraph,
    makeNetwork,
    tourLength,
    planTour,
    routeNodes,
  };
  if (typeof module === "object" && module.exports) module.exports = api;
  root.TemizRotaEngine = api;
})(typeof window === "object" ? window : globalThis);
