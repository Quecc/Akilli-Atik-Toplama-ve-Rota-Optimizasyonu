# Web paneli doğrulaması — 16 Ekim 2026

## 0.3 sürümü — kod düzenlemesi ve akış şeması

Python'da kutu doğrulama ve tura kutu ekleme adımları ayrı fonksiyonlara alındı. Web dosyalarındaki sıkıştırılmış satırlar açıldı; Dijkstra kuyruğundaki değişken adları netleştirildi. Bu değişikliklerden sonra **24 Python ve 7 JavaScript testi geçti**. Python ve JavaScript'in varsayılan rota sonuçları eşleşti.

Tarayıcıda **8 kontrol geçti**: başlangıç senaryosu, 80 cm ölçüm, tam %50 sınırı, tümü boş, tümü dolu, güncellenen açıklama ve şema bağlantısı, mobil bilgi penceresinin taşmaması ve hata kaydı kontrolü. Sonuçlar [sadelestirme-tarayici-testleri.json](sadelestirme-tarayici-testleri.json) dosyasında. Test için 390 px görünüm seçildi; tarayıcının kullanılabilir içerik genişliği 375 px idi.

[Akış şeması](ALGORITMA.md) SVG ve PNG olarak açılıp metinler ve bağlantılar kontrol edildi. Düzenlenebilir draw.io kaynağı da eklendi. Aşağıdaki kayıtlar önceki sürümlerin doğrulamasını korur.

## Otomatik testler

`python python/run_tests.py`: **24 test geçti, 0 hata, 0 atlanan** (Python 3.14.7; Node.js karşılaştırması da çalıştı).

Python kapsamı: mesafe doğrulama ve kalibrasyon; NaN/sonsuz/hatalı metin; kesin %50 sınırı; yönlü Dijkstra; ulaşılamayan yol; asimetrik/boş/tek/tam tur; eksik veya yinelenmiş kutular; 441 nokta çifti yolunun mevcut yönlü kenarları izlemesi; JSON ve JS harita verilerinin eşitliği ve iki hesap motorunun sonuçlarının uyumu. Gerçek yerel HTTP istekleriyle ölçüm/planlama, hatalı istekler, dış origin ve gizli dosya erişimi de denendi. GET ve HEAD gizli dosya kontrolleri geçti.

`node --test tests/route-engine.test.cjs`: **7 test geçti, 0 hata**.

Kapsam: boş/dolu kalibrasyonu, geçersiz ölçümlerin reddedilmesi, Tinkercad satırının ve Türkçe ondalık ayracının okunması, tek yön ve ters tek yön, 21 nokta arasındaki yolların bağlılığı, her rotanın gerçek yol kenarlarını izlemesi, 14/6 başlangıç senaryosu, bütün durakların birer kez ziyareti, boş/tek durak/tam tur ve tam %50 sınırı.

## Tarayıcı doğrulaması

### Python bağlantısı eklenen 0.2 sürümü

Codex uygulama içi tarayıcısında **13 kontrol geçti**. Kayıt: [python-tarayici-testleri.json](python-tarayici-testleri.json).

- Python motoru göstergesiyle 14 aday / 6 atlanan varsayılan senaryo.
- Python ölçüm API'si üzerinden K03 için 80 cm → yaklaşık %66,7; aday sayısı 15.
- Geçersiz ölçümün doluluğu koruması; 110 cm → tam %50 ve aday sayılmaması.
- Python ile tüm kutular boş / dolu senaryoları; sıfır tur ve referansla eşit tam tur.
- Bilgi penceresinde demo niteliği, önceki donanım kapsamı ve yeniden yazılmış Python açıklaması.
- Dışa aktarılan JSON'da `calculationEngine: "python"`, `simulation: true` ve 20 kutu.
- Senaryo sıfırlanınca eski ölçüm mesajının temizlenmesi. Bu kontrolde bulunan eski mesaj sorunu düzeltildi ve yeniden denendi.
- 390 px görünümde yatay sayfa taşması olmaması.
- Ayrı Node sunucusunda “Tarayıcı hesabı” göstergesi ve JavaScript ile 80 cm aktarımı.
- Python panelinde JavaScript hata kaydı olmaması.

Güncel ekran görüntüleri: [Python paneli](web-paneli.png), [mobil](web-mobil.png). Terminal giriş noktası da ayrı çalıştırıldı: [14 adaylı Python çıktısı](python-ornek-sonuc.json), [K03 ölçümü sonrası 15 adaylı çıktı](python-olcum-sonucu.json), [%100 eşikte 0 adaylı çıktı](python-bos-tur.json).

Bu kontroller yazılım demosuna aittir; gerçek Raspberry Pi, GPS, Wi‑Fi veya sensör iletişimi denenmedi.

### Önceki web sürümünün arayüz kontrolleri

Python bağlantısı eklenmeden önce yerel HTTP sunucusu üzerinde **20 arayüz kontrolü geçti**. Önceki kayıt [tarayici-testleri.json](tarayici-testleri.json) dosyasındadır; aşağıdaki liste o çalıştırmaya aittir.

- Başlangıçta **14 aday / 6 atlanan durak**.
- Haritada K03 seçimi; `Mesafe: 80.0 cm ...` aktarımıyla yaklaşık **%66,7** ve aday sayısının 15'e çıkması.
- Geçersiz girişin mevcut doluluğu koruması.
- 110 cm ölçümünün tam **%50** olması ve toplama adayı sayılmaması.
- Doluluk kaydırıcısının %0 ve %100 uçları.
- Klavyeyle eşik değişimi ve %100 eşiğinde hiç aday olmaması.
- Bütün kutular boşken **0 aday / 20 atlanan / 0 km**.
- Bütün kutular doluyken **20 aday / 0 atlanan**, iki turun aynı mesafede olması.
- Karşılaştırma rotasını açma, harita yakınlaştırma ve sıfırlama.
- Arama ile aday/atlanan filtrelerinin birlikte çalışması.
- Proje açıklaması penceresi.
- Canlı simülasyonun bir sanal ölçüm üretmesi ve durdurulması.
- 20 kutu ve 14 aday içeren JSON dışa aktarımı; [örnek çıktı](ornek-senaryo.json).
- Seçili kutuyu boşaltınca aday sayısının azalması.
- **390 px genişlikte mobil görünüm:** yatay sayfa taşması yok, harita panel içinde kalıyor. Testte görülen harita/tablo taşması CSS ile düzeltildi ve yeniden doğrulandı.

Tarayıcıda JavaScript hata kaydı görülmedi. Masaüstü ve mobil görünüm görüntüleri: [panel](web-paneli.png), [mobil](web-mobil.png).

Yerel sunucunun ana sayfası **HTTP 200** döndürdü. Doğrudan `file:` protokolüyle açılış tarayıcı güvenlik politikası tarafından engellendi; bu yöntem doğrulanmadı ve çalışma yolu olarak yerel HTTP sunucusu seçildi. Windows başlatıcısının PowerShell sözdizimi kontrol edildi; tarayıcı açma adımı otomatik olarak çalıştırılmadı.

## Başlangıç senaryosu sonucu

| Değer | Sonuç |
| --- | --- |
| Sanal kutu | 20 |
| Eşik | %50'nin üzeri |
| Aday / atlanan | 14 / 6 |
| Bütün kutuları ziyaret eden tur | Yaklaşık 14,55 km |
| Seçilmiş kutuların turu | Yaklaşık 12,53 km |
| Senaryodaki kısalma | Yaklaşık 2,02 km / %13,9 |

Sonuçlar bu harita, örnek kutu konumları ve sezgisel rota algoritmasının çıktısıdır. Gerçek kamyon sürüşü, süre veya yakıt ölçümü değildir. Dönüş yasakları, kamyon kısıtları, kapasite ve zaman pencereleri uygulanmadığı için sahada kullanılacak navigasyon rotası olarak değerlendirilmemelidir.

Harita verisinde 258 yol, 1552 yol düğümü, 354 bina geometrisi ve 10 park/bahçe/spor alanı geometrisi bulunur. 20 kutu aynı gidilip dönülebilir yol bileşenine örnek olarak yerleştirilmiştir.

## Arduino doğrulaması ayrı tutulur

Tinkercad'de mesafe ve %37 / %44,6 gibi pozitif doluluklar kullanıcı görüntüleriyle doğrulandı. Seri monitörde %50 üstü `TOPLAMA ADAYI` satırının görüntüsü henüz alınmadı. Web panelindeki eşik testi bu fiziksel/simüle devre testinin yerine geçmez. Arduino ayrıntıları: [ARDUINO-DOGRULAMA.md](ARDUINO-DOGRULAMA.md).
