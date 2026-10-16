const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const E=require('../route-engine.js');
const text=fs.readFileSync(path.join(__dirname,'../data/map-data.js'),'utf8');
const data=JSON.parse(text.slice(text.indexOf('=')+1).trim().replace(/;$/,''));

test('sensör kalibrasyonu ve ölçüm hatası boş kutuyla karışmaz',()=>{
  assert.equal(E.fillFromDistance(200),0);assert.equal(E.fillFromDistance(20),100);
  assert.ok(Math.abs(E.fillFromDistance(80)-66.6666667)<0.0001);
  assert.equal(E.fillFromDistance(110),50);assert.equal(E.fillFromDistance(300),0);
  for(const n of [0,-1,401,NaN,Infinity])assert.equal(E.fillFromDistance(n),null);
  assert.equal(E.fillFromDistance(50,20,200),null);
});
test('Tinkercad cm çıktısı ve Türkçe ondalık ayracı okunur',()=>{
  assert.equal(E.parseDistance('80,5'),80.5);
  assert.equal(E.parseDistance('Mesafe: 119.7 cm | Yaklasik doluluk: %44.6'),119.7);
  for(const v of ['','abc','%70','NaN','0','401','80 in','-1'])assert.equal(E.parseDistance(v),null);
});
test('tek yön ve ters tek yön yol grafiğinde uygulanır',()=>{
  const graph=E.buildGraph({nodes:{1:[39,32],2:[39,32.001],3:[39,32.002]},roads:[{nodes:[1,2],oneway:'yes'},{nodes:[2,3],oneway:'-1'}]});
  assert.deepEqual(graph.get(1).map(x=>x[0]),[2]);assert.deepEqual(graph.get(2),[]);assert.deepEqual(graph.get(3).map(x=>x[0]),[2]);
});
const network=E.makeNetwork(data),full=E.planTour(network.matrix,data.bins.map((_,i)=>i+1));
test('gerçek yol verisindeki 20 sanal kutu birbirine bağlıdır',()=>{
  assert.equal(data.bins.length,20);assert.ok(data.roads.length>20);
  for(let i=0;i<network.points.length;i++)for(let j=0;j<network.points.length;j++){
    assert.ok(Number.isFinite(network.matrix[i][j]));const p=network.paths[i][j];
    assert.equal(p[0],network.points[i]);assert.equal(p.at(-1),network.points[j]);
    let length=0;for(let k=1;k<p.length;k++){const edge=network.graph.get(p[k-1]).find(x=>x[0]===p[k]);assert.ok(edge);length+=edge[1];}
    assert.ok(Math.abs(length-network.matrix[i][j])<0.001);
  }
});
test('başlangıçta 14 toplama adayı ve 6 düşük doluluk bulunur; ziyaretler eksiksizdir',()=>{
  const ids=data.bins.flatMap((b,i)=>b.fill>50?[i+1]:[]);assert.equal(ids.length,14);
  const chosen=E.planTour(network.matrix,ids,full.order);
  assert.equal(chosen.order[0],0);assert.equal(chosen.order.at(-1),0);
  assert.deepEqual(chosen.order.slice(1,-1).sort((a,b)=>a-b),ids);
  assert.ok(chosen.meters<=full.meters+0.001);assert.ok(chosen.meters>0);
});
test('boş tur, tek durak ve tüm kutular durumları geçerli',()=>{
  assert.deepEqual(E.planTour(network.matrix,[]),{order:[0],meters:0});
  const one=E.planTour(network.matrix,[1]);assert.deepEqual(one.order,[0,1,0]);
  assert.ok(Math.abs(one.meters-(network.matrix[0][1]+network.matrix[1][0]))<0.001);
  assert.equal(new Set(full.order.slice(1,-1)).size,20);assert.equal(full.order.length,22);
});
test('eşikteki kutu seçilmez, eşiği aşan seçilir',()=>{
  assert.equal(E.fillFromDistance(110)>50,false);assert.equal(E.fillFromDistance(109)>50,true);
});
