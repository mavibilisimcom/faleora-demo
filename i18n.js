(function(){
const D='tr';
const S={
tr:{language:'Dil',turkish:'Türkçe',english:'İngilizce',russian:'Rusça',home:'Ana Sayfa',discover:'Keşfet',life:'Yaşam',oracle:'Kişisel Rehber',places:'Mekânlar',profile:'Profil',business:'İşletme',admin:'Yönetici',rewards:'Ödüller',readers:'Yorumcular',community:'Çevreler',screen:'Ekran',table:'Masa',kitchen:'Mutfak',stock:'Stok',purchasing:'Satın Alma',staff:'Personel',finance:'Finans',reservations:'Rezervasyonlar',delivery:'Paket Servis',settings:'Ayarlar',notifications:'Bildirimler',licenses:'Lisanslar',welcome:'Hoş geldin',today:'Bugün',save:'Kaydet',cancel:'İptal',open:'Aç',close:'Kapat',status:'Durum'},
en:{language:'Language',turkish:'Turkish',english:'English',russian:'Russian',home:'Home',discover:'Discover',life:'Life',oracle:'Oracle',places:'Places',profile:'Profile',business:'Business',admin:'Admin',rewards:'Rewards',readers:'Readers',community:'Circles',screen:'Screen',table:'Table',kitchen:'Kitchen',stock:'Stock',purchasing:'Purchasing',staff:'Staff',finance:'Finance',reservations:'Reservations',delivery:'Delivery',settings:'Settings',notifications:'Notifications',licenses:'Licenses',welcome:'Welcome',today:'Today',save:'Save',cancel:'Cancel',open:'Open',close:'Close',status:'Status'},
ru:{language:'Язык',turkish:'Турецкий',english:'Английский',russian:'Русский',home:'Главная',discover:'Обзор',life:'Жизнь',oracle:'Оракул',places:'Места',profile:'Профиль',business:'Бизнес',admin:'Администратор',rewards:'Награды',readers:'Эксперты',community:'Сообщества',screen:'Экран',table:'Стол',kitchen:'Кухня',stock:'Склад',purchasing:'Закупки',staff:'Персонал',finance:'Финансы',reservations:'Бронирования',delivery:'Доставка',settings:'Настройки',notifications:'Уведомления',licenses:'Лицензии',welcome:'Добро пожаловать',today:'Сегодня',save:'Сохранить',cancel:'Отмена',open:'Открыть',close:'Закрыть',status:'Статус'}
};
function valid(x){return ['tr','en','ru'].includes(x)?x:D}
function lang(){return valid(localStorage.getItem('faleora_lang')||D)}
function t(k){return (S[lang()]&&S[lang()][k])||S.tr[k]||k}
function apply(){
 const l=lang();document.documentElement.lang=l;
 document.querySelectorAll('[data-i18n]').forEach(el=>{const k=el.dataset.i18n;if(S[l][k])el.textContent=S[l][k]});
 document.querySelectorAll('[data-i18n-placeholder]').forEach(el=>{const k=el.dataset.i18nPlaceholder;if(S[l][k])el.placeholder=S[l][k]});
 document.querySelectorAll('[data-lang-current]').forEach(el=>el.textContent=l.toUpperCase());
}
function setLang(l){l=valid(l);localStorage.setItem('faleora_lang',l);document.cookie='faleora_lang='+l+';path=/;max-age=31536000;SameSite=Lax';location.reload()}
function picker(){
 if(document.getElementById('faleora-language'))return;
 const box=document.createElement('div');box.id='faleora-language';box.style.cssText='position:fixed;right:14px;top:14px;z-index:9999';
 box.innerHTML="<select aria-label='Dil' style='background:#17101d;color:#f8f2e8;border:1px solid #e8c77a55;border-radius:999px;padding:8px 12px'><option value='tr'>TR</option><option value='en'>EN</option><option value='ru'>RU</option></select>";
 const s=box.querySelector('select');s.value=lang();s.onchange=()=>setLang(s.value);document.body.appendChild(box)
}
window.FaleoraI18n={t,setLang,getLang:lang,apply};
document.addEventListener('DOMContentLoaded',()=>{if(!localStorage.getItem('faleora_lang'))localStorage.setItem('faleora_lang',D);apply();picker()});
})();