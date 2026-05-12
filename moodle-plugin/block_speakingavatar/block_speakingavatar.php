<?php

class block_speakingavatar extends block_base {
    public function init() {
        $this->title = get_string('pluginname', 'block_speakingavatar');
    }

    public function get_content() {
        global $COURSE;

        if ($this->content !== null) {
            return $this->content;
        }

        $apiurl = get_config('block_speakingavatar', 'api_url') ?: 'http://localhost:8000/api/v1';
        $voice = get_config('block_speakingavatar', 'voice') ?: 'it-IT-ElsaNeural';
        $theme = get_config('block_speakingavatar', 'theme') ?: 'light';
        $avatar = get_config('block_speakingavatar', 'avatar') ?: 'The Coach';
        $cdnjs = get_config('block_speakingavatar', 'cdn_js') ?: 'https://cdn.jsdelivr.net/npm/speaking-avatar@1.0.0/dist/speaking-avatar.umd.js';

        $coursename = $COURSE->fullname ?? '';

        $safe = function($v) { return htmlspecialchars($v, ENT_QUOTES, 'UTF-8'); };
        $bg = $theme === 'dark' ? '#1a1a2e' : '#ffffff';
        $txt = $theme === 'dark' ? '#e2e8f0' : '#1e293b';
        $border = $theme === 'dark' ? '#2a2a4a' : '#e2e8f0';

        $uid = uniqid();

        $this->content = new stdClass();
        $this->content->text = '
<div id="sa-root-' . $uid . '">
  <div id="sa-debug-' . $uid . '" style="font-size:11px;color:#64748b;padding:4px;">⏳ caricamento avatar...</div>
  <speaking-avatar
    id="sa-engine-' . $uid . '"
    tts-api="' . $safe($apiurl) . '/tts"
    stt-api="' . $safe($apiurl) . '/stt"
    llm-api="' . $safe($apiurl) . '/chat"
    voice="' . $safe($voice) . '"
    avatar="' . $safe($avatar) . '"
    style="display:none;"
  ></speaking-avatar>

  <div id="sa-panel-' . $uid . '" style="display:none;position:fixed;bottom:190px;right:20px;width:340px;height:400px;z-index:10000;background:' . $bg . ';color:' . $txt . ';border:1px solid ' . $border . ';border-radius:16px;box-shadow:0 8px 32px rgba(0,0,0,.15);flex-direction:column;overflow:hidden;">
    <div style="padding:12px 16px;border-bottom:1px solid ' . $border . ';font-weight:600;font-size:14px;display:flex;justify-content:space-between;">
      <span>AI Tutor</span>
      <span id="sa-indicator-' . $uid . '" style="font-size:12px;font-weight:400;color:#64748b;">🟢 in ascolto</span>
    </div>
    <div id="sa-msgs-' . $uid . '" style="flex:1;overflow-y:auto;padding:12px;display:flex;flex-direction:column;gap:6px;font-size:14px;"></div>
    <form id="sa-form-' . $uid . '" style="display:flex;gap:8px;padding:12px;border-top:1px solid ' . $border . ';margin:0;">
      <input id="sa-input-' . $uid . '" type="text" placeholder="Scrivi un messaggio..." style="flex:1;padding:8px 12px;border:1px solid ' . $border . ';border-radius:8px;font-size:13px;outline:none;background:' . ($theme === 'dark' ? '#12121e' : '#fff') . ';color:' . $txt . ';">
      <button type="submit" style="padding:8px 16px;background:#6366f1;color:white;border:none;border-radius:8px;font-size:13px;cursor:pointer;font-weight:500;">Invia</button>
    </form>
  </div>
</div>

<script src="' . $safe($cdnjs) . '"></script>
<script>
(function() {
  // Wait for the <speaking-avatar> custom element to be defined
  function waitForAvatar(callback, retries) {
    retries = retries || 0;
    if (retries > 50) {
      var d = document.getElementById("sa-debug-' . $uid . '");
      if (d) d.textContent = "❌ Errore: avatar non caricato";
      return;
    }
    if (window.customElements && customElements.get("speaking-avatar")) {
      callback();
    } else {
      setTimeout(function() { waitForAvatar(callback, retries + 1); }, 200);
    }
  }

  waitForAvatar(function() {
    var debug = document.getElementById("sa-debug-' . $uid . '");
    var engine = document.getElementById("sa-engine-' . $uid . '");
    var panel = document.getElementById("sa-panel-' . $uid . '");
    var msgs = document.getElementById("sa-msgs-' . $uid . '");
    var input = document.getElementById("sa-input-' . $uid . '");
    var form = document.getElementById("sa-form-' . $uid . '");
    var indicator = document.getElementById("sa-indicator-' . $uid . '");
    var isOpen = false;

    function addMsg(role, text) {
      var d = document.createElement("div");
      d.textContent = text;
      d.style.cssText = "padding:8px 12px;border-radius:12px;max-width:85%;line-height:1.4;word-wrap:break-word;" +
        (role === "user"
          ? "align-self:flex-end;background:#6366f1;color:white;border-bottom-right-radius:3px;"
          : "align-self:flex-start;background:' . ($theme === 'dark' ? '#1a1a33' : '#f1f3f8') . ';border:1px solid ' . $border . ';border-bottom-left-radius:3px;");
      msgs.appendChild(d);
      msgs.scrollTop = msgs.scrollHeight;
    }

    engine.style.position = "fixed";
    engine.style.bottom = "20px";
    engine.style.right = "20px";
    engine.style.width = "120px";
    engine.style.height = "160px";
    engine.style.zIndex = "9999";
    engine.style.borderRadius = "12px";
    engine.style.cursor = "pointer";
    engine.style.boxShadow = "0 4px 20px rgba(0,0,0,.15)";
    engine.style.background = "' . $bg . '";
    engine.style.overflow = "hidden";
    engine.style.display = "block";

    if (debug) debug.remove();

    function toggle() {
      isOpen = !isOpen;
      panel.style.display = isOpen ? "flex" : "none";
      if (isOpen) {
        addMsg("assistant", "Benvenuto al corso ' . addslashes($coursename) . '! Come posso aiutarti?");
        engine.speak("Benvenuto al corso ' . addslashes($coursename) . '! Come posso aiutarti?");
        input.focus();
      }
    }

    engine.addEventListener("click", function(e) { e.stopPropagation(); toggle(); });

    form.addEventListener("submit", async function(e) {
      e.preventDefault();
      var text = input.value.trim();
      if (!text) return;
      input.value = "";
      addMsg("user", text);
      indicator.textContent = "⏳ sta pensando...";
      try {
        var reply = await engine.ask(text);
        addMsg("assistant", reply);
        indicator.textContent = "🔵 sta parlando...";
      } catch(err) {
        addMsg("assistant", "Errore: " + err.message);
        indicator.textContent = "🔴 errore";
      }
    });

    engine.addEventListener("speechend", function() { indicator.textContent = "🟢 in ascolto"; });
    engine.addEventListener("error", function(e) { indicator.textContent = "🔴 errore"; });
  });
})();
</script>';

        $this->content->footer = '';
        return $this->content;
    }

    public function applicable_formats() {
        return array('course-view' => true, 'site' => false);
    }

    public function has_config() {
        return true;
    }
}
