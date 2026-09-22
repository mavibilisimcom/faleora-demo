# Canlıya çıkışta dış bağımlılıklar

Repo içinde uygulanabilecek çekirdek fonksiyonlar geliştirilmektedir. Aşağıdakiler gerçek dış ortam/hesap olmadan tamamlanmış sayılamaz:

- PostgreSQL staging sunucusu ve bağlantı bilgisi
- Secret manager / güçlü AUTH_SECRET
- HTTPS staging domain
- Gerçek kart ödeme sandbox hesabı
- Yetkili e-Fatura/e-Arşiv entegratörü hesabı
- SMS / WhatsApp / e-posta / push servis hesapları
- Dosya/object storage
- Monitoring/error tracking
- Backup/restore altyapısı
- Android/iOS signing ve mağaza hesapları

Fiş/fatura fotoğrafı işleme katmanı kullanıcı onaylı taslak üretmelidir; OCR/AI sonucu doğrudan muhasebe kaydı değildir.
