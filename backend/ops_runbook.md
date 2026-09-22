# FALEORA Operasyon Runbook

## Deploy
1. Backend CI yeşil olmalı.
2. Staging readiness kontrolü geçmeli.
3. Veritabanı yedeği alınmalı.
4. Alembic upgrade head çalıştırılmalı.
5. API deploy edilmeli.
6. /health ve /ready doğrulanmalı.
7. Auth -> satış -> KDS -> ödeme -> stok -> kasa smoke testi yapılmalı.

## Rollback
1. Yeni trafik durdurulur.
2. Uygulama önceki image/commit'e döndürülür.
3. Migration geriye uyumlu değilse onaylı downgrade/restore prosedürü uygulanır.
4. Veri kaybı ihtimalinde otomatik işlem yapılmaz; son doğrulanmış backup kullanılır.

## Alarm öncelikleri
P0: ödeme/adisyon veri kaybı, çift tahsilat, veri izolasyonu ihlali.
P1: KDS/checkout/stok senkronizasyonu çalışmıyor.
P2: rapor/bildirim gecikmesi.
