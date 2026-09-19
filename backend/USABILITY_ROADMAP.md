# Kullanılabilir Ürün Yol Haritası

## A — Repo içinde tamamlanacak
- Auth/session ve rol kapsamı
- Para güvenli checkout kuralları
- Sipariş/KDS durum makinesi
- Modifier/order item bağlantısı
- Reçete -> stok hareket üretimi
- Kasa/payment reconciliation
- Audit otomasyonu
- API tabanlı boş/yükleniyor/hata UI durumları
- TR kaynak + EN/RU sözlük kapsamı
- Integration testleri

## B — Gerçek staging gerektirir
- PostgreSQL instance
- Alembic konsolide migration
- Güçlü AUTH_SECRET / secret manager
- HTTPS staging domain
- Object storage
- Monitoring/error tracking
- Backup/restore drill

## C — Sağlayıcı hesabı gerektirir
- Kart ödeme sandbox
- SMS / WhatsApp / SMTP / Push
- App Store / Google Play hesapları

Repo işi bitmiş görünse bile B ve C doğrulanmadan canlı ürün etiketi kullanılmaz.
