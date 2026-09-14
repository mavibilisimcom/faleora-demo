const byId=x=>document.getElementById(x);
document.addEventListener('DOMContentLoaded',()=>{byId('apiBase').value=localStorage.getItem('faleoraApiBase')||''});
async function testApi(){const v=byId('apiBase').value.trim();if(v)localStorage.setItem('faleoraApiBase',v);try{const d=await notificationApi('/health');byId('apiState').textContent='Backend bağlı: '+d.env+' / '+d.notification_mode}catch(e){byId('apiState').textContent=e.message}}
async function sendCampaign(){const id=Number(byId('campaignId').value);if(!id)return;try{const d=await runCampaignOnBackend(id);byId('campaignState').textContent=JSON.stringify(d)}catch(e){byId('campaignState').textContent=e.message}}
async function loadReport(){const id=Number(byId('campaignId').value);if(!id)return;try{const d=await getCampaignReport(id);byId('report').textContent=JSON.stringify(d,null,2)}catch(e){byId('report').textContent=e.message}}
