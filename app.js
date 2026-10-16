(function () {
  "use strict";
  const engine = window.TemizRotaEngine,
    data = window.TEMIZ_ROTA_MAP;
  const getElement = (id) => document.getElementById(id);
  const esc = (v) =>
    String(v).replace(
      /[&<>"']/g,
      (c) =>
        ({
          "&": "&amp;",
          "<": "&lt;",
          ">": "&gt;",
          '"': "&quot;",
          "'": "&#39;",
        })[c],
    );
  const number = (n, digits = 1) =>
    n.toLocaleString("tr-TR", { maximumFractionDigits: digits });
  const km = (meters) => `${number(meters / 1000, 2)} km`;
  const percent = (n) => number(n, Number.isInteger(n) ? 0 : 1);
  const clock = (iso) =>
    iso
      ? new Intl.DateTimeFormat("tr-TR", {
          timeZone: "Europe/Istanbul",
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit",
        }).format(new Date(iso))
      : "Başlangıç senaryosu";
  const initialFills = data?.bins.map((b) => b.fill);
  let bins =
    data?.bins.map((b) => ({ ...b, updatedAt: null, source: "scenario" })) ||
    [];
  let threshold = 50,
    selected = 0,
    filter = "all",
    search = "",
    simulation = null,
    tick = 0,
    toastTimeout;
  const STORAGE_KEY = "temiz-rota-gultepe-v1";
  try {
    const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || "null");
    if (
      saved?.version === 1 &&
      Array.isArray(saved.bins) &&
      saved.bins.length === bins.length &&
      Number.isFinite(saved.threshold) &&
      saved.threshold >= 0 &&
      saved.threshold <= 100 &&
      saved.bins.every(
        (b, i) =>
          b.id === bins[i].id &&
          Number.isFinite(b.fill) &&
          b.fill >= 0 &&
          b.fill <= 100,
      )
    ) {
      bins = bins.map((b, i) => ({
        ...b,
        fill: saved.bins[i].fill,
        updatedAt:
          typeof saved.bins[i].updatedAt === "string" &&
          Number.isFinite(Date.parse(saved.bins[i].updatedAt))
            ? saved.bins[i].updatedAt
            : null,
        source: "saved",
      }));
      threshold = saved.threshold;
    }
  } catch {}
  function persist() {
    try {
      localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify({
          version: 1,
          threshold,
          bins: bins.map(({ id, fill, updatedAt }) => ({
            id,
            fill,
            updatedAt,
          })),
        }),
      );
    } catch {}
  }
  function toast(text) {
    getElement("toast").textContent = text;
    getElement("toast").hidden = false;
    clearTimeout(toastTimeout);
    toastTimeout = setTimeout(() => {
      getElement("toast").hidden = true;
    }, 3200);
  }
  function collect(bin) {
    return bin.fill > threshold;
  }
  let network, baseline, current;
  let pythonAvailable = false,
    pythonPendingKey = null,
    pythonSequence = 0;
  const pythonPlans = new Map();
  const tourCache = new Map();
  try {
    if (!data || bins.length !== 20)
      throw new Error("Mahalle verisi yüklenemedi.");
    network = engine.makeNetwork(data);
    baseline = engine.planTour(
      network.matrix,
      bins.map((_, i) => i + 1),
    );
  } catch (error) {
    getElement("route-computed-status").textContent = error.message;
    getElement("route-computed-status").style.color = "#b34e3c";
    toast(
      "Harita verisi yüklenemedi. Proje dosyalarının tamamını aynı klasörde açın.",
    );
    return;
  }

  const [south, west, north, east] = data.bbox,
    midLat = (south + north) / 2,
    midLon = (west + east) / 2;
  const metersPerLon = 111320 * Math.cos((midLat * Math.PI) / 180),
    metersPerLat = 111320;
  const scale = Math.min(
    900 / ((east - west) * metersPerLon),
    690 / ((north - south) * metersPerLat),
  );
  function project(point) {
    return [
      500 + (point[1] - midLon) * metersPerLon * scale,
      400 - (point[0] - midLat) * metersPerLat * scale,
    ];
  }
  const svgNS = "http://www.w3.org/2000/svg";
  function svg(tag, attrs, parent) {
    const node = document.createElementNS(svgNS, tag);
    for (const [key, value] of Object.entries(attrs || {}))
      node.setAttribute(key, value);
    if (parent) parent.append(node);
    return node;
  }
  function pointsString(points) {
    return points
      .map((p) =>
        project(p)
          .map((v) => v.toFixed(2))
          .join(","),
      )
      .join(" ");
  }
  function pathString(nodeIds) {
    return nodeIds
      .map(
        (id, i) =>
          `${i ? "L" : "M"}${project(data.nodes[id])
            .map((v) => v.toFixed(2))
            .join(",")}`,
      )
      .join(" ");
  }
  const world = getElement("map-world");
  for (const park of data.parks)
    svg(
      "polygon",
      {
        points: pointsString(park.points),
        fill: park.type === "pitch" ? "#d7e3c5" : "#dce7ce",
        stroke: "#d1dfc2",
        "stroke-width": 1,
      },
      world,
    );
  for (const building of data.buildings)
    svg(
      "polygon",
      {
        points: pointsString(building),
        fill: "#e4e7de",
        stroke: "#dce1d5",
        "stroke-width": 0.8,
      },
      world,
    );
  for (const road of data.roads) {
    const width = ["primary", "secondary", "tertiary"].includes(road.type)
      ? 10
      : road.type === "service"
        ? 4
        : 6.5;
    const points = pointsString(
      road.nodes.map((id) => data.nodes[id]).filter(Boolean),
    );
    svg(
      "polyline",
      {
        points,
        fill: "none",
        stroke: "#dce2d5",
        "stroke-width": width + 2,
        "stroke-linejoin": "round",
        "stroke-linecap": "round",
      },
      world,
    );
    svg(
      "polyline",
      {
        points,
        fill: "none",
        stroke: "#fafbf4",
        "stroke-width": width,
        "stroke-linejoin": "round",
        "stroke-linecap": "round",
      },
      world,
    );
  }
  const labelNames = new Set();
  for (const road of [...data.roads].sort(
    (a, b) => b.nodes.length - a.nodes.length,
  )) {
    if (!road.name || labelNames.has(road.name) || labelNames.size >= 17)
      continue;
    const p = data.nodes[road.nodes[Math.floor(road.nodes.length / 2)]],
      [x, y] = project(p);
    if (x < 100 || x > 900 || y < 100 || y > 700) continue;
    labelNames.add(road.name);
    const label = svg(
      "text",
      { x, y, class: "street-label", "text-anchor": "middle" },
      world,
    );
    label.textContent = road.name;
  }
  const baselinePath = svg(
    "path",
    {
      class: "baseline-line",
      d: pathString(engine.routeNodes(baseline.order, network.paths)),
    },
    world,
  );
  baselinePath.style.display = "none";
  const routeHalo = svg(
    "path",
    {
      fill: "none",
      stroke: "#fcfff4",
      "stroke-width": 8,
      "stroke-linejoin": "round",
      "stroke-linecap": "round",
    },
    world,
  );
  const routePath = svg("path", { class: "route-line" }, world);
  const pinLayer = svg("g", {}, world);
  const [depotX, depotY] = project(data.nodes[data.depot.node]);
  const depot = svg(
    "g",
    { transform: `translate(${depotX},${depotY})` },
    world,
  );
  svg(
    "rect",
    {
      x: -15,
      y: -15,
      width: 30,
      height: 30,
      rx: 9,
      fill: "#3c5f73",
      stroke: "white",
      "stroke-width": 3,
      filter: "url(#pin-shadow)",
    },
    depot,
  );
  svg(
    "path",
    {
      d: "M-7 1V-5H4V1H8V6H-7ZM-4 7h1M5 7h1",
      fill: "none",
      stroke: "white",
      "stroke-width": 1.7,
      "stroke-linecap": "round",
    },
    depot,
  );
  const depotTitle = svg("title", {}, depot);
  depotTitle.textContent = "Örnek araç başlangıcı ve dönüş";
  const pins = bins.map((bin, i) => {
    const [x, y] = project(data.nodes[bin.node]),
      g = svg(
        "g",
        {
          class: "map-pin",
          transform: `translate(${x},${y})`,
          role: "button",
          tabindex: 0,
          "data-bin": bin.id,
        },
        pinLayer,
      );
    svg("circle", { class: "pin-ring", r: 20 }, g);
    const circle = svg("circle", { class: "pin-circle", r: 15 }, g);
    const label = svg("text", { class: "pin-text", x: 0, y: 0 }, g);
    label.textContent = bin.id;
    const fill = svg("text", { class: "pin-percent", x: 0, y: 32 }, g),
      title = svg("title", {}, g);
    g.addEventListener("click", () => selectBin(i));
    g.addEventListener("keydown", (event) => {
      if (["Enter", " "].includes(event.key)) {
        event.preventDefault();
        selectBin(i);
        g.focus();
      }
    });
    return { g, circle, fill, title };
  });
  const initialView = { x: 0, y: 0, w: 1000, h: 800 };
  let view = { ...initialView };
  function updateView() {
    getElement("neighborhood-map").setAttribute(
      "viewBox",
      `${view.x} ${view.y} ${view.w} ${view.h}`,
    );
    const canvas = getElement("map-canvas");
    getElement("scale-bar").style.width =
      `${100 * scale * Math.min(canvas.clientWidth / view.w, canvas.clientHeight / view.h)}px`;
  }
  function zoom(factor) {
    const w = Math.max(260, Math.min(1600, view.w * factor)),
      h = w * 0.8;
    view = { x: view.x + (view.w - w) / 2, y: view.y + (view.h - h) / 2, w, h };
    updateView();
  }
  getElement("zoom-in").onclick = () => zoom(0.75);
  getElement("zoom-out").onclick = () => zoom(1.33);
  getElement("zoom-reset").onclick = () => {
    view = { ...initialView };
    updateView();
  };
  const mapSvg = getElement("neighborhood-map");
  let drag;
  mapSvg.addEventListener("pointerdown", (event) => {
    if (event.target.closest(".map-pin") || event.button !== 0) return;
    drag = { x: event.clientX, y: event.clientY, v: { ...view } };
    mapSvg.setPointerCapture(event.pointerId);
  });
  mapSvg.addEventListener("pointermove", (event) => {
    if (!drag) return;
    const r = mapSvg.getBoundingClientRect(),
      ratio = Math.min(r.width / view.w, r.height / view.h);
    view.x = drag.v.x - (event.clientX - drag.x) / ratio;
    view.y = drag.v.y - (event.clientY - drag.y) / ratio;
    updateView();
  });
  mapSvg.addEventListener("pointerup", () => {
    drag = null;
  });
  mapSvg.addEventListener("pointercancel", () => {
    drag = null;
  });
  window.addEventListener("resize", updateView);
  getElement("baseline-toggle").onchange = (event) => {
    baselinePath.style.display = event.target.checked ? "" : "none";
  };

  function selectBin(index) {
    selected = index;
    getElement("distance-input").value = "";
    getElement("distance-message").textContent =
      "Örnek kalibrasyon: boş 200 cm / dolu 20 cm.";
    getElement("distance-message").classList.remove("error");
    render();
  }
  function updateFill(index, fill, source) {
    bins[index].fill = fill;
    bins[index].updatedAt = new Date().toISOString();
    bins[index].source = source;
    persist();
    render();
  }
  // Ziyaret edilecek kutular aynıysa hesaplanan tur da aynı kalır.
  function planKey() {
    return `${bins.flatMap((b, i) => (collect(b) ? [i + 1] : [])).join(",")}|${threshold}`;
  }
  async function requestPythonPlan(key) {
    if (pythonPendingKey === key) return;
    pythonPendingKey = key;
    const sequence = ++pythonSequence;
    try {
      const response = await fetch("/api/plan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          bins: bins.map(({ id, fill }) => ({ id, fill })),
          threshold,
        }),
        signal: AbortSignal.timeout(7000),
      });
      const result = await response.json();
      if (!response.ok || result.engine !== "python")
        throw new Error(result.error || "Python hesaplaması alınamadı.");
      pythonPlans.set(key, result);
      if (pythonPlans.size > 128)
        pythonPlans.delete(pythonPlans.keys().next().value);
      if (key === planKey()) {
        baseline = { ...result.baseline, engine: "python" };
        baselinePath.setAttribute("d", pathString(result.baseline.pathNodes));
        render();
      }
    } catch (error) {
      if (sequence === pythonSequence) {
        pythonAvailable = false;
        getElement("engine-status").innerHTML = "<i></i> Tarayıcı hesabı";
        toast("Python hesabı alınamadı; tarayıcı hesabıyla devam ediliyor.");
        render();
      }
    } finally {
      if (sequence === pythonSequence) pythonPendingKey = null;
    }
  }
  // Python sunucusu açıksa hesabı oradan al; yoksa tarayıcı motorunu kullan.
  async function detectPython() {
    try {
      const response = await fetch("/api/health", {
        signal: AbortSignal.timeout(2000),
      });
      const health = await response.json();
      pythonAvailable = response.ok && health.engine === "python";
    } catch {
      pythonAvailable = false;
    }
    render();
  }
  function render() {
    const required = bins.flatMap((b, i) => (collect(b) ? [i + 1] : [])),
      key = required.join(",");
    if (!tourCache.has(key)) {
      tourCache.set(
        key,
        engine.planTour(network.matrix, required, baseline.order),
      );
      if (tourCache.size > 120) {
        const first = tourCache.keys().next().value;
        tourCache.delete(first);
      }
    }
    const apiKey = planKey(),
      pythonResult = pythonAvailable ? pythonPlans.get(apiKey) : null;
    current = pythonResult
      ? { ...pythonResult.tour, engine: "python" }
      : tourCache.get(key);
    getElement("engine-status").innerHTML = pythonResult
      ? "<i></i> Python motoru"
      : pythonAvailable
        ? "<i></i> Python hesaplanıyor…"
        : "<i></i> Tarayıcı hesabı";
    if (pythonAvailable && !pythonResult) requestPythonPlan(apiKey);
    const skipped = 20 - required.length,
      saved = Math.max(0, baseline.meters - current.meters),
      gain = baseline.meters ? (100 * saved) / baseline.meters : 0;
    getElement("candidate-count").textContent = required.length;
    getElement("skipped-count").textContent = skipped;
    getElement("saving-percent").textContent = number(gain, 1);
    getElement("saving-meters").textContent =
      `${km(saved)} daha kısa örnek tur`;
    getElement("threshold-caption").textContent =
      `%${percent(threshold)} eşiğinin üzerinde`;
    getElement("collect-tab-count").textContent = required.length;
    getElement("skip-tab-count").textContent = skipped;
    getElement("threshold").value = threshold;
    getElement("baseline-distance").textContent = km(baseline.meters);
    getElement("optimized-distance").textContent = km(current.meters);
    getElement("optimized-stops").textContent =
      `${required.length} toplama durağı`;
    getElement("saved-distance").textContent = km(saved);
    getElement("route-computed-status").textContent = required.length
      ? `Rota güncel · ${current.engine === "python" ? "Python" : "tarayıcı"} hesabı`
      : "Toplama adayı yok · araç çıkışı yok";
    const d = pathString(
      current.pathNodes || engine.routeNodes(current.order, network.paths),
    );
    routePath.setAttribute("d", d);
    routeHalo.setAttribute("d", d);
    pins.forEach((pin, i) => {
      const bin = bins[i],
        yes = collect(bin);
      pin.g.classList.toggle("selected", i === selected);
      pin.circle.setAttribute("fill", yes ? "#d7974e" : "#85a77b");
      pin.fill.textContent = `%${percent(bin.fill)}`;
      pin.g.setAttribute(
        "aria-label",
        `${bin.id}, yüzde ${percent(bin.fill)} dolu, ${yes ? "toplama adayı" : "eşik üzerinde değil"}`,
      );
      pin.g.setAttribute("aria-pressed", i === selected ? "true" : "false");
      pin.title.textContent = `${bin.id} · ${bin.street} · %${percent(bin.fill)}`;
    });
    const bin = bins[selected],
      yes = collect(bin);
    getElement("selected-heading").textContent = bin.id;
    getElement("selected-street").textContent = bin.street;
    getElement("selected-fill").textContent = percent(bin.fill);
    getElement("slider-value").textContent = `%${percent(bin.fill)}`;
    getElement("fill-slider").value = Math.round(bin.fill);
    getElement("fill-slider").setAttribute(
      "aria-valuetext",
      `Yüzde ${percent(bin.fill)} dolu`,
    );
    getElement("selected-status").textContent = yes
      ? "Toplama adayı"
      : "Eşiğin üzerinde değil";
    getElement("selected-status").classList.toggle("skip", !yes);
    getElement("meter-progress").style.stroke = yes ? "#d99b53" : "#85a77b";
    getElement("meter-progress").style.strokeDashoffset =
      458.673 * (1 - bin.fill / 100);
    getElement("selected-coordinates").textContent =
      `${bin.lat.toFixed(5)}, ${bin.lon.toFixed(5)}`;
    getElement("selected-update").textContent = bin.updatedAt
      ? clock(bin.updatedAt)
      : "Örnek konum · sanal veri";
    getElement("route-itinerary").innerHTML =
      current.order.length === 1
        ? '<span class="muted">Bütün kutular eşikte veya altında. Bu tur için araç çıkışına gerek yok.</span>'
        : current.order
            .map(
              (index, i) =>
                `${i ? '<span class="itinerary-arrow" aria-hidden="true">→</span>' : ""}${index === 0 ? '<span class="route-stop depot">Araç noktası</span>' : `<button class="route-stop" data-select="${index - 1}" aria-label="${bins[index - 1].id} kutusunu seç">${bins[index - 1].id}</button>`}`,
            )
            .join("");
    renderTable();
  }
  function renderTable() {
    const visible = bins
      .map((bin, index) => ({ bin, index }))
      .filter(
        ({ bin }) =>
          (filter === "all" ||
            (filter === "collect" ? collect(bin) : !collect(bin))) &&
          `${bin.id} ${bin.street}`.toLocaleLowerCase("tr-TR").includes(search),
      );
    getElement("bins-table").innerHTML = visible
      .map(({ bin, index }) => {
        const yes = collect(bin);
        return `<tr class="${index === selected ? "selected" : ""}" data-select="${index}"><td><span class="bin-id"><span class="bin-dot" aria-hidden="true">▥</span>${esc(bin.id)}</span></td><td>${esc(bin.street)}</td><td class="fill-cell"><div><span class="mini-track"><i class="${yes ? "collect" : ""}" style="width:${bin.fill}%"></i></span><b>%${percent(bin.fill)}</b></div></td><td><span class="status-pill ${yes ? "" : "skip"}"><i></i>${yes ? "Toplama adayı" : "Eşiğin üzerinde değil"}</span></td><td>${esc(clock(bin.updatedAt))}</td><td><button class="row-button" data-select="${index}" aria-label="${esc(bin.id)} kutusunu seç">↗</button></td></tr>`;
      })
      .join("");
    getElement("empty-search").hidden = visible.length > 0;
  }
  document.addEventListener("click", (event) => {
    const element = event.target.closest("[data-select]");
    if (element) {
      selectBin(Number(element.dataset.select));
    }
  });
  getElement("fill-slider").oninput = (event) => {
    updateFill(selected, Number(event.target.value), "slider");
  };
  getElement("empty-bin").onclick = () => {
    updateFill(selected, 0, "manual-empty");
    toast(`${bins[selected].id} boşaltıldı. Rota güncellendi.`);
  };
  async function applyDistance() {
    const raw = getElement("distance-input").value,
      binIndex = selected;
    let distance = engine.parseDistance(raw);
    const message = getElement("distance-message");
    if (distance === null) {
      message.textContent =
        "2–400 cm arası bir sayı veya “Mesafe: 80.0 cm” çıktısı gir.";
      message.classList.add("error");
      return;
    }
    let fill = engine.fillFromDistance(distance);
    if (pythonAvailable) {
      getElement("apply-distance").disabled = true;
      try {
        const response = await fetch("/api/measurement", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ measurement: raw }),
          signal: AbortSignal.timeout(5000),
        });
        const result = await response.json();
        if (!response.ok || result.engine !== "python")
          throw new Error(result.error || "Python ölçümü alınamadı.");
        distance = result.distanceCm;
        fill = result.fillPercent;
      } catch (error) {
        message.textContent = error.message;
        message.classList.add("error");
        return;
      } finally {
        getElement("apply-distance").disabled = false;
      }
    }
    updateFill(
      binIndex,
      fill,
      pythonAvailable ? "manual-tinkercad-python" : "manual-tinkercad",
    );
    if (selected === binIndex) {
      message.textContent = `${number(distance, 1)} cm → %${percent(fill)} doluluk. Rota güncellendi.`;
      message.classList.remove("error");
    }
    toast(`${bins[binIndex].id}: Tinkercad ölçümü elle aktarıldı.`);
  }
  getElement("apply-distance").onclick = applyDistance;
  getElement("distance-input").onkeydown = (event) => {
    if (event.key === "Enter") applyDistance();
  };
  getElement("threshold").onchange = (event) => {
    const n = Number(event.target.value);
    if (
      event.target.value.trim() === "" ||
      !Number.isFinite(n) ||
      n < 0 ||
      n > 100
    ) {
      event.target.value = threshold;
      toast("Eşik 0 ile 100 arasında olmalı.");
      return;
    }
    threshold = n;
    persist();
    render();
  };
  getElement("bin-search").oninput = (event) => {
    search = event.target.value.toLocaleLowerCase("tr-TR");
    renderTable();
  };
  document.querySelectorAll("[data-filter]").forEach(
    (button) =>
      (button.onclick = () => {
        filter = button.dataset.filter;
        document.querySelectorAll("[data-filter]").forEach((b) => {
          b.classList.toggle("active", b === button);
          b.setAttribute("aria-pressed", b === button ? "true" : "false");
        });
        renderTable();
      }),
  );
  function stopSimulation() {
    if (simulation) clearInterval(simulation);
    simulation = null;
    getElement("simulation-button").innerHTML =
      "<span>▶</span> Canlı simülasyon";
    getElement("simulation-button").setAttribute("aria-pressed", "false");
  }
  getElement("simulation-button").onclick = () => {
    if (simulation) {
      stopSimulation();
      toast("Canlı simülasyon durduruldu.");
      return;
    }
    getElement("simulation-button").innerHTML =
      "<span>Ⅱ</span> Simülasyonu durdur";
    getElement("simulation-button").setAttribute("aria-pressed", "true");
    simulation = setInterval(() => {
      const index = (tick * 7) % 20;
      tick++;
      updateFill(
        index,
        Math.min(100, bins[index].fill + 6 + (tick % 4)),
        "simulation",
      );
    }, 3000);
    toast("Sanal ölçümler her 3 saniyede bir güncellenecek.");
  };
  function scenario(value) {
    stopSimulation();
    bins.forEach((b, i) => {
      b.fill = value === "empty" ? 0 : value === "full" ? 100 : initialFills[i];
      b.updatedAt = null;
      b.source = "scenario";
    });
    threshold = 50;
    selected = 0;
    getElement("distance-input").value = "";
    getElement("distance-message").textContent =
      "Örnek kalibrasyon: boş 200 cm / dolu 20 cm.";
    getElement("distance-message").classList.remove("error");
    persist();
    render();
    toast(
      value === "empty"
        ? "Bütün sanal kutular boşaltıldı."
        : value === "full"
          ? "Bütün sanal kutular dolduruldu."
          : "14 aday / 6 düşük doluluk senaryosu yüklendi.",
    );
  }
  getElement("scenario").onchange = (event) => scenario(event.target.value);
  getElement("reset-button").onclick = () => {
    getElement("scenario").value = "default";
    scenario("default");
  };
  getElement("export-button").onclick = () => {
    const payload = {
      project: "Temiz Rota",
      version: 2,
      simulation: true,
      calculationEngine: current.engine || "javascript",
      region: "Gültepe ve çevresi, Altındağ, Ankara",
      exportedAt: new Date().toISOString(),
      source: data.source,
      sourceUrl: data.sourceUrl,
      dataLicense: data.license,
      calibration: { emptyCm: 200, fullCm: 20 },
      collectionThresholdPercent: threshold,
      bins: bins.map((b) => ({ ...b, collectionCandidate: collect(b) })),
      route: {
        algorithm:
          "Çok başlangıçlı en ucuz ekleme ve yönlü maliyetle 2-opt; kesin optimum garantisi yok",
        baselineMeters: baseline.meters,
        selectedMeters: current.meters,
        baselineOrder: baseline.order.map((i) => (i ? bins[i - 1].id : "ARAÇ")),
        selectedOrder: current.order.map((i) => (i ? bins[i - 1].id : "ARAÇ")),
        assumptions:
          "Tek araç; ortak başlangıç/dönüş; kapasite, zaman penceresi, dönüş yasağı ve kamyon kısıtı yok; kutu konumları örnek.",
      },
    };
    const url = URL.createObjectURL(
        new Blob([JSON.stringify(payload, null, 2)], {
          type: "application/json",
        }),
      ),
      link = document.createElement("a");
    link.href = url;
    link.download = "temiz-rota-gultepe-senaryo.json";
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    toast("Senaryo ve rota verileri indirildi.");
  };
  function showMethod() {
    if (!getElement("method-dialog").open)
      getElement("method-dialog").showModal();
  }
  getElement("method-button").onclick = showMethod;
  getElement("help-button").onclick = showMethod;
  getElement("close-dialog").onclick = () =>
    getElement("method-dialog").close();
  getElement("method-dialog").onclick = (event) => {
    if (event.target === getElement("method-dialog")) {
      const r = event.target.getBoundingClientRect();
      if (
        event.clientX < r.left ||
        event.clientX > r.right ||
        event.clientY < r.top ||
        event.clientY > r.bottom
      )
        event.target.close();
    }
  };
  render();
  updateView();
  detectPython();
  window.addEventListener("pagehide", stopSimulation);
  window.TemizRotaDebug = {
    getState: () => ({
      threshold,
      bins: bins.map((b) => ({ ...b })),
      selected,
      current: structuredClone(current),
      baseline: structuredClone(baseline),
    }),
    data,
    network,
  };
})();
