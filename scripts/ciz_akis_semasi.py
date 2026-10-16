"""Akış şemasını SVG ve düzenlenebilir draw.io dosyası olarak üret."""

from html import escape
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
WIDTH, HEIGHT = 3440, 1850
NODES = {}
EDGES = []
COLORS = {
    "process": ("#fff0b3", "#b99a38"),
    "decision": ("#99bafa", "#587dac"),
    "good": ("#c9ead5", "#76a58a"),
    "error": ("#f2b1b5", "#bc777d"),
    "start": ("#ded7fb", "#9c8ec7"),
    "note": ("#f6d8ec", "#c89bb9"),
}


def node(key, x, y, lines, kind="process", width=330, height=96):
    NODES[key] = dict(x=x, y=y, lines=lines, kind=kind, w=width, h=height)


def edge(source, target, points, label="", label_at=None):
    EDGES.append(dict(source=source, target=target, points=points,
                      label=label, label_at=label_at))


def down(source, target, label=""):
    first, last = NODES[source], NODES[target]
    points = [(first["x"], first["y"] + first["h"] / 2),
              (last["x"], last["y"] - last["h"] / 2)]
    edge(source, target, points, label,
         (first["x"] + 40, (points[0][1] + points[-1][1]) / 2))


def next_stage(source, target, gutter):
    first, last = NODES[source], NODES[target]
    edge(source, target, [
        (first["x"] + first["w"] / 2, first["y"]),
        (gutter, first["y"]), (gutter, 235),
        (last["x"], 235), (last["x"], last["y"] - last["h"] / 2),
    ])


# 1. Sabit harita ve yollar, uygulama açılırken hazırlanır.
node("start", 260, 255, ["BAŞLA"], "start", 220, 58)
node("load", 260, 390, ["Haritayı ve 20 kutuyu yükle", "Varsayılan eşik: %50"])
node("graph", 260, 565, ["Yol grafiğini oluştur", "Mesafeleri ve tek yönleri ekle"])
node("dijkstra", 260, 740, ["Dijkstra ile en kısa yolları bul", "Araç + 20 kutu: 21 × 21 matris"])
node("baseline", 260, 915, ["20 kutunun referans turunu", "hesapla ve sakla"])
node("setup_note", 260, 1190, ["Bu hazırlık başlangıçta bir kez yapılır.",
                              "Doluluk değişince yol verisi", "yeniden indirilmez."], "note", 350, 126)
for first, last in [("start", "load"), ("load", "graph"),
                    ("graph", "dijkstra"), ("dijkstra", "baseline")]:
    down(first, last)

# 2. Ölçüm veya sanal doluluk girişi.
node("input", 740, 390, ["Yeni veriyi al", "Tinkercad mesafesi veya", "panelde sanal doluluk"])
node("valid", 740, 590, ["Girdi", "geçerli mi?"], "decision", 250, 140)
node("invalid", 630, 820, ["Hata göster", "Mevcut doluluğu", "koru"], "error", 190, 116)
node("accepted", 850, 820, ["Geçerli veriyi", "işle"], "good", 190, 116)
node("input_note", 740, 1120, ["Mesafe: 2–400 cm", "Doluluk ve eşik: %0–100",
                              "Hatalı veri boş kutu sayılmaz."], "note", 350, 126)
next_stage("baseline", "input", 470)
down("input", "valid")
edge("valid", "invalid", [(615,590),(550,590),(550,762),(630,762)], "Hayır", (572,566))
edge("invalid", "input", [(535,820),(520,820),(520,390),(575,390)])
edge("valid", "accepted", [(740,660),(740,710),(850,710),(850,762)], "Evet", (800,687))

# 3. Mesafe girilmişse yüzde hesaplanır. Kaydırıcı doğrudan yüzde verir.
node("is_distance", 1220, 390, ["Girdi", "mesafe mi?"], "decision", 250, 140)
node("calculate", 1110, 650, ["Mesafeyi doluluğa", "çevir", "Sonucu %0–100", "arasında tut"], width=200, height=126)
node("use_fill", 1330, 650, ["Sanal doluluk", "değerini kullan"], width=200, height=126)
node("update_fill", 1220, 880, ["Seçili kutunun doluluğunu", "güncelle"])
node("formula", 1220, 1170, ["Doluluk = 100 × (200 − cm) / 180",
                           "110 cm → %50   |   80 cm → %66,7",
                           "Örnek kalibrasyon: boş 200 / dolu 20 cm"], "note", 390, 126)
next_stage("accepted", "is_distance", 970)
edge("is_distance", "calculate", [(1220,460),(1220,510),(1110,510),(1110,587)], "Evet", (1110,485))
edge("is_distance", "use_fill", [(1345,390),(1440,390),(1440,550),(1330,550),(1330,587)], "Hayır", (1380,367))
edge("calculate", "update_fill", [(1110,713),(1110,770),(1220,770),(1220,832)])
edge("use_fill", "update_fill", [(1330,713),(1330,770),(1220,770),(1220,832)])

# 4. Bütün kutular eşik kuralından geçirilir.
node("threshold", 1700, 390, ["Her kutu için", "Doluluk > eşik?"], "decision", 270, 150)
node("collect", 1590, 650, ["Toplama listesine", "ekle"], "good", 190, 100)
node("skip", 1810, 650, ["Bu turda", "kutuyu atla"], "error", 190, 100)
node("more_bins", 1700, 880, ["Sıradaki kutu", "var mı?"], "decision", 250, 140)
node("list_ready", 1700, 1100, ["Aday kutu listesini hazırla"])
node("threshold_note", 1700, 1310, ["Tam %50 aday değildir.",
                                  "%50'nin üzeri seçilir.",
                                  "Örnek: 14 aday, 6 atlanan durak."], "note", 350, 126)
next_stage("update_fill", "threshold", 1455)
edge("threshold", "collect", [(1700,465),(1700,520),(1590,520),(1590,600)], "Evet", (1590,497))
edge("threshold", "skip", [(1835,390),(1920,390),(1920,550),(1810,550),(1810,600)], "Hayır", (1870,367))
edge("collect", "more_bins", [(1590,700),(1590,760),(1700,760),(1700,810)])
edge("skip", "more_bins", [(1810,700),(1810,760),(1700,760),(1700,810)])
edge("more_bins", "threshold", [(1575,880),(1480,880),(1480,280),(1700,280),(1700,315)], "Evet", (1520,855))
down("more_bins", "list_ready", "Hayır")

# 5. Aday yoksa araç turu oluşturulmaz.
node("any_candidate", 2180, 390, ["Toplama adayı", "var mı?"], "decision", 250, 140)
node("paths", 2180, 650, ["Hazır mesafe matrisinden", "aday kutuların yollarını al"])
node("zero", 2180, 1040, ["Araç çıkışı yok", "Önerilen tur: 0 km"], "error", 330, 100)
node("path_note", 2180, 1290, ["Yol bilgisi graph.py içinde hazırlanır.",
                              "Bu adımda hazır yollar kullanılır.",
                              "Ulaşılamayan yol hata olarak bildirilir."], "note", 390, 126)
next_stage("list_ready", "any_candidate", 1940)
down("any_candidate", "paths", "Evet")
edge("any_candidate", "zero", [(2055,390),(1980,390),(1980,1040),(2015,1040)], "Hayır", (2010,365))

# 6. Uygulamadaki en ucuz ekleme ve 2-opt döngüleri.
node("first_stop", 2660, 390, ["Bir aday kutuyu", "ilk durak olarak seç"])
node("insert", 2660, 565, ["En ucuz ekleme", "Kutuları en az ek yol getiren", "konumlara yerleştir"], height=116)
node("opt", 2660, 760, ["2-opt: sıra değişikliklerini dene", "En kısa aday turu bul"])
node("better", 2660, 950, ["Tur kısaldı mı", "ve tekrar < 12 mi?"], "decision", 270, 150)
node("keep_change", 2830, 1120, ["Turu güncelle"], "good", 170, 72)
node("save_best", 2660, 1240, ["Bulunan en iyi turu sakla"], height=78)
node("more_first", 2660, 1390, ["Başka ilk durak", "var mı?"], "decision", 250, 130)
next_stage("paths", "first_stop", 2410)
down("first_stop", "insert")
down("insert", "opt")
down("opt", "better")
edge("better", "keep_change", [(2795,950),(2830,950),(2830,1084)], "Evet", (2855,995))
edge("keep_change", "opt", [(2915,1120),(2925,1120),(2925,760),(2825,760)])
down("better", "save_best", "Hayır")
down("save_best", "more_first")
edge("more_first", "first_stop", [(2535,1390),(2465,1390),(2465,285),(2660,285),(2660,342)], "Evet", (2490,1365))

# 7. Sonuç ve yeni veri döngüsü.
node("display", 3140, 390, ["Rotayı haritada göster", "Toplama sırasını yaz"])
node("compare", 3140, 585, ["Referans turla karşılaştır", "Mesafeyi ve kısalma", "yüzdesini göster"])
node("new_data", 3140, 830, ["Yeni ölçüm veya", "senaryo değişti mi?"], "decision", 270, 150)
node("wait", 3140, 1090, ["Yeni işlem bekle"], "start", 250, 66)
node("result_note", 3140, 1310, ["Başlangıç senaryosu: 14 aday",
                                "14,55 km → 12,53 km",
                                "Yaklaşık %13,9 daha kısa yol"], "note", 350, 126)
edge("more_first", "display", [(2660,1455),(2660,1500),(2940,1500),(2940,235),(3140,235),(3140,342)], "Hayır", (2720,1478))
edge("zero", "display", [(2345,1040),(2390,1040),(2390,1580),(3365,1580),(3365,390),(3305,390)], "0 km sonucu", (3100,1555))
down("display", "compare")
down("compare", "new_data")
down("new_data", "wait", "Hayır")
edge("new_data", "input", [(3005,830),(2960,830),(2960,1690),(505,1690),(505,300),(740,300),(740,342)], "Evet • yeniden hesapla", (2760,1665))

STAGES = [
    ("01  HAZIRLIK", "graph.py · Planner.__init__"),
    ("02  VERİ GİRİŞİ", "sensor.py · validate_bins"),
    ("03  DOLULUK", "Calibration.fill_percent"),
    ("04  KUTU SEÇİMİ", "service.py · plan"),
    ("05  YOL BİLGİSİ", "Network.matrix · Network.paths"),
    ("06  ROTA SIRASI", "routing.py · plan_tour"),
    ("07  SONUÇ", "app.js · Python API"),
]


def render_svg():
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">',
        '<title>Temiz Rota algoritma akış şeması</title>',
        '<desc>Ölçüm doğrulama, doluluk, eşik seçimi, Dijkstra ve 2-opt ile toplama turu.</desc>',
        '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse"><path d="M0 0L10 5L0 10Z" fill="#566273"/></marker></defs>',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        '<g font-family="Segoe UI, Arial, sans-serif" fill="#253247">',
        '<text x="60" y="66" font-size="40" font-weight="700">Temiz Rota • Algoritma Akış Şeması</text>',
        '<text x="60" y="105" font-size="23">Gültepe / Ankara · 20 sanal kutu · Python hesap motoru · Demo / simülasyon</text>',
    ]
    for index, (title, source) in enumerate(STAGES):
        x = 60 + index * 480
        parts.append(f'<rect x="{x-8}" y="126" width="416" height="1478" rx="18" fill="#f8fafc" stroke="#e5e9ef"/>')
        parts.append(f'<rect x="{x}" y="138" width="400" height="52" rx="16" fill="#ffe17c" stroke="#b99a38"/>')
        parts.append(f'<text x="{x+200}" y="172" text-anchor="middle" font-size="24" font-weight="700">{escape(title)}</text>')
        parts.append(f'<text x="{x+200}" y="218" text-anchor="middle" font-size="19" fill="#5a6576">{escape(source)}</text>')

    for connection in EDGES:
        points = " ".join(f"{x},{y}" for x, y in connection["points"])
        parts.append(f'<polyline points="{points}" fill="none" stroke="#566273" stroke-width="2.4" stroke-linejoin="round" marker-end="url(#arrow)"/>')

    for item in NODES.values():
        x, y, w, h = item["x"], item["y"], item["w"], item["h"]
        fill, stroke = COLORS[item["kind"]]
        if item["kind"] == "decision":
            points = f"{x},{y-h/2} {x+w/2},{y} {x},{y+h/2} {x-w/2},{y}"
            parts.append(f'<polygon points="{points}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
        else:
            radius = 28 if item["kind"] == "start" else 10
            parts.append(f'<rect x="{x-w/2}" y="{y-h/2}" width="{w}" height="{h}" rx="{radius}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
        font_size = 19 if item["kind"] == "note" else 22
        line_height = 28
        first_line = y - (len(item["lines"])-1)*line_height/2 + 8
        for index, line in enumerate(item["lines"]):
            parts.append(f'<text x="{x}" y="{first_line+index*line_height}" text-anchor="middle" font-size="{font_size}">{escape(line)}</text>')

    for connection in EDGES:
        if connection["label"]:
            x, y = connection["label_at"]
            label = escape(connection["label"])
            width = len(connection["label"]) * 11 + 14
            parts.append(f'<rect x="{x-width/2}" y="{y-20}" width="{width}" height="28" fill="#ffffff" rx="5"/>')
            parts.append(f'<text x="{x}" y="{y}" text-anchor="middle" font-size="20" fill="#4c596c">{label}</text>')

    parts.extend([
        '<text x="60" y="1760" font-size="21">Sarı: işlem   •   Mavi: karar   •   Yeşil: kabul / güncelleme   •   Kırmızı: hata / atlama   •   Pembe: açıklama</text>',
        '<text x="60" y="1793" font-size="19" fill="#5a6576">Tinkercad ölçümü elle aktarılır. 2-opt sezgisel bir iyileştirmedir; kesin optimum garantisi yoktur. Mesafe kısalması, ölçülmüş yakıt tasarrufu değildir.</text>',
        '<text x="60" y="1826" font-size="19" fill="#5a6576">Rota sırasında, referans turdan yalnızca adaylara indirgenmiş bir başlangıç da denenir ve bulunan en iyi sonuç tutulur.</text>',
        '</g></svg>',
    ])
    return "\n".join(parts)


def render_drawio():
    document = ET.Element("mxfile", host="app.diagrams.net")
    diagram = ET.SubElement(document, "diagram", name="Temiz Rota", id="temiz-rota-flow")
    model = ET.SubElement(diagram, "mxGraphModel", page="1", pageWidth=str(WIDTH), pageHeight=str(HEIGHT))
    root = ET.SubElement(model, "root")
    ET.SubElement(root, "mxCell", id="0")
    ET.SubElement(root, "mxCell", id="1", parent="0")

    labels = [
        ("title", "Temiz Rota • Algoritma Akış Şeması", 60, 25, 1700, 60, 36, "none"),
        ("subtitle", "Gültepe / Ankara · 20 sanal kutu · Demo / simülasyon", 60, 85, 1700, 36, 22, "none"),
    ]
    for index, (title, source) in enumerate(STAGES):
        x = 60 + index * 480
        labels.append((f"stage{index}", title, x, 138, 400, 52, 24, "#ffe17c"))
        labels.append((f"source{index}", source, x, 195, 400, 32, 19, "none"))
    for key, value, x, y, w, h, size, color in labels:
        style = f"rounded=1;whiteSpace=wrap;html=0;fillColor={color};strokeColor=none;fontSize={size};fontFamily=Helvetica;"
        cell = ET.SubElement(root, "mxCell", id=key, value=value, style=style, vertex="1", parent="1")
        ET.SubElement(cell, "mxGeometry", x=str(x), y=str(y), width=str(w), height=str(h), attrib={"as":"geometry"})

    for key, item in NODES.items():
        fill, stroke = COLORS[item["kind"]]
        shape = "rhombus" if item["kind"] == "decision" else "rectangle"
        style = f"shape={shape};rounded=1;whiteSpace=wrap;html=0;fillColor={fill};strokeColor={stroke};fontSize=22;fontFamily=Helvetica;"
        cell = ET.SubElement(root, "mxCell", id=key, value="\n".join(item["lines"]),
                             style=style, vertex="1", parent="1")
        ET.SubElement(cell, "mxGeometry", x=str(item["x"]-item["w"]/2),
                      y=str(item["y"]-item["h"]/2), width=str(item["w"]),
                      height=str(item["h"]), attrib={"as":"geometry"})

    for index, connection in enumerate(EDGES):
        source, target = NODES[connection["source"]], NODES[connection["target"]]
        start, end = connection["points"][0], connection["points"][-1]
        exit_x = (start[0] - source["x"] + source["w"]/2) / source["w"]
        exit_y = (start[1] - source["y"] + source["h"]/2) / source["h"]
        entry_x = (end[0] - target["x"] + target["w"]/2) / target["w"]
        entry_y = (end[1] - target["y"] + target["h"]/2) / target["h"]
        style = f"endArrow=block;html=0;strokeColor=#566273;fontSize=19;exitX={exit_x};exitY={exit_y};entryX={entry_x};entryY={entry_y};"
        cell = ET.SubElement(root, "mxCell", id=f"edge{index}", value=connection["label"],
                             style=style, edge="1", parent="1",
                             source=connection["source"], target=connection["target"])
        geometry = ET.SubElement(cell, "mxGeometry", relative="1", attrib={"as":"geometry"})
        points = ET.SubElement(geometry, "Array", attrib={"as":"points"})
        for x, y in connection["points"][1:-1]:
            ET.SubElement(points, "mxPoint", x=str(x), y=str(y))
    return ET.tostring(document, encoding="unicode")


def main():
    folder = ROOT / "docs"
    folder.mkdir(exist_ok=True)
    (folder / "algoritma-akis-semasi.svg").write_text(render_svg(), encoding="utf-8")
    (folder / "algoritma-akis-semasi.drawio").write_text(render_drawio(), encoding="utf-8")
    print("SVG ve draw.io dosyaları docs klasörüne yazıldı.")


if __name__ == "__main__":
    main()
