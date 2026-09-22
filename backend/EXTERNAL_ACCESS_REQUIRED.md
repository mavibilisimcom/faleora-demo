# Dış Erişim Gerektiren Son Kapılar

Repo içindeki çekirdek ve CI işleri dış hesap olmadan ilerletilmiştir. Aşağıdakiler kullanıcı/kurum hesabı gerektirir:

1. Staging hosting hesabı ve PostgreSQL bağlantısı.
2. Staging domain/DNS ve TLS.
3. Secret manager erişimi.
4. Ödeme sağlayıcısı sandbox/production hesabı.
5. Yetkili e-belge entegratörü hesabı.
6. SMTP/SMS/WhatsApp/Push sağlayıcı hesapları.
7. Object/media storage hesabı.
8. Error monitoring hesabı.
9. Android/iOS signing ve mağaza hesapları.

Bu erişimler olmadan ilgili servisler mock/dry-run/connector sınırında kalır; canlı olarak tamamlandı sayılmaz.
