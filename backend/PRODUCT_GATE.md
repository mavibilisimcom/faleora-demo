# FALEORA Kullanılabilir Ürün Kapısı

Bir modül ancak aşağıdaki koşullar sağlandığında "hazır" kabul edilir:

1. Gerçek API ve kalıcı veri modeli vardır.
2. Yetkilendirme kontrolü vardır.
3. Demo sabit verisi yerine API verisi kullanır.
4. Hata/boş/yükleniyor durumları vardır.
5. Uçtan uca otomatik testi vardır.
6. PostgreSQL staging üzerinde migration ile kurulmuştur.
7. Audit gerektiren işlem audit kaydı üretir.
8. TR varsayılan, EN/RU çeviri anahtarları tanımlıdır.
9. Mobil/tablet görünümü test edilmiştir.
10. Pilot ortamda gerçek kullanıcı tarafından denenmiştir.

## P0 Pilot Akışı
Giriş -> Salon -> Masa -> Adisyon -> Modifier -> KDS -> Hazır -> Servis -> Ödeme -> Kasa -> Reçete/Stok -> Reward -> Audit -> Rapor.

Bu zincir gerçek staging üzerinde geçmeden POS için production-ready etiketi kullanılmaz.
