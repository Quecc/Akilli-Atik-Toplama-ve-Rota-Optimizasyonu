# Temiz Rota — Akıllı Atık Toplama ve Rota Optimizasyonu

Temiz Rota, atık toplama araçlarının doluluk verilerine göre ihtiyaç duyulan kutulara yönlendirilmesini amaçlayan akıllı atık yönetimi projesidir. Sensör verileri ve konum bilgileri kullanılarak gereksiz durakların azaltılması, toplama süreçlerinin verimli hâle getirilmesi ve sürdürülebilir şehir uygulamalarına katkı sağlanması hedeflenmektedir.

Projenin fiziksel uygulaması; **Raspberry Pi 4, mesafe sensörleri, GPS ve Wi-Fi/haberleşme modüllerini** bir araya getiren daha kapsamlı bir donanım ve yazılım çalışmasına dayanmaktadır. Bu kapsam, kutu doluluğunun ölçülmesini, konumlandırmayı, verilerin iletilmesini ve toplama rotalarının planlanmasını içermektedir.

**Bu depo, projenin yayımlanmak amacıyla hazırlanan demo sürümünü ve örnek kodlarını içermektedir.** Tinkercad devresi, Python ile doluluk ve rota hesaplama örnekleri ve web paneli üzerinden sistemin temel çalışma mantığı sunulmaktadır. Demo, fiziksel donanım gerektirmeden çalıştırılabilir; kapsamlı fiziksel uygulamanın tüm bileşenlerini içermez.

## Demo nasıl çalışıyor?

Örnek çalışma alanı Ankara, Altındağ'daki **Gültepe Mahallesi ve çevresidir**. Yol ağı OpenStreetMap verilerinden oluşturulmuştur. 20 kutunun konumu, doluluk değerleri ve aracın başlangıç noktası örnek senaryo için tanımlanmıştır.

1. Kutunun üstündeki sensörün ölçtüğü mesafe, yaklaşık doluluk oranına çevrilir.
2. Doluluk **%50'nin üzerindeyse** kutu toplama listesine eklenir.
3. Seçilen kutular için yol ağı üzerinde bir ziyaret sırası hesaplanır.
4. Doluluk değiştiğinde panel ve toplama rotası güncellenir.

Başlangıç senaryosunda **14 kutu toplama adayıdır; 6 kutu atlanır**. Tam %50 dolu bir kutu listeye alınmaz; doluluğun eşik değerinden büyük olması gerekir.

<p align="center">
  <a href="docs/web-paneli.png"><img src="docs/web-paneli.png" alt="Temiz Rota web paneli" width="520"></a>
</p>

<p align="center"><em>Web paneli ön izlemesi — tam boyut için görsele tıklanabilir.</em></p>

## Algoritma akış şeması

Hazırlık, veri kontrolü, doluluk hesabı, kutu seçimi ve rota oluşturma adımları:

[![Temiz Rota algoritma akış şeması](docs/algoritma-akis-semasi.png)](docs/algoritma-akis-semasi.svg)

**[Büyütülebilir SVG](docs/algoritma-akis-semasi.svg) · [PNG](docs/algoritma-akis-semasi.png) · [Düzenlenebilir draw.io dosyası](docs/algoritma-akis-semasi.drawio)**

Şemadaki adımların kod karşılıkları [akış açıklamasında](docs/ALGORITMA.md) yer almaktadır.

## Bilgisayarda çalıştırma

Python 3.10 veya üzeri yeterlidir. Ek Python paketi veya API anahtarı gerekmemektedir.

```sh
git clone https://github.com/Quecc/Akilli-Atik-Toplama-ve-Rota-Optimizasyonu.git
cd Akilli-Atik-Toplama-ve-Rota-Optimizasyonu
python python/run_server.py
```

Uygulamaya tarayıcı üzerinden **[127.0.0.1:4173](http://127.0.0.1:4173)** adresinden erişilebilir. Windows'ta `BASLAT.cmd` dosyasına çift tıklanarak da başlatılabilir.

Üst bölümdeki **“Python motoru”** göstergesi, rota hesabının Python tarafından yapıldığını belirtir. Harita verisi depoda bulunduğundan normal kullanımda internet bağlantısı gerekmez. Sunucu yalnızca uygulamanın çalıştırıldığı bilgisayardan erişilebilen yerel adreste çalışır. Terminalden başlatılan sunucu Ctrl+C ile durdurulabilir.

Port kullanımda ise `python python/run_server.py --port 4174` komutuyla [4174 adresi](http://127.0.0.1:4174) kullanılabilir. `BASLAT.cmd` ile arka planda başlatılan sunucu, Görev Yöneticisi'nde komut satırı `python/run_server.py` olan işlem kapatılarak durdurulabilir.

### Sadece Python ile denemek

Aynı hesap web paneli açılmadan da çalıştırılabilir:

```sh
python python/run_demo.py --output sonuc.json
python python/run_demo.py --distance 80 --bin K03 --output olcum-sonucu.json
```

İlk komut 14 adaylı başlangıç senaryosunu verir. İkinci komut K03'e 80 cm ölçüm uygular: doluluğu yaklaşık %66,7 olur ve aday sayısı 15'e çıkar. Sonuçlar terminale ve belirtilen JSON dosyasına yazılır.

Kod yapısı ve örnek girdiler [Python rehberinde](docs/PYTHON-INCELEME.md) açıklanmaktadır.

## Tinkercad devresi

Fiziksel Arduino gerektirmeden, Tinkercad üzerinde **Arduino Uno + dört pinli HC-SR04** ile mesafe ölçümü denenebilir.

| Sensör pini | Uno bağlantısı |
| --- | --- |
| VCC | 5V |
| GND | GND |
| TRIG | D9 |
| ECHO | D10 |

![Tinkercad devresi](docs/tinkercad-devresi.png)

[Arduino simülasyon kodu](arduino/simulasyon_doluluk/simulasyon_doluluk.ino) · [Tinkercad çalışma bağlantısı](https://www.tinkercad.com/things/7IQvomvfJ6q-shiny-bruticus/editel)

Tinkercad bağlantısı erişim izni gerektirebilir; devre görseli ve örnek kod depoda da bulunmaktadır. **Bu demoda Tinkercad ile panel arasında otomatik bağlantı bulunmamaktadır.** Seri monitördeki değer, seçilen kutunun ölçüm alanına elle girilir. Örnek girdiler: `80`, `80,0` veya `Mesafe: 80.0 cm`.

Demoda boş kutu mesafesi 200 cm, dolu seviye mesafesi 20 cm olarak kabul edilmiştir:

```text
Doluluk = 100 × (200 − mesafe) / (200 − 20)

200 cm → %0
110 cm → %50
 80 cm → yaklaşık %66,7
 20 cm → %100
```

Geçerli ölçümün sonucu %0–100 arasında tutulur. 2–400 cm dışındaki mesafeler ve okunamayan girdiler reddedilir. Hesap, sensörün algıladığı yüzeye göre yaklaşık doluluk verir; düzensiz atıkların gerçek hacmini birebir ölçmez. Fiziksel uygulamada boş ve dolu seviye mesafelerinin kutuya göre kalibre edilmesi gerekir.

## Rota hesabı

Python tarafında yol ağı bir grafik olarak modellenir. **Dijkstra algoritması** ile kutular arasındaki en kısa yol mesafeleri hesaplanır. Ardından **en ucuz ekleme** yöntemiyle kutular tura yerleştirilir; **2-opt** ile ziyaret sırası iyileştirilir. Farklı ilk duraklarla oluşturulan turlar arasından bulunan en kısa tur seçilir.

Tek yönlü yollar hesaba katılır. Yöntem bütün olası turları taramadığından kesin en kısa tur garantisi vermez. Uygulama ayrıntıları [routing.py](python/temiz_rota/routing.py) dosyasında yer almaktadır.

Başlangıç senaryosunda bütün kutuları kapsayan tur yaklaşık **14,55 km**, aday kutuları kapsayan tur **12,53 km** olarak hesaplanır. Bu, örnek senaryoda yaklaşık **%13,9 mesafe kısalmasına** karşılık gelir. Sonuç, saha koşullarında ölçülmüş yakıt veya süre tasarrufu olarak değerlendirilmemelidir. Atlanan bir kutunun bulunduğu sokaktan geçilebilir; ilgili kutuda toplama yapılmaz.

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

24 Python ve 7 JavaScript testi bulunmaktadır. Ölçüm sınırları, %50 kuralı, tek yönlü yollar, boş/dolu senaryoları ve HTTP istekleri kontrol edilir. Python testlerindeki JavaScript karşılaştırması, Node.js kurulu değilse atlanır.

Sonuçlar ve denenen durumlar: [doğrulama kaydı](docs/DOGRULAMA.md). Devreye ait kayıtlar: [Arduino / Tinkercad testleri](docs/ARDUINO-DOGRULAMA.md).

## Demo kapsamı ve geliştirme alanları

Yayımlanan demo, doluluk hesabı ve rota planlama mantığının incelenmesine odaklanmaktadır. Gerçek Raspberry Pi, GPS veya Wi-Fi cihazından canlı veri alımı bu deponun kapsamı dışındadır. Sensör ve konum bilgilerinin otomatik aktarımı, geçmiş ölçümlerin saklanması ve bağlantı yönetimi, kapsamlı donanım ve yazılım entegrasyonunun bileşenleridir.

Geliştirme alanları arasında araç kapasitesi, birden fazla araç ve çalışma saatlerinin rota hesabına eklenmesi bulunmaktadır. Bu demoda trafik, dönüş yasakları ve kamyona özel yol kısıtları uygulanmamaktadır.

Demo sürümünde makine öğrenmesi modeli kullanılmamaktadır. Yeterli ölçüm verisiyle dolma zamanı tahmini yapılması, ileri geliştirme alanlarından biridir.

## Harita verisi

Yollar **© OpenStreetMap contributors**, [ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/) lisansıyla kullanılmaktadır. Çalışma alanı resmî mahalle sınırını, örnek kutular ise belediyenin gerçek envanterini temsil etmemektedir. [Veri kaynağı ve lisans ayrıntıları](data/README.md) ilgili dosyada açıklanmaktadır.

Haritayı yenilemek için `node scripts/refresh-map.mjs` kullanılabilir; internet gerektirir ve JSON / JS veri dosyalarını birlikte günceller. Kaynak kod için ayrıca bir dağıtım lisansı tanımlanmamıştır.

## İletişim

Projenin kapsamı, fiziksel uygulaması ve teknik ayrıntıları hakkında daha detaylı bilgi için e-posta üzerinden iletişime geçilebilir.
