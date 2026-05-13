<?php
/**
 * Example: Integrate Speaking Avatar into Moodle
 *
 * Copy the <script> and <style> sections below into your
 * Moodle config.php's $CFG->additionalhtmltopofbody, or paste
 * them into a Custom HTML block in your course page.
 *
 * Customize:
 *   - BACKEND_URL: replace with your backend address (e.g. "http://localhost:8000")
 *   - /path/to/speaking-avatar.umd.js: path to the built avatar JS
 *   - Voice: change 'it-IT-ElsaNeural' to your preferred Edge TTS voice
 */

$CFG->additionalhtmltopofbody = <<<'HTML'
<style>
#sa-engine { width: 120px !important; height: 160px !important; }
@keyframes sa-fade { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }
</style>
<script src="/path/to/speaking-avatar.umd.js"></script>
<script>
(function() {
  var BACKEND = 'http://localhost:8000';

  // Only show on specific page types — customize as needed
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
    window.__AVATAR_STATIC_BASE__ = window.__AVATAR_STATIC_BASE__ || '';

    var e = document.createElement('speaking-avatar');
    e.id = 'sa-engine';
    e.setAttribute('tts-api', BACKEND + '/api/v1');
    e.setAttribute('stt-api', BACKEND + '/api/v1/stt');
    e.setAttribute('llm-api', BACKEND + '/api/v1/chat/stream');

    // Extract context from page heading
    var crumb = document.querySelector('.breadcrumb-item:last-child, .page-header-headings h1, h1');
    var ctx = crumb ? crumb.textContent.trim() : document.title;
    e.setAttribute('context', ctx);

    e.style.cssText = 'position:fixed;bottom:20px;right:20px;width:120px;height:160px;z-index:9999;border-radius:12px;cursor:pointer;box-shadow:0 4px 20px rgba(0,0,0,.15);background:white;overflow:hidden;display:block;';
    document.body.appendChild(e);

    // ── Chat panel (built-in UI for demo — replace with your own) ──
    var p = document.createElement('div');
    p.style.cssText = 'display:none;position:fixed;bottom:190px;right:20px;width:360px;height:440px;z-index:10000;background:white;border:1px solid #e2e8f0;border-radius:16px;box-shadow:0 8px 32px rgba(0,0,0,.12);flex-direction:column;overflow:hidden;';
    p.innerHTML = [
      '<div style="display:flex;align-items:center;justify-content:space-between;padding:14px 16px;border-bottom:1px solid #e2e8f0;">',
        '<span style="font-weight:600;font-size:15px;">AI Tutor</span>',
        '<span id="sa-i" style="font-size:12px;color:#64748b;">🟢</span>',
      '</div>',
      '<div id="sa-m" style="flex:1;overflow-y:auto;padding:12px 16px;font-size:14px;"></div>',
      '<form id="sa-f" style="display:flex;gap:8px;padding:12px 16px;border-top:1px solid #e2e8f0;margin:0;">',
        '<input id="sa-in" type="text" placeholder="Scrivi..." style="flex:1;padding:9px 12px;border:1px solid #e2e8f0;border-radius:8px;font-size:13px;outline:none;">',
        '<button type="submit" style="padding:9px 16px;background:#6366f1;color:white;border:none;border-radius:8px;font-size:13px;cursor:pointer;">Invia</button>',
      '</form>',
    ].join('');
    document.body.appendChild(p);

    var ms = document.getElementById('sa-m'), ip = document.getElementById('sa-in');
    var f = document.getElementById('sa-f'), ii = document.getElementById('sa-i');
    var op = false;

    function addMessage(role, text) {
      var d = document.createElement('div');
      var align = role === 'user' ? 'flex-end' : 'flex-start';
      var bg = role === 'user' ? '#6366f1;color:white' : '#f1f3f8';
      d.style.cssText = 'display:flex;flex-direction:column;max-width:85%;animation:sa-fade .25s ease-out;align-self:' + align + ';align-items:' + align + ';margin-bottom:8px;';
      d.innerHTML = '<div style="padding:10px 14px;border-radius:14px;line-height:1.5;background:' + bg + '">' + text.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;') + '</div>';
      ms.appendChild(d);
      ms.scrollTop = ms.scrollHeight;
    }

    e.addEventListener('click', function(ev) {
      ev.stopPropagation();
      op = !op;
      p.style.display = op ? 'flex' : 'none';
      if (op) {
        addMessage('assistant', 'Ciao! Come posso aiutarti?');
        e.speak('Ciao! Come posso aiutarti?').catch(function() {});
        ip.focus();
      }
    });

    // ── SSE streaming submit ──
    f.addEventListener('submit', async function(ev) {
      ev.preventDefault();
      var t = ip.value.trim(); if (!t) return;
      ip.value = ''; addMessage('user', t); ii.textContent = '⏳';

      var mid = 'm-' + Date.now();
      var d = document.createElement('div'); d.id = mid;
      d.innerHTML = '<div id="' + mid + '-t" style="padding:10px 14px;border-radius:14px;line-height:1.5;background:#f1f3f8"></div>';
      ms.appendChild(d); ms.scrollTop = ms.scrollHeight;
      var el = document.getElementById(mid + '-t'); var full = '';

      var audioQueue = [], isPlaying = false;
      var audioBuffer = {}, expectedSeq = 0;
      function playNext() {
        if (audioQueue.length === 0) { isPlaying = false; return; }
        isPlaying = true;
        var blob = audioQueue.shift();
        var url = URL.createObjectURL(blob);
        var aud = new Audio(url);
        aud.onended = function() { URL.revokeObjectURL(url); playNext(); };
        aud.play().catch(function() { playNext(); });
      }

      try {
        var res = await fetch(BACKEND + '/api/v1/chat/stream', {
          method: 'POST', headers: {'Content-Type':'application/json'},
          body: JSON.stringify({ message: t, context: e.getAttribute('context') || '' }),
        });
        var rdr = res.body.getReader(), dec = new TextDecoder(), buf = '';
        while (true) {
          var r = await rdr.read(); if (r.done) break;
          buf += dec.decode(r.value, { stream: true });
          for (var l of buf.split('\n').slice(0, -1)) {
            if (!l.startsWith('data: ')) continue;
            try {
              var dt = JSON.parse(l.slice(6));
              if (dt.token !== undefined) { full += dt.token; el.textContent = full; ms.scrollTop = ms.scrollHeight; }
              if (dt.type === 'token') { full += dt.text; el.textContent = full; ms.scrollTop = ms.scrollHeight; }
              if (dt.type === 'audio_complete') {
                (function(b64, seq) {
                  var u = 'data:audio/mpeg;base64,' + b64;
                  fetch(u).then(function(resp) { return resp.blob(); }).then(function(b) {
                    audioBuffer[seq] = b;
                    while (audioBuffer[expectedSeq] !== undefined) {
                      audioQueue.push(audioBuffer[expectedSeq]);
                      delete audioBuffer[expectedSeq];
                      expectedSeq++;
                      if (!isPlaying) playNext();
                    }
                  });
                })(dt.data, dt.seq);
              }
              if (dt.type === 'done') { ii.textContent = '🟢'; }
            } catch(e) {}
          }
          buf = buf.split('\n').pop();
        }
      } catch(err) { el.textContent = 'Errore: ' + (err.message || err); ii.textContent = '🔴'; }
    });

    e.addEventListener('speechend', function() { ii.textContent = '🟢'; });
  }
})();
</script>
HTML;
