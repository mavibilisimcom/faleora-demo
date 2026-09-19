# Güvenlik tabanı

- Gerçek secrets repoya yazılmaz.
- Staging/production AUTH_SECRET güçlü ve rastgele olmalıdır.
- HTTPS zorunludur.
- Admin ve işletme API'leri rol + venue kapsamıyla korunmalıdır.
- Kritik işlemler: fiyat, indirim, iade, iptal, stok düzeltme, kasa kapanışı ve yetki değişikliği audit üretmelidir.
- Kart verisi FALEORA veritabanında saklanmaz; ödeme sağlayıcısının tokenizasyonu kullanılır.
- Fal, ilişki, günlük ve benzeri özel kullanıcı içerikleri işletme veri alanından ayrılır.
- Production CORS yalnız onaylı origin listesine izin verir.
- Rate limiting ve brute-force koruması edge/API gateway katmanında etkinleştirilmelidir.
