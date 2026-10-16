# Temiz Rota — Akıllı Atık Toplama ve Rota Optimizasyonu

Çöp toplama araçlarının, doluluk durumuna bakmadan her kutuya uğraması yerine ihtiyaç olan kutulara yönelmesini istedim. Bu projedeki amacım, sensörlerden gelen bilgiyle toplama sırasını belirlemek ve gereksiz durakları azaltmak.

Projenin donanımlı çalışmasında Raspberry Pi 4, mesafe sensörü, GPS ve Wi-Fi/haberleşme modülleri kullandık. Bir süre ara verdikten sonra projeyi yeniden ele aldım. **Bu depoda, fiziksel donanım olmadan da denenebilen demo sürümünü paylaşıyorum.** Yazılım bu demo için yeniden hazırlandı; Tinkercad devresi ve bilgisayarda çalışan bir web paneli içeriyor.

## Demo nasıl çalışıyor?

Örnek olarak Ankara, Altındağ'daki **Gültepe Mahallesi ve çevresini** kullandım. Haritadaki yollar OpenStreetMap'ten geliyor. 20 kutunun konumu, dolulukları ve aracın başlangıç noktası ise deneme için oluşturuldu.

1. Kutunun üstündeki sensörün ölçtüğü mesafe, yaklaşık doluluğa çevriliyor.
2. Doluluk **%50'nin üzerindeyse** kutu toplama listesine ekleniyor.
3. Seçilen kutular için yol ağı üzerinde bir ziyaret sırası hesaplanıyor.
4. Doluluk değiştiğinde panel ve toplama rotası güncelleniyor.

Başlangıç senaryosunda **14 kutu toplanacak, 6 kutu atlanacak** şekilde ayarlı. Tam %50 dolu bir kutu listeye girmiyor; eşikten büyük olması gerekiyor.

![Temiz Rota web paneli](docs/web-paneli.png)

## Algoritma akış şeması

Hazırlık, veri kontrolü, doluluk hesabı, kutu seçimi ve rota oluşturma adımları:

[![Temiz Rota algoritma akış şeması](docs/algoritma-akis-semasi.png)](docs/algoritma-akis-semasi.svg)

**[Büyütülebilir SVG](docs/algoritma-akis-semasi.svg) · [PNG](docs/algoritma-akis-semasi.png) · [Düzenlenebilir draw.io dosyası](docs/algoritma-akis-semasi.drawio)**

Şemadaki adımların kodda nereye karşılık geldiği [akış açıklamasında](docs/ALGORITMA.md) bulunuyor.

## Bilgisayarda çalıştırma

Python 3.10 veya üzeri yeterli. Ek Python paketi ya da API anahtarı gerekmiyor.

```sh
git clone https://github.com/Quecc/Akilli-Atik-Toplama-ve-Rota-Optimizasyonu.git
cd Akilli-Atik-Toplama-ve-Rota-Optimizasyonu
python python/run_server.py
```

Ardından tarayıcıda **[127.0.0.1:4173](http://127.0.0.1:4173)** adresini aç. Windows'ta `BASLAT.cmd` dosyasına çift tıklayarak da başlatabilirsin.

Üstte **“Python motoru”** yazıyorsa rota Python tarafından hesaplanıyordur. Harita verisi klasörün içinde olduğu için normal kullanımda internet gerekmez. Sunucu yalnızca kendi bilgisayarından erişilebilen yerel adreste çalışır. Terminalden başlattıysan kapatmak için Ctrl+C kullanabilirsin.

Port doluysa `python python/run_server.py --port 4174` komutunu çalıştırıp [4174 adresini](http://127.0.0.1:4174) aç. `BASLAT.cmd` ile arka planda başlattıysan Görev Yöneticisi'nde komut satırı `python/run_server.py` olan işlemi kapatabilirsin.

### Sadece Python ile denemek

Web panelini açmadan da aynı hesabı çalıştırabilirsin:

```sh
python python/run_demo.py --output sonuc.json
python python/run_demo.py --distance 80 --bin K03 --output olcum-sonucu.json
```

İlk komut 14 adaylı başlangıç senaryosunu verir. İkinci komut K03'e 80 cm ölçüm uygular: doluluğu yaklaşık %66,7 olur ve aday sayısı 15'e çıkar. Sonuçlar terminale ve belirtilen JSON dosyasına yazılır.

Kodun hangi bölümden okunabileceğini ve örnek girişleri [Python rehberinde](docs/PYTHON-INCELEME.md) anlattım.

## Tinkercad devresi

Fiziksel Arduino olmadan, Tinkercad'de **Arduino Uno + dört pinli HC-SR04** ile ölçümü deneyebilirsin.

| Sensör pini | Uno bağlantısı |
| --- | --- |
| VCC | 5V |
| GND | GND |
| TRIG | D9 |
| ECHO | D10 |

![Tinkercad devresi](docs/tinkercad-devresi.png)

[Arduino simülasyon kodu](arduino/simulasyon_doluluk/simulasyon_doluluk.ino) · [Tinkercad çalışma bağlantısı](https://www.tinkercad.com/things/7IQvomvfJ6q-shiny-bruticus/editel)

Tinkercad bağlantısı erişim izni isteyebilir; devre görseli ve kod burada da var. **Tinkercad ile panel arasında otomatik bağlantı kurulu değil.** Seri monitördeki değeri, seçtiğin kutunun ölçüm alanına elle yazıyorsun. Örneğin `80`, `80,0` veya `Mesafe: 80.0 cm`.

Demoda boş kutu mesafesini 200 cm, dolu seviyesini 20 cm kabul ettim:

```text
Doluluk = 100 × (200 − mesafe) / (200 − 20)

200 cm → %0
110 cm → %50
 80 cm → yaklaşık %66,7
 20 cm → %100
```

Geçerli ölçümün sonucu %0–100 arasında tutuluyor. 2–400 cm dışındaki mesafeler ve okunamayan girişler reddediliyor. Bu, sensörün gördüğü yüzeye göre yaklaşık bir doluluk hesabı; düzensiz çöplerin gerçek hacmini birebir ölçmüyor. Gerçek kutuda boş ve dolu mesafelerini ayrıca ayarlamak gerekiyor.

## Rota hesabı

Python tarafında önce yolları bir grafik olarak hazırlıyorum. **Dijkstra**, kutular arasındaki en kısa yol mesafelerini buluyor. Ardından **en ucuz ekleme** yöntemiyle kutular tura yerleştiriliyor; **2-opt** ile ziyaret sırasının daha kısa olup olamayacağı deneniyor. Farklı ilk duraklar arasından bulunan en iyi tur seçiliyor.

Tek yönlü yollar hesaba katılıyor. Bu yöntem bütün olası turları taramadığı için kesin en kısa tur garantisi vermiyor. Ayrıntılı adımlar [routing.py](python/temiz_rota/routing.py) içinde.

Başlangıç örneğinde bütün kutuların turu yaklaşık **14,55 km**, aday kutuların turu **12,53 km** çıkıyor: yaklaşık **%13,9 mesafe kısalması**. Bu, örnek senaryonun sonucu; gerçek yakıt veya süre ölçümü yapmadım. Atlanan bir kutunun bulunduğu sokaktan yine geçilebilir, sadece o kutuda toplama yapılmaz.

## Dosyalar

| Klasör / dosya | İçeriği |
| --- | --- |
| [python/](python/) | Doluluk, yol grafiği, rota hesabı, yerel API ve testler |
| [arduino/](arduino/) | Tinkercad kodu ve fiziksel kurulum için başlangıç örneği |
| [data/](data/) | OSM yol verisi ve 20 örnek kutu |
| [docs/](docs/) | Akış şeması, devre, kod rehberi ve test kayıtları |
| [app.js](app.js) | Web panelinin etkileşimleri |
| [route-engine.js](route-engine.js) | Python açık olmadığında kullanılan tarayıcı hesabı |
| [scripts/](scripts/) | Harita yenileme ve akış şeması üretme araçları |

Python olmadan arayüzü denemek için Node.js 18+ ile `node server.mjs` çalıştırılabilir. Bu durumda üstte “Tarayıcı hesabı” yazar.

## Testler

```sh
python python/run_tests.py
node --test tests/route-engine.test.cjs
```

24 Python ve 7 JavaScript testi bulunuyor. Ölçüm sınırları, %50 kuralı, tek yönlü yollar, boş/dolu senaryoları ve HTTP istekleri kontrol ediliyor. Python testlerindeki JavaScript karşılaştırması, Node.js kurulu değilse atlanır.

Sonuçlar ve denenen durumlar: [doğrulama kaydı](docs/DOGRULAMA.md). Devreye ait kayıtlar: [Arduino / Tinkercad testleri](docs/ARDUINO-DOGRULAMA.md).

## Projenin devamı

Bu sürümde gerçek Raspberry Pi, GPS veya Wi-Fi cihazından veri alınmıyor. Donanımlı sürüme dönerken sensör okumalarını ve konumları otomatik aktarmayı, geçmiş ölçümleri kaydetmeyi ve bağlantı kopmalarını yönetmeyi planlıyorum.

Sonraki adımlarda araç kapasitesi, birden fazla araç ve çalışma saatleri de rota hesabına eklenebilir. Bu demoda trafik, dönüş yasakları ve kamyona özel yol kısıtları uygulanmıyor.

Şu an makine öğrenmesi modeli kullanmıyorum. Yeterli ölçüm biriktikten sonra kutuların ne zaman dolacağını tahmin eden bir bölüm eklemek istiyorum.

## Harita verisi

Yollar **© OpenStreetMap contributors**, [ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/) lisansıyla kullanılıyor. Bu alan resmî mahalle sınırı, kutular da belediyenin gerçek envanteri değil. [Veri kaynağı ve lisans ayrıntıları](data/README.md) dosyada yer alıyor.

Haritayı yenilemek için `node scripts/refresh-map.mjs` kullanılabilir; internet gerektirir ve JSON / JS veri dosyalarını birlikte günceller. Kod için ayrıca bir dağıtım lisansı henüz seçmedim.
