# Migration standardı

Staging ve production üzerinde tablo oluşturmak için uygulama başlangıcındaki create_all çağrıları uzun vadede kullanılmayacaktır. Alembic migration tek kaynak olacaktır.

Komutlar:
- alembic revision --autogenerate -m "schema change"
- alembic upgrade head
- alembic downgrade -1

İlk staging kurulumu öncesi mevcut schema_registry metadata ile konsolide başlangıç revision'ı üretilmeli ve review edilmelidir.
