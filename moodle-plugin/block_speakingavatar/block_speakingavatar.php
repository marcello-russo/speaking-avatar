<?php
// moodle-plugin/block_speakingavatar/block_speakingavatar.php

class block_speakingavatar extends block_base {
    public function init() {
        $this->title = get_string('pluginname', 'block_speakingavatar');
    }

    public function get_content() {
        global $COURSE, $CFG;

        if ($this->content !== null) {
            return $this->content;
        }

        $apiurl = get_config('block_speakingavatar', 'api_url') ?: 'http://localhost:8000/api/v1';
        $voice = get_config('block_speakingavatar', 'voice') ?: 'it-IT-ElsaNeural';
        $theme = get_config('block_speakingavatar', 'theme') ?: 'light';
        $avatar = get_config('block_speakingavatar', 'avatar') ?: 'The Coach';
        $cdnjs = get_config('block_speakingavatar', 'cdn_js') ?: 'https://cdn.jsdelivr.net/npm/speaking-avatar/dist/speaking-avatar.umd.js';

        $safe_course = htmlspecialchars($coursename, ENT_QUOTES, 'UTF-8');
        $safe_apiurl = htmlspecialchars($apiurl, ENT_QUOTES, 'UTF-8');
        $safe_voice = htmlspecialchars($voice, ENT_QUOTES, 'UTF-8');
        $safe_avatar = htmlspecialchars($avatar, ENT_QUOTES, 'UTF-8');

        $mountid = 'sa-mount-' . uniqid();
        $this->content = new stdClass();
        $this->content->text = '
<div id="' . $mountid . '"></div>
<script src="' . htmlspecialchars($cdnjs, ENT_QUOTES, 'UTF-8') . '"></script>
<script>
(function() {
  var mount = document.getElementById("' . $mountid . '");
  if (!mount) return;

  var el = document.createElement("speaking-avatar");
  el.setAttribute("tts-api", "' . $safe_apiurl . '/tts");
  el.setAttribute("stt-api", "' . $safe_apiurl . '/stt");
  el.setAttribute("llm-api", "' . $safe_apiurl . '/chat");
  el.setAttribute("voice", "' . $safe_voice . '");
  el.setAttribute("avatar", "' . $safe_avatar . '");

  el.style.position = "fixed";
  el.style.bottom = "20px";
  el.style.right = "20px";
  el.style.width = "80px";
  el.style.height = "120px";
  el.style.zIndex = "9999";
  el.style.cursor = "pointer";
  el.style.borderRadius = "12px";
  el.style.boxShadow = "0 4px 20px rgba(0,0,0,0.15)";
  el.style.background = "' . ($theme === 'dark' ? '#1a1a2e' : 'white') . '";
  el.style.transition = "all 0.3s ease";
  el.style.overflow = "hidden";

  var expanded = false;
  el.addEventListener("click", function() {
    expanded = !expanded;
    if (expanded) {
      el.style.width = "360px";
      el.style.height = "500px";
      el.style.borderRadius = "16px";
      if (el.speak) {
        el.speak("Benvenuto al corso ' . addslashes($safe_course) . '! Cosa vuoi studiare?");
      }
    } else {
      el.style.width = "80px";
      el.style.height = "120px";
      el.style.borderRadius = "12px";
    }
  });

  mount.appendChild(el);
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
