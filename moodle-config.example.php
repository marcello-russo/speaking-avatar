<?php
unset($CFG);
$CFG = new stdClass();

$CFG->dbtype    = 'mariadb';
$CFG->dblibrary = 'native';
$CFG->dbhost    = 'moodle-db';
$CFG->dbname    = 'moodle';
$CFG->dbuser    = 'moodle';
$CFG->dbpass    = 'moodle_pass';
$CFG->prefix    = 'mdl_';
$CFG->dboptions = array('dbpersist' => false, 'dbsocket' => false);

$CFG->wwwroot   = 'http://localhost:8080';
$CFG->dataroot  = '/var/moodledata';
$CFG->admin     = 'admin';

$CFG->directorypermissions = 02777;
$CFG->lang = 'en';

$CFG->additionalhtmltopofbody = <<<'HTML'
<style>
#sa-engine { width: 120px !important; height: 160px !important; }
@keyframes sa-fade { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }
</style>
<script src="/lib/speakingavatar/speaking-avatar.umd.js"></script>
<script>
(function() {
  var p = window.location.pathname;
  var allowed = p.indexOf('/mod/page/') >= 0 || p.indexOf('/mod/lesson/') >= 0;
  var blocked = p.indexOf('/mod/quiz/') >= 0 || p.indexOf('/mod/assign/') >= 0 || p.indexOf('/course/view.php') >= 0;
  if (!allowed || blocked) return;

  function waitAndInit() {
    if (window.customElements && customElements.get('speaking-avatar')) {
      init();
    } else {
      setTimeout(waitAndInit, 100);
    }
  }
  waitAndInit();

  function init() {
    window.__AVATAR_STATIC_BASE__ = '/lib/speakingavatar';

    var e = document.createElement('speaking-avatar');
    e.id = 'sa-engine';
    e.setAttribute('tts-api', 'http://localhost:8000/api/v1');
    e.setAttribute('stt-api', 'http://localhost:8000/api/v1/stt');
    e.setAttribute('llm-api', 'http://localhost:8000/api/v1/chat');

    // Context: extract page title + optional course name from breadcrumb
    var crumb = document.querySelector('.breadcrumb-item:last-child, .page-header-headings h1, h1');
    var ctx = crumb ? crumb.textContent.trim() : document.title;
    e.setAttribute('context', ctx);

    e.style.cssText = 'position:fixed;bottom:20px;right:20px;width:120px;height:160px;z-index:9999;border-radius:12px;cursor:pointer;box-shadow:0 4px 20px rgba(0,0,0,.15);background:white;overflow:hidden;display:block;transition:width .3s,height .3s;';
    document.body.appendChild(e);

    var p = document.createElement('div');
    p.style.cssText = 'display:none;position:fixed;bottom:190px;right:20px;width:360px;height:440px;z-index:10000;background:white;border:1px solid #e2e8f0;border-radius:16px;box-shadow:0 8px 32px rgba(0,0,0,.12);flex-direction:column;overflow:hidden;';
    p.innerHTML = '<div style="display:flex;align-items:center;justify-content:space-between;padding:14px 16px;border-bottom:1px solid #e2e8f0;"><span style="font-weight:600;font-size:15px;display:flex;align-items:center;gap:6px;">🧑‍🏫 AI Tutor</span><span id="sa-i" style="font-size:12px;color:#64748b;">🟢</span></div><div id="sa-m" style="flex:1;overflow-y:auto;padding:12px 16px;display:flex;flex-direction:column;gap:10px;font-size:14px;"></div><form id="sa-f" style="display:flex;gap:8px;padding:12px 16px;border-top:1px solid #e2e8f0;margin:0;align-items:center;"><button type="button" id="sa-mic" style="width:36px;height:36px;border-radius:50%;border:1px solid #e2e8f0;background:white;cursor:pointer;font-size:16px;display:flex;align-items:center;justify-content:center;flex-shrink:0;" title="Registra">🎤</button><input id="sa-in" type="text" placeholder="Scrivi..." style="flex:1;padding:9px 12px;border:1px solid #e2e8f0;border-radius:8px;font-size:13px;outline:none;"><button type="submit" style="padding:9px 16px;background:#6366f1;color:white;border:none;border-radius:8px;font-size:13px;cursor:pointer;">Invia</button></form>';
    document.body.appendChild(p);

    var ms = document.getElementById('sa-m'), ip = document.getElementById('sa-in'), f = document.getElementById('sa-f'), ii = document.getElementById('sa-i'), mic = document.getElementById('sa-mic');
    var op = false;

    function a(r, t) {
      var ti = new Date(); var ts = String(ti.getHours()).padStart(2,'0') + ':' + String(ti.getMinutes()).padStart(2,'0');
      var d = document.createElement('div');
      d.style.cssText = 'display:flex;flex-direction:column;max-width:85%;animation:sa-fade .25s ease-out;' + (r === 'user' ? 'align-self:flex-end;align-items:flex-end;' : 'align-self:flex-start;align-items:flex-start;');
      d.innerHTML = (r === 'assistant' ? '<span style="font-size:11px;color:#6366f1;margin-bottom:2px;">🧑‍🏫 AI Tutor</span>' : '') + '<div style="padding:10px 14px;border-radius:14px;line-height:1.5;' + (r === 'user' ? 'background:#6366f1;color:white;border-bottom-right-radius:4px;' : 'background:#f1f3f8;border:1px solid #e2e8f0;border-bottom-left-radius:4px;') + '">' + t.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;') + '</div><span style="font-size:10px;color:#94a3b8;margin-top:2px;">' + ts + '</span>';
      ms.appendChild(d);
      ms.scrollTop = ms.scrollHeight;
    }

    e.addEventListener('click', function(ev) {
      ev.stopPropagation();
      op = !op;
      p.style.display = op ? 'flex' : 'none';
      if (op) {
        a('assistant', 'Ciao! Come posso aiutarti?');
        e.speak('Ciao! Come posso aiutarti?').catch(function(err) { console.error('speak error', err); });
        ip.focus();
      }
    });

    // ── Submit (SSE streaming) ──
    f.addEventListener('submit', async function(ev) {
      ev.preventDefault();
      var t = ip.value.trim(); if (!t) return;
      ip.value = ''; a('user', t); ii.textContent = '⏳';

      var mid = 'm-' + Date.now();
      var ts = new Date(); var tm = String(ts.getHours()).padStart(2,'0') + ':' + String(ts.getMinutes()).padStart(2,'0');
      var d = document.createElement('div'); d.id = mid;
      d.style.cssText = 'display:flex;flex-direction:column;max-width:85%;animation:sa-fade .25s ease-out;align-self:flex-start;align-items:flex-start;';
      d.innerHTML = '<span style="font-size:11px;color:#6366f1;">🧑‍🏫</span><div id="' + mid + '-t" style="padding:10px 14px;border-radius:14px;line-height:1.5;background:#f1f3f8;border:1px solid #e2e8f0;border-bottom-left-radius:4px;"></div><span style="font-size:10px;color:#94a3b8;">' + tm + '</span>';
      ms.appendChild(d); ms.scrollTop = ms.scrollHeight;
      var el = document.getElementById(mid + '-t'); var full = '';

      try {
        var res = await fetch('http://localhost:8000/api/v1/chat/stream', {
          method: 'POST', headers: {'Content-Type':'application/json'},
          body: JSON.stringify({ message: t, context: e.getAttribute('context') || '' }),
        });
        var rdr = res.body.getReader(), dec = new TextDecoder(), buf = '';
        while (true) {
          var { done, value } = await rdr.read(); if (done) break;
          buf += dec.decode(value, { stream: true });
          var ls = buf.split('\n'); buf = ls.pop() || '';
          for (var l of ls) {
            if (l.startsWith('data: ')) try {
              var dt = JSON.parse(l.slice(6));
              if (dt.token) { full += dt.token; el.textContent = full; ms.scrollTop = ms.scrollHeight; }
              if (dt.done) { ii.textContent = '🔵'; e.speak(full).catch(function(){}); }
            } catch(e) {}
          }
        }
      } catch(err) { el.textContent = 'Errore: ' + (err.message || err); ii.textContent = '🔴'; }
    });

    e.addEventListener('speechend', function() { ii.textContent = '🟢'; });
    e.addEventListener('error', function() { ii.textContent = '🔴'; });

    // ── STT Live (Web Speech API) ──
    var recognition = null, isListening = false;

    mic.addEventListener('click', function() {
      if (isListening) { if (recognition) recognition.stop(); return; }
      var SR = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (!SR) { mic.textContent = '❌'; setTimeout(function() { mic.textContent = '🎤'; }, 2000); return; }
      recognition = new SR();
      recognition.continuous = true; recognition.interimResults = true; recognition.lang = 'it-IT';
      isListening = true;
      mic.textContent = '🔴'; mic.style.borderColor = '#ef4444'; mic.style.background = '#fef2f2';
      recognition.onresult = function(ev) { ip.value = ev.results[ev.results.length-1][0].transcript; };
      recognition.onend = function() {
        if (isListening) { var txt = ip.value.trim(); if (txt) f.dispatchEvent(new Event('submit')); }
        isListening = false; mic.textContent = '🎤'; mic.style.borderColor = '#e2e8f0'; mic.style.background = 'white';
      };
      recognition.onerror = function() { isListening = false; mic.textContent = '❌'; setTimeout(function() { mic.textContent = '🎤'; }, 2000); };
      recognition.start();
    });
  }
})();
</script>
HTML;

require_once(__DIR__ . '/lib/setup.php');
