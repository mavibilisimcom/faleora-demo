window.FALEORA_API=localStorage.getItem('faleora_api_url')||'';
window.FaleoraApi={
 configured(){return !!window.FALEORA_API},
 async req(path,opt={}){const token=localStorage.getItem('faleora_token');const headers={'Content-Type':'application/json',...(opt.headers||{})};if(token)headers.Authorization='Bearer '+token;const r=await fetch(window.FALEORA_API+path,{...opt,headers});let data={};try{data=await r.json()}catch{}if(!r.ok)throw new Error(data.detail||('HTTP '+r.status));return data},
 get(path){return this.req(path)},
 post(path,body){return this.req(path,{method:'POST',body:JSON.stringify(body)})}
};