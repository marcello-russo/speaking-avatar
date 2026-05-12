define(['jquery'], function($) {
    return {
        init: function(configStr) {
            var cfg = JSON.parse(configStr);

            // Set static base URL for GLB files (CDN path)
            var cdnBase = cfg.cdnJs.indexOf('/dist/') > 0
                ? cfg.cdnJs.substring(0, cfg.cdnJs.lastIndexOf('/dist/') + 6)
                : '';
            window.__AVATAR_STATIC_BASE__ = cdnBase;

            // Poll for custom element, then init
            var retries = 0;
            var maxRetries = 50;
            var interval = setInterval(function() {
                if (window.customElements && customElements.get('speaking-avatar')) {
                    clearInterval(interval);
                    initAvatar(cfg);
                } else if (++retries > maxRetries) {
                    clearInterval(interval);
                    console.error('[SA] Custom element not defined');
                }
            }, 200);

            // Load CDN script
            var script = document.createElement('script');
            script.src = cfg.cdnJs;
            script.onerror = function() { console.error('[SA] Failed to load', cfg.cdnJs); };
            document.head.appendChild(script);
        }
    };

    function initAvatar(cfg) {
        var engine = document.createElement('speaking-avatar');
        engine.id = 'sa-engine';
        engine.setAttribute('tts-api', cfg.ttsApi);
        engine.setAttribute('stt-api', cfg.sttApi);
        engine.setAttribute('llm-api', cfg.llmApi);
        engine.setAttribute('voice', cfg.voice);
        engine.setAttribute('avatar', cfg.avatar);
        engine.style.cssText = 'position:fixed;bottom:20px;right:20px;width:120px;height:160px;z-index:9999;border-radius:12px;cursor:pointer;box-shadow:0 4px 20px rgba(0,0,0,.15);background:' + cfg.themeBg + ';overflow:hidden;display:none;';

        var mount = document.getElementById(cfg.mountId);
        if (!mount) return;
        mount.appendChild(engine);

        // Show avatar
        engine.style.display = 'block';

        // Chat panel
        var panel = document.createElement('div');
        panel.id = 'sa-panel';
        panel.style.cssText = 'display:none;position:fixed;bottom:190px;right:20px;width:340px;height:400px;z-index:10000;background:' + cfg.themeBg + ';border:1px solid ' + cfg.themeBorder + ';border-radius:16px;box-shadow:0 8px 32px rgba(0,0,0,.15);flex-direction:column;overflow:hidden;';
        panel.innerHTML = ''
            + '<div style="padding:12px 16px;border-bottom:1px solid ' + cfg.themeBorder + ';font-weight:600;font-size:14px;display:flex;justify-content:space-between;">'
            + '<span>AI Tutor</span>'
            + '<span id="sa-indicator" style="font-size:12px;font-weight:400;color:#64748b;">🟢 in ascolto</span></div>'
            + '<div id="sa-msgs" style="flex:1;overflow-y:auto;padding:12px;display:flex;flex-direction:column;gap:6px;font-size:14px;"></div>'
            + '<form id="sa-form" style="display:flex;gap:8px;padding:12px;border-top:1px solid ' + cfg.themeBorder + ';margin:0;">'
            + '<input id="sa-input" type="text" placeholder="Scrivi un messaggio..." style="flex:1;padding:8px 12px;border:1px solid ' + cfg.themeBorder + ';border-radius:8px;font-size:13px;outline:none;">'
            + '<button type="submit" style="padding:8px 16px;background:#6366f1;color:white;border:none;border-radius:8px;font-size:13px;cursor:pointer;font-weight:500;">Invia</button>'
            + '</form>';
        document.body.appendChild(panel);

        var msgs = document.getElementById('sa-msgs');
        var input = document.getElementById('sa-input');
        var form = document.getElementById('sa-form');
        var indicator = document.getElementById('sa-indicator');
        var isOpen = false;

        function addMsg(role, text) {
            var d = document.createElement('div');
            d.textContent = text;
            d.style.cssText = 'padding:8px 12px;border-radius:12px;max-width:85%;line-height:1.4;word-wrap:break-word;'
                + (role === 'user'
                    ? 'align-self:flex-end;background:#6366f1;color:white;border-bottom-right-radius:3px;'
                    : 'align-self:flex-start;background:' + (cfg.themeBg === '#1a1a2e' ? '#1a1a33' : '#f1f3f8') + ';border:1px solid ' + cfg.themeBorder + ';border-bottom-left-radius:3px;');
            msgs.appendChild(d);
            msgs.scrollTop = msgs.scrollHeight;
        }

        engine.addEventListener('click', function(e) {
            e.stopPropagation();
            isOpen = !isOpen;
            panel.style.display = isOpen ? 'flex' : 'none';
            if (isOpen) {
                addMsg('assistant', 'Benvenuto al corso ' + cfg.courseName + '! Come posso aiutarti?');
                engine.speak('Benvenuto al corso ' + cfg.courseName + '! Come posso aiutarti?');
                input.focus();
            }
        });

        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            var text = input.value.trim();
            if (!text) return;
            input.value = '';
            addMsg('user', text);
            indicator.textContent = '⏳ sta pensando...';
            try {
                var reply = await engine.ask(text);
                addMsg('assistant', reply);
                indicator.textContent = '🔵 sta parlando...';
            } catch(err) {
                addMsg('assistant', 'Errore: ' + err.message);
                indicator.textContent = '🔴 errore';
            }
        });

        engine.addEventListener('speechend', function() { indicator.textContent = '🟢 in ascolto'; });
        engine.addEventListener('error', function() { indicator.textContent = '🔴 errore'; });
    }
});
