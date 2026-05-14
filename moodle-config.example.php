<?php
/**
 * Example: Integrate Speaking Avatar into Moodle
 *
 * This file is for reference only. For a proper Moodle plugin,
 * use the local_speakingavatar plugin instead.
 *
 * To use this example:
 * 1. Copy the <style> and <script> sections below
 * 2. Paste into a Custom HTML block, or add to
 *    $CFG->additionalhtmltopofbody in your config.php
 * 3. Update BACKEND to your backend URL
 * 4. Update the script src to your avatar JS path
 *
 * The avatar is zero-UI — you build your own chat interface
 * and control it via the avatar's JavaScript API.
 */

$CFG->additionalhtmltopofbody = <<<'HTML'
<style>
#my-avatar { width: 120px; height: 160px; }
</style>
<script src="/path/to/speaking-avatar.umd.js"></script>
<script>
(function() {
  var BACKEND = 'http://localhost:8000';

  var e = document.createElement('speaking-avatar');
  e.id = 'my-avatar';
  e.setAttribute('tts-api', BACKEND + '/api/v1');
  e.setAttribute('llm-api', BACKEND + '/api/v1/chat/stream');
  e.setAttribute('context', document.title);
  e.style.cssText = 'position:fixed;bottom:20px;right:20px;width:120px;height:160px;z-index:9999;border-radius:12px;background:white;overflow:hidden;display:block;';
  document.body.appendChild(e);

  // ── JavaScript API ──
  // e.speak('Hello!');                         // TTS
  // e.ask('What is a fraction?').then(reply =>  // LLM + TTS via SSE
  //   console.log(reply)
  // );
  // e.listen(audioBlob).then(text => ...);      // STT
  // e.configure({ voice: 'en-US-JennyNeural' });// Config
})();
</script>
HTML;
