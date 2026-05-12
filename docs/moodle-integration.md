# Moodle Integration — config.php

To integrate Speaking Avatar into Moodle, add this to your Moodle `config.php`:

```php
$CFG->additionalhtmlfooter = '
<div id="sa-mount"></div>
<script src="https://cdn.jsdelivr.net/npm/speaking-avatar@latest/dist/speaking-avatar.umd.js"></script>
<script>
(function() {
  var r=0,m=50,w=setInterval(function(){if(window.customElements&&customElements.get("speaking-avatar")){clearInterval(w);i();}else if(++r>m)clearInterval(w);},200);
  function i(){
    window.__AVATAR_STATIC_BASE__="https://cdn.jsdelivr.net/npm/speaking-avatar@latest/dist/";
    var e=document.createElement("speaking-avatar");
    e.setAttribute("tts-api","http://localhost:8000/api/v1/tts");e.setAttribute("stt-api","http://localhost:8000/api/v1/stt");e.setAttribute("llm-api","http://localhost:8000/api/v1/chat");
    e.style.cssText="position:fixed;bottom:20px;right:20px;width:120px;height:160px;z-index:9999;border-radius:12px;cursor:pointer;box-shadow:0 4px 20px rgba(0,0,0,.15);background:white;overflow:hidden;display:block;";
    var mo=document.getElementById("sa-mount");if(!mo)return;mo.appendChild(e);
    var p=document.createElement("div");
    p.style.cssText="display:none;position:fixed;bottom:190px;right:20px;width:340px;height:400px;z-index:10000;background:white;border:1px solid #e2e8f0;border-radius:16px;box-shadow:0 8px 32px rgba(0,0,0,.15);flex-direction:column;overflow:hidden;";
    p.innerHTML="<div style=\"padding:12px 16px;border-bottom:1px solid #e2e8f0;font-weight:600;font-size:14px;\">AI Tutor <span id=\"sa-i\" style=\"font-size:12px;font-weight:400;color:#64748b;float:right;\">🟢</span></div><div id=\"sa-m\" style=\"flex:1;overflow-y:auto;padding:12px;display:flex;flex-direction:column;gap:6px;font-size:14px;\"></div><form id=\"sa-f\" style=\"display:flex;gap:8px;padding:12px;border-top:1px solid #e2e8f0;margin:0;\"><input id=\"sa-in\" type=\"text\" placeholder=\"Scrivi...\" style=\"flex:1;padding:8px 12px;border:1px solid #e2e8f0;border-radius:8px;font-size:13px;outline:none;\"><button type=\"submit\" style=\"padding:8px 16px;background:#6366f1;color:white;border:none;border-radius:8px;font-size:13px;cursor:pointer;\">Invia</button></form>";
    document.body.appendChild(p);
    var ms=document.getElementById("sa-m"),ip=document.getElementById("sa-in"),f=document.getElementById("sa-f"),ii=document.getElementById("sa-i"),op=false;
    function a(r,t){var d=document.createElement("div");d.textContent=t;d.style.cssText="padding:8px 12px;border-radius:12px;max-width:85%;line-height:1.4;"+(r=="user"?"align-self:flex-end;background:#6366f1;color:white;border-bottom-right-radius:3px;":"align-self:flex-start;background:#f1f3f8;border:1px solid #e2e8f0;border-bottom-left-radius:3px;");ms.appendChild(d);ms.scrollTop=ms.scrollHeight;}
    e.addEventListener("click",function(ev){ev.stopPropagation();op=!op;p.style.display=op?"flex":"none";if(op){a("assistant","Ciao! Come posso aiutarti?");e.speak("Ciao! Come posso aiutarti?");ip.focus();}});
    f.addEventListener("submit",async function(ev){ev.preventDefault();var t=ip.value.trim();if(!t)return;ip.value="";a("user",t);ii.textContent="⏳";try{var r=await e.ask(t);a("assistant",r);ii.textContent="🔵";}catch(err){a("assistant","Errore: "+err.message);ii.textContent="🔴";}});
    e.addEventListener("speechend",function(){ii.textContent="🟢";});
    e.addEventListener("error",function(){ii.textContent="🔴";});
  }
})();
</script>';
```

Make sure to:

1. Delete any existing `additionalhtmlfooter` entries from your Moodle database:
   ```sql
   DELETE FROM mdl_config WHERE name='additionalhtmlfooter';
   DELETE FROM mdl_config_plugins WHERE name='additionalhtmlfooter';
   ```

2. Update the backend URLs (`tts-api`, `stt-api`, `llm-api`) to point to your running backend.

3. Clear Moodle cache: `php admin/cli/purge_caches.php`
