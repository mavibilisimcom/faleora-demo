# FALEORA Demo Release

FALEORA'nın tamamlanmış online **statik ürün demosu / staging** deposudur. Production veya mağaza yayını değildir.

## Ana girişler
- `release.html` — tüm ürün ailesi ve release hub
- `unified.html` — ana kullanıcı uygulaması
- `life.html` — Personal Universe / retention katmanı
- `premium.html` — premium kullanıcı deneyimleri
- `venues.html` — halka açık partner mekân vitrini
- `business.html` — kafe/restoran işletme paneli
- `growth.html` — Café Growth Engine
- `network.html` — Café Network / partner ve ticari ağ
- `admin.html` — merkez yönetim
- `enterprise.html` — Enterprise Experience OS
- `design-system.html` — tasarım ve motion standardı
- `qa.html` — browser smoke-test merkezi

## Demo özellikleri
Kullanıcı tarafında Today, Journey, Oracle, Life, Twin, Timeline, Memory, Future Me, Passport, Places, cinematic Tarot/Coffee Vision, onboarding, TR/EN/RU dil iskeleti ve privacy-first deneyimler bulunur.

B2B tarafında işletme başvurusu, şube/personel rolleri, kampanya/QR, loyalty, Happy Hours, etkinlikler, Growth Engine, partner/temsilci ağı ve merkez admin konseptleri bulunur.

Enterprise tarafında white-label/co-brand Experience Studio, Dynamic QR/NFC, Digital Cup, Brand Passport, Campaign Orchestrator, Experiment Lab, Store Traffic Optimizer ve entegrasyon mimarisi bulunur.

## Teknik
- GitHub Pages uyumlu statik HTML/CSS/JS
- `manifest.webmanifest` — PWA manifest iskeleti
- `sw.js` — demo offline cache service worker
- `BACKEND_MODEL.md` — production veri modeli taslağı
- `qa.html` / `qa.js` — hızlı smoke tests

## Production sınırı
Gerçek kullanıcı hesabı, kalıcı veritabanı, ödeme/abonelik, gerçek AI servisleri, gerçek QR token doğrulama, POS/CRM entegrasyonu, analytics event pipeline ve push bildirimleri sunucu tarafı altyapı gerektirir. Bu depoda bunlar güvenli demo/simülasyon olarak tutulur.

## Release
Online demo için önerilen ana giriş: `release.html` veya `unified.html`.
