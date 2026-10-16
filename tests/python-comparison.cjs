// Python testinin karşılaştıracağı JavaScript rota sonuçlarını üretir.
const fs = require("node:fs");
const assert = require("node:assert/strict");
const engine = require("../route-engine.js");

const data = JSON.parse(fs.readFileSync("data/map-data.json", "utf8"));
const browserSource = fs.readFileSync("data/map-data.js", "utf8");
const browserJson = browserSource
  .slice(browserSource.indexOf("=") + 1)
  .trim()
  .replace(/;$/, "");
assert.deepEqual(JSON.parse(browserJson), data);

const network = engine.makeNetwork(data);
const allStops = data.bins.map((bin, index) => index + 1);
const selectedStops = [];
for (let index = 0; index < data.bins.length; index++) {
  if (data.bins[index].fill > 50) selectedStops.push(index + 1);
}

const baseline = engine.planTour(network.matrix, allStops);
const selectedTour = engine.planTour(
  network.matrix,
  selectedStops,
  baseline.order,
);
console.log(
  JSON.stringify({ baseline: baseline.meters, tour: selectedTour.meters }),
);
