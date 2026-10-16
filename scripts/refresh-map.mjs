import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const projectRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
await fs.mkdir(path.join(projectRoot, 'work'), {recursive:true});

const bbox = [39.9412, 32.8777, 39.9534, 32.8943];
const query = `[out:json][timeout:40];(way["highway"~"^(residential|unclassified|tertiary|secondary|primary|living_street|service|tertiary_link|secondary_link|primary_link)$"]["access"!~"^(no|private)$"]["motor_vehicle"!~"^(no|private)$"]["motorcar"!~"^(no|private)$"](${bbox.join(',')});way["building"](${bbox.join(',')});way["leisure"~"^(park|garden|pitch)$"](${bbox.join(',')}););out body geom;`;
let raw;
for (const endpoint of ['https://overpass-api.de/api/interpreter', 'https://overpass.kumi.systems/api/interpreter']) {
  try {
    const response = await fetch(endpoint, {method: 'POST', headers: {'Content-Type': 'application/x-www-form-urlencoded', 'User-Agent': 'TemizRota-Educational-Prototype/1.0'}, body: new URLSearchParams({data: query}), signal: AbortSignal.timeout(55000)});
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    raw = await response.json();
    if (!raw.elements?.length) throw new Error('Harita verisi boş');
    raw.sourceEndpoint = endpoint;
    break;
  } catch (error) { console.log(`${endpoint}: ${error.message}`); }
}
if (!raw) throw new Error('Yol verisi alınamadı');
await fs.writeFile(path.join(projectRoot,'work/gultepe-osm-raw.json'), JSON.stringify(raw));
const roads = raw.elements.filter(e => e.type === 'way' && e.tags?.highway && e.geometry?.length > 1);
const buildings = raw.elements.filter(e => e.tags?.building && e.geometry?.length > 2);
const parks = raw.elements.filter(e => e.tags?.leisure && e.geometry?.length > 2);
const nodes = new Map();
const inside = p => p.lat >= bbox[0] && p.lat <= bbox[2] && p.lon >= bbox[1] && p.lon <= bbox[3];
for (const road of roads) road.nodes.forEach((id, i) => { const p = road.geometry[i]; if (p) nodes.set(id, [p.lat, p.lon]); });
const compactRoads = roads.map(r => ({id: r.id, name: r.tags.name || '', type: r.tags.highway, oneway: r.tags.oneway || (r.tags.junction === 'roundabout' ? 'yes' : 'no'), nodes: r.nodes}));
const graph = new Map([...nodes.keys()].map(id => [id, []]));
for (const road of compactRoads) {
  for (let i = 1; i < road.nodes.length; i++) {
    const a = road.nodes[i - 1], b = road.nodes[i];
    if (!nodes.has(a) || !nodes.has(b)) continue;
    if (road.oneway !== '-1') graph.get(a).push(b);
    if (!['yes', '1', 'true'].includes(road.oneway)) graph.get(b).push(a);
  }
}
// Kosaraju: kutuları birbirine gidilip dönülebilen aynı yol bileşeninden seç.
const seen = new Set(), order = [];
function dfs(v) { seen.add(v); for (const n of graph.get(v)) if (!seen.has(n)) dfs(n); order.push(v); }
for (const v of graph.keys()) if (!seen.has(v)) dfs(v);
const reverse = new Map([...nodes.keys()].map(id => [id, []]));
for (const [v, list] of graph) for (const n of list) reverse.get(n).push(v);
seen.clear(); let largest = [];
function collect(v, result) { seen.add(v); result.push(v); for (const n of reverse.get(v)) if (!seen.has(n)) collect(n, result); }
for (const v of order.reverse()) if (!seen.has(v)) { const component = []; collect(v, component); if (component.length > largest.length) largest = component; }
const candidates = largest.filter(id => inside({lat:nodes.get(id)[0],lon:nodes.get(id)[1]}) && graph.get(id).length >= 2);
if (candidates.length < 21) throw new Error(`Yetersiz bağlı yol düğümü: ${candidates.length}`);
const nearest = (lat,lon) => candidates.reduce((best,id) => {
  const p=nodes.get(id), b=nodes.get(best);
  return (p[0]-lat)**2 + ((p[1]-lon)*0.766)**2 < (b[0]-lat)**2 + ((b[1]-lon)*0.766)**2 ? id : best;
}, candidates[0]);
const chosen = [nearest(39.9427,32.8802)];
for (let i = 0; i < 20; i++) {
  let best, score = -1;
  for (const id of candidates) {
    if (chosen.includes(id)) continue;
    const p = nodes.get(id);
    const d = Math.min(...chosen.map(c => {const q=nodes.get(c); return (p[0]-q[0])**2+((p[1]-q[1])*0.766)**2;}));
    if (d > score) { best=id; score=d; }
  }
  chosen.push(best);
}
const fill = [82,65,34,91,56,74,28,88,63,47,95,52,71,16,84,58,67,41,92,22];
const streetFor = id => compactRoads.find(r => r.nodes.includes(id) && r.name)?.name || 'Mahalle içi yol';
const data = {title:'Gültepe Mahallesi', district:'Altındağ', city:'Ankara', center:[39.947273,32.885998], bbox, source:'© OpenStreetMap contributors', license:'ODbL-1.0', sourceUrl:'https://www.openstreetmap.org/copyright', retrievedAt:new Date().toISOString(), osmTimestamp:raw.osm3s?.timestamp_osm_base, query, endpoint:raw.sourceEndpoint, nodes:Object.fromEntries(nodes), roads:compactRoads,
  buildings:buildings.map(b=>b.geometry.map(p=>[p.lat,p.lon])), parks:parks.map(p=>({name:p.tags.name||'',type:p.tags.leisure,points:p.geometry.map(q=>[q.lat,q.lon])})),
  depot:{id:'depot',node:chosen[0],name:'Örnek araç başlangıcı'},
  bins:chosen.slice(1).map((id,i)=>({id:`K${String(i+1).padStart(2,'0')}`,node:id,street:streetFor(id),fill:fill[i],lat:nodes.get(id)[0],lon:nodes.get(id)[1]}))};
await fs.mkdir(path.join(projectRoot,'data'),{recursive:true});
await fs.writeFile(path.join(projectRoot,'data/map-data.js'), 'window.TEMIZ_ROTA_MAP = '+JSON.stringify(data).replace(/</g,'\\u003c')+';\n');
await fs.writeFile(path.join(projectRoot,'data/map-data.json'), JSON.stringify(data)+'\n');
console.log(JSON.stringify({roads:roads.length,nodes:nodes.size,buildings:buildings.length,parks:parks.length,connectedNodes:largest.length,bins:data.bins.length,candidates:data.bins.filter(b=>b.fill>50).length,bytes:JSON.stringify(data).length}));
