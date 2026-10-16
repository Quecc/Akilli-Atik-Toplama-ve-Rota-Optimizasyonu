(function (root) {
  'use strict';
  const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));
  function fillFromDistance(distance, empty = 200, full = 20) {
    if (!Number.isFinite(distance) || distance < 2 || distance > 400) return null;
    if (!(empty > full && full >= 2 && empty <= 400)) return null;
    return clamp(100 * (empty - distance) / (empty - full), 0, 100);
  }
  function parseDistance(text) {
    const value = String(text).trim();
    const match = value.match(/^\d+(?:[.,]\d+)?$/) || value.match(/Mesafe\s*:\s*(\d+(?:[.,]\d+)?)\s*cm/i);
    if (!match) return null;
    const n = Number((match[1] || match[0]).replace(',', '.'));
    return fillFromDistance(n) === null ? null : n;
  }
  function haversine(a, b) {
    const rad = Math.PI / 180, lat = (b[0] - a[0]) * rad, lon = (b[1] - a[1]) * rad;
    const v = Math.sin(lat / 2) ** 2 + Math.cos(a[0] * rad) * Math.cos(b[0] * rad) * Math.sin(lon / 2) ** 2;
    return 6371000 * 2 * Math.atan2(Math.sqrt(v), Math.sqrt(Math.max(0, 1 - v)));
  }
  function buildGraph(data) {
    const graph = new Map(Object.keys(data.nodes).map(id => [Number(id), []]));
    for (const road of data.roads) {
      for (let i = 1; i < road.nodes.length; i++) {
        const a = road.nodes[i - 1], b = road.nodes[i];
        if (!graph.has(a) || !graph.has(b)) continue;
        const length = haversine(data.nodes[a], data.nodes[b]);
        if (road.oneway !== '-1') graph.get(a).push([b, length]);
        if (!['yes', '1', 'true'].includes(road.oneway)) graph.get(b).push([a, length]);
      }
    }
    return graph;
  }
  class Heap {
    constructor() { this.items = []; }
    push(value) {
      const a = this.items; a.push(value); let i = a.length - 1;
      while (i > 0) { const p = (i - 1) >> 1; if (a[p][0] <= a[i][0]) break; [a[p], a[i]] = [a[i], a[p]]; i = p; }
    }
    pop() {
      const a = this.items, result = a[0], last = a.pop();
      if (a.length) { a[0] = last; let i = 0;
        while (true) { let n = i, l = i * 2 + 1, r = l + 1; if (l < a.length && a[l][0] < a[n][0]) n = l; if (r < a.length && a[r][0] < a[n][0]) n = r; if (n === i) break; [a[i], a[n]] = [a[n], a[i]]; i = n; }
      }
      return result;
    }
  }
  function dijkstra(graph, start, targets) {
    const dist = new Map([[start, 0]]), prev = new Map(), heap = new Heap(), remaining = new Set(targets);
    heap.push([0, start]);
    while (heap.items.length && remaining.size) {
      const [d, v] = heap.pop(); if (d !== dist.get(v)) continue;
      remaining.delete(v);
      for (const [next, length] of graph.get(v) || []) {
        const candidate = d + length;
        if (candidate < (dist.get(next) ?? Infinity)) { dist.set(next, candidate); prev.set(next, v); heap.push([candidate, next]); }
      }
    }
    return {dist, prev};
  }
  function makeNetwork(data) {
    const graph = buildGraph(data), points = [data.depot.node, ...data.bins.map(b => b.node)];
    const matrix = [], paths = [];
    for (const start of points) {
      const {dist, prev} = dijkstra(graph, start, points), row = [], pathRow = [];
      for (const target of points) {
        if (!dist.has(target)) throw new Error('Seçilen kutular arasında bağlı yol bulunamadı.');
        row.push(dist.get(target)); const nodes = [target]; let v = target;
        while (v !== start) { v = prev.get(v); if (v === undefined) throw new Error('Yol geri oluşturulamadı.'); nodes.push(v); }
        pathRow.push(nodes.reverse());
      }
      matrix.push(row); paths.push(pathRow);
    }
    return {graph, points, matrix, paths};
  }
  function tourLength(order, matrix) { let total = 0; for (let i = 1; i < order.length; i++) total += matrix[order[i - 1]][order[i]]; return total; }
  function improve(order, matrix) {
    let route = order.slice(), length = tourLength(route, matrix);
    for (let round = 0; round < 12; round++) {
      let best = route, bestLength = length;
      for (let i = 1; i < route.length - 2; i++) for (let j = i + 1; j < route.length - 1; j++) {
        const candidate = [...route.slice(0, i), ...route.slice(i, j + 1).reverse(), ...route.slice(j + 1)];
        const nextLength = tourLength(candidate, matrix); // Tek yönlü yollarda tüm ters segment yeniden değerlendirilir.
        if (nextLength < bestLength - 0.001) { best = candidate; bestLength = nextLength; }
      }
      if (bestLength >= length - 0.001) break;
      route = best; length = bestLength;
    }
    return {order: route, meters: length};
  }
  function planTour(matrix, required, seedTour) {
    const selected = [...new Set(required)].sort((a, b) => a - b);
    if (selected.some(i => !Number.isInteger(i) || i <= 0 || i >= matrix.length)) throw new Error('Geçersiz durak.');
    if (!selected.length) return {order: [0], meters: 0};
    let best = {order: [], meters: Infinity};
    if (seedTour) {
      const allowed = new Set([0, ...selected]), projected = seedTour.filter(i => allowed.has(i));
      if (projected[0] === 0 && projected.at(-1) === 0 && selected.every(i => projected.includes(i))) best = improve(projected, matrix);
    }
    for (const first of selected) {
      const order = [0, first, 0], remaining = selected.filter(i => i !== first);
      while (remaining.length) {
        let delta = Infinity, bestNode = -1, position = -1;
        for (const node of remaining) for (let p = 1; p < order.length; p++) {
          const cost = matrix[order[p - 1]][node] + matrix[node][order[p]] - matrix[order[p - 1]][order[p]];
          if (cost < delta) { delta = cost; bestNode = node; position = p; }
        }
        if (bestNode < 0 || !Number.isFinite(delta)) throw new Error('Ulaşılabilir rota bulunamadı.');
        order.splice(position, 0, bestNode); remaining.splice(remaining.indexOf(bestNode), 1);
      }
      const candidate = improve(order, matrix);
      if (candidate.meters < best.meters) best = candidate;
    }
    return best;
  }
  function routeNodes(order, paths) {
    const result = [];
    for (let i = 1; i < order.length; i++) result.push(...paths[order[i - 1]][order[i]].slice(i === 1 ? 0 : 1));
    return result;
  }
  const api = {fillFromDistance, parseDistance, haversine, buildGraph, makeNetwork, tourLength, planTour, routeNodes};
  if (typeof module === 'object' && module.exports) module.exports = api;
  root.TemizRotaEngine = api;
})(typeof window === 'object' ? window : globalThis);
