# Öğretmen için Python inceleme rehberi

Bu bölümün amacı Python uygulamasının web görünümünden bağımsız incelenebilmesidir. **Buradaki kod yeniden yazılmış demo kodudur.** Önceki Raspberry Pi/GPS/Wi‑Fi projesinin kaynak dosyaları bulunamadığından o dönemdeki yazılımın aynısı olduğu iddia edilmez.

## Beş dakikada çalıştırma

Komutları deponun ana klasöründe çalıştırın. Python 3.10+ dışında zorunlu bağımlılık yoktur.

```sh
python python/run_tests.py
python python/run_demo.py --output sonuc.json
python python/run_demo.py --distance 80 --bin K03 --output olcum-sonucu.json
python python/run_server.py
```

İlk komut testleri çalıştırır. İkinci komut 14 aday / 6 atlanan durak senaryosunu üretir. Üçüncü komut K03'ün mesafesini 80 cm kabul ederek doluluğunu yaklaşık %66,7 yapar; aday sayısı 15'e çıkar. Son komut [web panelini](http://127.0.0.1:4173) Python çekirdeğine bağlar.

Çalıştırılmış örnek çıktılar da depoda bulunur: [varsayılan senaryo](python-ornek-sonuc.json), [80 cm ölçüm sonrası](python-olcum-sonucu.json), [%100 eşikte boş tur](python-bos-tur.json). Bunlar simülasyon raporlarıdır.

## Okuma sırası

### 1. Sensör verisi: sensor.py

[`Calibration`](../python/temiz_rota/sensor.py) boş/dolu mesafelerini doğrular ve mesafeyi yüzdeye dönüştürür. `parse_distance`, çıplak sayı veya Tinkercad seri satırını okuyabilir. Türkçe ondalık virgülünü destekler. `finite_number`, mantıksal değer, NaN ve sonsuzluğu geçerli ölçüm gibi kabul etmez.

| Girdi | Beklenen sonuç |
| --- | --- |
| 200 cm | %0 |
| 110 cm | %50; varsayılan eşikte aday değil |
| 80 cm | Yaklaşık %66,7; aday |
| 20 cm | %100 |
| 1 cm / 401 cm / hatalı metin | Hata; boş kutu olarak yorumlanmaz |

Kalibrasyon 200/20 cm örnektir. Bu hesap yüzey mesafesinden yaklaşık yükseklik doluluğu çıkarır; düzensiz atığın gerçek hacmini ölçmez. Python bu sürümde GPIO, GPS veya seri port okumaz; yalnızca kendisine verilen örnek ölçümü işler.

### 2. Yol ağı: graph.py

[`build_graph`](../python/temiz_rota/graph.py) OSM yol noktalarını komşuluk listesine dönüştürür. Kenar ağırlıkları metre cinsinden Haversine mesafesidir. Tek yön `yes/1/true`, ters yön `-1` ve çift yön ayrılır.

`dijkstra`, `heapq` öncelik kuyruğu ile negatif olmayan ağırlıklı grafikte en kısa yolu bulur. Ulaşılamayan durak hatadır. `Network.from_map`, başlangıç + 20 kutu için 21×21 mesafe matrisi ve yol düğümlerini hazırlar. Bu veri sunucu açılırken bir kez hesaplanır.

Grafiğin Dijkstra adımı için yaklaşık maliyet `O((V+E) log V)`; 21 başlangıçtan matris hazırlanır. Bu sayı demo ölçeğidir; büyük şehir için ayrıca ölçekleme çalışması gerekir.

### 3. Ziyaret sırası: routing.py

[`plan_tour`](../python/temiz_rota/routing.py), seçili kutulara uğrayıp başlangıca dönen bir tur üretir. Farklı başlangıçlar için en ucuz ekleme denenir; ardından 2-opt iyileştirmesi uygulanır. Yönlü yollarda iki düğüm arasındaki gidiş ve dönüş farklı olabileceğinden, değiştirilen turun **tam yönlü maliyeti** yeniden hesaplanır. İyileştirme en fazla 12 tur sürer.

Bütün kutuların referans turundan yalnızca adaylara indirgenmiş bir başlangıç da denenir. Bu, aynı mesafe matrisinde karşılaştırmayı tutarlı tutar. Dijkstra ilgili noktalar arasındaki en kısa yolu bulur; ziyaret sırası sezgisel bir çözümdür ve **kesin optimum iddiası yoktur**.

### 4. Uygulama kuralları: service.py

[`Planner`](../python/temiz_rota/service.py) veri dosyasını yükler, grafiği ve karşılaştırma turunu hazırlar. `measurement()` ölçümü doğrular. `plan()` bütün kutuların doluluğunu ve eşiği alarak rapor üretir.

- Eşik kuralı kesin olarak `fill > threshold`; eşitlik toplama adayı değildir.
- API'ye tam 20 benzersiz ve bilinen kutu gönderilmelidir. Eksik veya yinelenmiş kayıt reddedilir.
- Doluluk ve eşik %0–100 arasında sonlu sayılar olmalıdır.
- Aynı aday kümesi için tur sonucu sınırlı önbellekte tutulur.
- Raporun `engine: "python"` ve `simulation: true` alanları hesap kaynağını ve demo niteliğini belirtir.
- `order` içindeki `0` araç noktası, `1..20` sırasıyla `K01..K20` kutularıdır. `pathNodes`, çizimde kullanılacak gerçek OSM yol düğümleridir.
- Sonuçtaki UTC zaman damgası **rapor üretim zamanıdır**; gerçek sensörün ölçüm zamanı değildir.

Varsayılan sonuç yaklaşık 14,55 km referans tur, 12,53 km aday tur ve %13,9 mesafe kısalmasıdır. Bunlar yakıt veya süre ölçümü değildir.

### 5. Giriş noktaları ve web bağlantısı

[`run_demo.py`](../python/run_demo.py), `Planner` sınıfını doğrudan kullanır. Tarayıcı, Node.js veya Arduino gerektirmez. `--help` ile seçenekler görülebilir.

[`server.py`](../python/temiz_rota/server.py), standart kütüphanedeki `ThreadingHTTPServer` üzerinde çalışır. `run_server.py` sunucuyu başlatır. Dinleme adresi yalnızca `127.0.0.1`'dir.

| Yol | Yöntem | İşlev |
| --- | --- | --- |
| `/api/health` | GET | Python motorunun hazır olduğunu bildirir |
| `/api/measurement` | POST | `{"measurement":"80,0"}` → yaklaşık %66,7 |
| `/api/plan` | POST | `bins: [{id, fill}, ...]` ve `threshold` → adaylar, tur ve mesafeler |

POST gövdesi JSON olmalıdır. Bilinen yerel origin dışındaki tarayıcı istekleri reddedilir. `.git` gibi gizli dosyalar sunulmaz. Bu yerel demo sunucusu, kimlik doğrulama ve üretim dağıtımı içeren bir servis değildir.

Panelde Python yanıtı alınırken üstte **“Python motoru”** yazısı görülür. Python API yoksa JavaScript alternatifi kullanılır ve hesap kaynağı değiştirilir. Bu nedenle yalnızca panelin açılması Python'un çalıştığına kanıt sayılmaz; motor göstergesi veya `/api/health` yanıtı da kontrol edilmelidir.

## Testlerin kapsamı

[`test_demo.py`](../python/tests/test_demo.py) standart `unittest` kullanır. **24 test** dört gruptadır:

1. Sensör kalibrasyonu, mesafe ayrıştırma ve eşik sınırları.
2. Yönlü grafikte Dijkstra, erişilemeyen yol, asimetrik tur ve boş/tek/tam seçimler.
3. Gerçek demo verisindeki 441 nokta çifti yolunun yönlü kenarlarla ve mesafe matrisiyle uyumu; 14/6 senaryosu; hatalı kayıtlar; JavaScript/Python karşılaştırması.
4. Gerçek yerel HTTP sunucusuna sağlık, ölçüm, planlama, hatalı istek ve gizli dosya erişim denemeleri.

JavaScript karşılaştırması için Node.js gerekir; yoksa yalnızca o test atlanır. Diğer Python testleri ve uygulama bağımsız çalışır. Testlerin geçmesi gerçek sensör, GPS, Wi‑Fi, trafik veya yakıt tasarrufunu doğrulamaz. Çalıştırma kaydı: [DOGRULAMA.md](DOGRULAMA.md).

## İleride eklenecek Python çalışmaları

Gerçek donanım için cihaz okuma, kutuya özel kalibrasyon, zaman damgası, bağlantı ve eskimiş ölçüm yönetimi; ardından veri kaydı ve saha doğrulaması gerekir. Makine öğrenmesiyle dolma zamanı tahmini için önce gerçek geçmiş ölçümler toplanmalıdır. Bunlar bu depoda tamamlanmış özellikler değildir.
