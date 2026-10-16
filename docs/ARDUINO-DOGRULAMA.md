# Doğrulama durumu — 15 Ekim 2026

- Hedef: klasik Arduino Uno R3, `arduino:avr:uno`.
- Araç: Arduino CLI 1.5.2-rc.1; Arduino AVR Boards 1.8.8.
- Ek sensör kütüphanesi: yok.
- Teslim edilen `CALIBRATED = false` kodu başarıyla derlendi: 4624 bayt program, 200 bayt global RAM.
- Ayrı bir geçici kopyada yalnızca `CALIBRATED = true` değiştirilerek doluluk hesabı açık sürüm de başarıyla derlendi: 4916 bayt program, 200 bayt global RAM.
- Güncel `simulasyon_doluluk/simulasyon_doluluk.ino` aynı Uno R3 hedefinde başarıyla derlendi: 5016 bayt program, 200 bayt global RAM. Bu sürüm örnek 200/20 cm değerleriyle yüzde hesabını açar ve başlangıçta kodda tanımlı güncel mesafeleri yazar. Değişiklik sonrası derleme başarılıdır; yeni ölçülerle Tinkercad testi kullanıcıdan bekleniyor.
- `--warnings all` kullanıldı. Proje kodunda uyarı bildirilmedi; Arduino çekirdeğinin `new.cpp` dosyasında kullanılmayan `tag` parametreleriyle ilgili dört uyarı oluştu.
- SVG dosyası XML olarak kontrol edildi. Aynı dosyadan üretilen 1200 × 700 PNG açılıp etiketler ve dört bağlantı görsel olarak kontrol edildi.

Derleme kodun Uno R3 için üretilebildiğini gösterir. Fiziksel sensör, gerçek kutuda kalibrasyon, GPS ve Raspberry Pi bağlantısı henüz test edilmedi. R4 veya farklı Uno çeşidinde derleme yapılmadı. Rehberdeki seri çıktı ve yüzde tablosu örnektir; fiziksel ölçüm sonucu değildir.

## Tinkercad'de ilk çalışma — kullanıcı tarafından doğrulandı

Kullanıcı, hedef hareket ettirildiğinde santimetre bilgisinin değiştiğini bildirdi. Gönderdiği [seri monitör görüntüsünde](testler/tinkercad-ilk-olcum.png) yaklaşık 136,1–136,3 cm mesafe, %0,0 doluluk ve `ESIGIN UZERINDE DEGIL` durumu görülüyor. Bu test sırasında örnek boş mesafesi 40 cm olduğundan bu uzak hedefte hesaplanan değerin %0'a sınırlandırılması beklenen davranıştır. Bunlar sanal sensör verileridir.

Bu kanıt Tinkercad'de kodun çalışmasını, mesafe çıktısını ve uzak hedefte %0 sonucunu destekler. Kullanıcının sonraki görüntüsünde 42,2–213,4 cm aralığında örnekler vardı; bu aralıktaki ölçümlerin tümü önceki boş mesafesi olan 40 cm'den büyük olduğundan doluluk %0 kalıyordu. Simülasyonun daha geniş hareket aralığında izlenebilmesi için örnek kutu 200 cm boş / 20 cm dolu olarak güncellendi; hesaplama yöntemi değişmedi.

## Güncel ölçülerle doluluk hesabı — kullanıcı görüntüleriyle doğrulandı

200/20 cm örnek ölçüleriyle gönderilen görüntülerde şu sonuçlar görüldü:

| Sanal mesafe | Seri monitördeki doluluk | Durum | Kanıt |
| --- | --- | --- | --- |
| 208,5 cm | %0,0 | Eşiğin üzerinde değil | [Görüntü](testler/tinkercad-yuzde37.png) |
| 133,4 cm | %37,0 | Eşiğin üzerinde değil | [Görüntü](testler/tinkercad-yuzde37.png) |
| 119,7 cm | %44,6 | Eşiğin üzerinde değil | [Görüntü](testler/tinkercad-yuzde44.png) |

Bu sonuçlar 200 cm boş / 20 cm dolu varsayımıyla kullanılan formül ve %50'nin üzeri kuralıyla uyumludur. Farklı pozitif doluluk seviyeleri artık doğrulanmıştır. %50 üzerindeki `TOPLAMA ADAYI` durumu ve tam doluluk henüz görüntüyle doğrulanmadı.

[Sensörün mesafe etiketi](testler/tinkercad-inc-santimetre.png) `47.1 in / 119.6 cm` gösteriyor. İlk değer inç, ikinci değer santimetredir. Bunlar doluluk yüzdesi değildir. Güncel örnek kutuda %50 yaklaşık 110 cm / 43,3 inç mesafeye karşılık gelir; bu mesafeden daha yakın hedeflerde toplama adayı beklenir.

Sıradaki deneme: 80 cm / yaklaşık 31,5 inç civarında yaklaşık %66,7 ve toplama adayı; 20 cm civarında yaklaşık %100. Eşik sınırına yakın davranış ayrıca incelenecek.
