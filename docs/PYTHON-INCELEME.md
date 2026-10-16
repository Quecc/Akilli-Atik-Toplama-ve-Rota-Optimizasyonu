# Python kodları

Python tarafını okuyacaksan şu sırayla ilerlemek daha kolay: **ölçüm → yol ağı → rota → uygulama**. Web paneli bu dosyaların ürettiği sonuçları gösteriyor.

## Hızlı deneme

Komutları projenin ana klasöründe çalıştır:

```sh
python python/run_demo.py --output sonuc.json
python python/run_demo.py --distance 80 --bin K03 --output olcum-sonucu.json
python python/run_tests.py
```

Python 3.10+ yeterli; ek paket gerekmiyor. İlk örnekte 14 kutu seçiliyor. K03'e 80 cm uygulandığında doluluk yaklaşık %66,7 oluyor ve sayı 15'e çıkıyor.

Hazır çıktılar: [14 aday](python-ornek-sonuc.json), [ölçüm sonrası 15 aday](python-olcum-sonucu.json), [%100 eşikte boş tur](python-bos-tur.json).

## 1. Mesafeden doluluğa — sensor.py

[sensor.py](../python/temiz_rota/sensor.py) üç işi yapıyor:

- `parse_distance`: sayı veya Tinkercad satırından mesafeyi okur.
- `Calibration.fill_percent`: mesafeyi yaklaşık doluluğa çevirir.
- `is_collection_candidate`: doluluğun eşikten büyük olup olmadığını kontrol eder.

Boş mesafesi 200 cm, dolu mesafesi 20 cm. Bu değerler gerçek kutuya göre değiştirilmeli.

| Mesafe | Doluluk | %50 eşiğinde |
| --- | --- | --- |
| 200 cm | %0 | Atlanır |
| 110 cm | %50 | Atlanır |
| 80 cm | Yaklaşık %66,7 | Toplanır |
| 20 cm | %100 | Toplanır |

Hatalı metin, sonsuz değer veya sensör aralığı dışındaki ölçüm hata verir. Böyle bir okumayı boş kutu olarak kabul etmiyorum.

## 2. Yolları hazırlama — graph.py

[graph.py](../python/temiz_rota/graph.py) haritadaki noktaları bir komşuluk listesine çeviriyor. Her bağlantının metre cinsinden uzunluğu var. Tek yönlü bir yolda, ters yönde bağlantı eklenmiyor.

`dijkstra`, bir başlangıçtan diğer noktalara en kısa yolu buluyor. Araç noktası ve 20 kutu için bu işlem tekrarlanarak 21 × 21 mesafe tablosu hazırlanıyor. Tablo ve çizimde kullanılacak yol noktaları `Network` içinde tutuluyor.

Bu hazırlık uygulama açılırken bir kez yapılıyor. Kutunun doluluğu değiştiğinde haritanın yeniden indirilmesine gerek yok.

## 3. Ziyaret sırası — routing.py

[routing.py](../python/temiz_rota/routing.py) içinde hesabı adımlara ayırdım:

1. `validate_inputs`: mesafe tablosunu ve kutu numaralarını kontrol eder.
2. `cheapest_insertion`: kalan kutuları, tura en az ek yol getiren konuma ekler.
3. `improve`: sıranın bir bölümünü ters çevirip daha kısa tur arar. Bu adım 2-opt olarak geçiyor.
4. `plan_tour`: farklı ilk durakları dener ve bulunan en iyi turu seçer.

Yollarda gidiş ve dönüş mesafeleri farklı olabildiği için, sıra değişince bütün turun maliyeti tekrar hesaplanıyor. 2-opt en fazla 12 iyileştirme turu deniyor. Referans turdan yalnızca seçili kutuların bırakıldığı bir başlangıç da değerlendiriliyor.

Dijkstra iki nokta arasındaki en kısa yolu bulur. Bütün kutuların en iyi ziyaret sırasını bulmak ise ayrı bir problem; burada kullandığım yöntem kesin optimum garantisi vermez.

## 4. İşlemleri birleştirme — service.py

[Planner](../python/temiz_rota/service.py), diğer dosyaları bir araya getiriyor:

- `initial_bins`: başlangıç doluluklarını getirir.
- `measurement`: tek bir mesafeyi doğrular ve yüzdeye çevirir.
- `validate_bins`: bütün kutuların birer kez ve geçerli dolulukla gönderildiğini kontrol eder.
- `plan`: adayları seçer, turu hesaplar ve sonuçları hazırlar.

Sonuçta `candidateIds` toplanacak, `skippedIds` atlanacak kutuları içerir. `order` içindeki **0 araç noktasıdır**; 1–20 değerleri K01–K20 kutularını gösterir. `pathNodes` ise haritada çizilecek OSM yol noktalarıdır.

`generatedAt` raporun oluşturulma zamanıdır. Demoda gerçek bir cihazın ölçüm zamanını ifade etmez.

## 5. Terminal ve web

[run_demo.py](../python/run_demo.py) doğrudan `Planner` ile çalışır. Tarayıcı gerektirmez.

[server.py](../python/temiz_rota/server.py), aynı hesapları yerel HTTP üzerinden panele açar. Sunucuyu başlatmak için:

```sh
python python/run_server.py
```

[Paneli aç](http://127.0.0.1:4173). Üstte “Python motoru” yazdığında sonuç Python API'sinden gelmiştir.

| API | İşlev |
| --- | --- |
| GET `/api/health` | Sunucunun hazır olduğunu bildirir |
| POST `/api/measurement` | `{"measurement":"80,0"}` girdisinden doluluk hesaplar |
| POST `/api/plan` | `bins: [{id, fill}, ...]` ve `threshold` ile tur hesaplar |

Sunucu yalnızca bu bilgisayardaki `127.0.0.1` adresini dinler. Gerçek GPIO, GPS veya seri port bağlantısı bu sürümde bulunmuyor.

## Testler ve şema

[test_demo.py](../python/tests/test_demo.py) ölçüm, eşik, yönlü yol, ziyaret sırası ve API davranışlarını kontrol ediyor. JavaScript karşılaştırması [python-comparison.cjs](../tests/python-comparison.cjs) dosyasında; Node.js yoksa yalnızca bu kontrol atlanıyor.

[Akış şeması ve kod eşleştirmesi](ALGORITMA.md) · [Test kayıtları](DOGRULAMA.md)
