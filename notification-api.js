function notificationApiBase(){return (localStorage.getItem('faleoraApiBase')||'').replace(/\/$/,'')}
async function notificationApi(path,options){const base=notificationApiBase();if(!base)throw new Error('API adresi tanımlı değil');const response=await fetch(base+path,options||{});if(!response.ok)throw new Error(await response.text());return response.json()}
async function testNotificationBackend(){const value=document.getElementById('apiBase').value.trim();if(value)localStorage.setItem('faleoraApiBase',value);try{const data=await notificationApi('/health');document.getElementById('backendState').textContent='Bağlı: '+data.env+' / '+data.notification_mode}catch(e){document.getElementById('backendState').textContent='Bağlantı hatası: '+e.message}}
async function sendCampaignToBackend(payload){return notificationApi('/api/notification-campaigns',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)})}
async function runCampaignOnBackend(id){return notificationApi('/api/notification-campaigns/'+id+'/send',{method:'POST'})}
async function getCampaignReport(id){return notificationApi('/api/notification-campaigns/'+id+'/report')}
