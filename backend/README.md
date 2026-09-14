# FALEORA Business Backend

FastAPI tabanlı production backend iskeleti. Bu servis GitHub Pages'ten ayrı çalışır ve lisans, yenileme uyarıları, bildirim logları ve ödeme kayıtlarını kalıcı veritabanında tutar.

## Ana özellikler

- Mekân kaydı
- 7 günlük demo, 6 aylık, 1 yıllık ve 2 yıllık lisanslar
- Lisans uzatma / askıya alma
- `trial → active → grace → expired → suspended` yaşam döngüsü
- 30/15/7/3/1 gün gibi yenileme hatırlatma kuralları
- E-posta / SMS / WhatsApp sağlayıcı adaptörleri
- Dry-run bildirim modu
- Günlük otomatik reminder job
- Bildirim audit kaydı
- Ödeme kaydı ve imzalı webhook doğrulama iskeleti
- CORS ile GitHub Pages frontend bağlantısı

## Çalıştırma

1. Python 3.11+ kullanın.
2. `backend` klasöründe sanal ortam oluşturun.
3. `requirements.txt` bağımlılıklarını kurun.
4. `.env.example` dosyasını `.env` olarak kopyalayıp ortam değişkenlerini doldurun.
5. `uvicorn main:app --host 0.0.0.0 --port 8000` ile başlatın.
6. Sağlık kontrolü: `GET /health`
7. API dokümanı: `/docs`

## Bildirim güvenliği

Varsayılan `NOTIFICATION_MODE=dry_run` gerçek mesaj göndermez. SMTP / SMS / WhatsApp sağlayıcı bilgileri tamamlandıktan sonra `NOTIFICATION_MODE=live` kullanılmalıdır.

Özel fal, Tarot, ilişki veya günlük verileri Business bildirim sistemine aktarılmamalıdır. Lisans sistemi yalnız işletme / abonelik / iletişim verilerini kullanır.

## Ödeme

Varsayılan `PAYMENT_PROVIDER=manual` durumundadır. Gerçek ödeme sağlayıcısı bağlandığında checkout oluşturma ve webhook eşleme katmanı sağlayıcıya özel tamamlanmalıdır. Webhook için `PAYMENT_WEBHOOK_SECRET` tanımlanması önerilir.

## Production notları

- SQLite demo ve tek instance için yeterlidir; production için PostgreSQL önerilir.
- Çoklu worker / çoklu instance kullanılıyorsa APScheduler job'u ayrı worker veya harici cron servisine taşıyın; aksi halde aynı reminder birden fazla instance tarafından tetiklenebilir.
- SMTP/SMS/WhatsApp/ödeme anahtarlarını repoya commit etmeyin.
- HTTPS zorunlu olmalıdır.
- Admin endpointleri production'da JWT/RBAC ile korunmalıdır.
- `notification_logs` ve ödeme webhookları için merkezi audit log tutulmalıdır.
