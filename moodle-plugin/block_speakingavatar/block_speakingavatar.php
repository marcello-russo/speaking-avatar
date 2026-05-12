<?php

class block_speakingavatar extends block_base {
    public function init() {
        $this->title = get_string('pluginname', 'block_speakingavatar');
    }

    public function get_content() {
        global $COURSE, $PAGE, $CFG;

        if ($this->content !== null) {
            return $this->content;
        }

        $apiurl = get_config('block_speakingavatar', 'api_url') ?: 'http://localhost:8000/api/v1';
        $voice = get_config('block_speakingavatar', 'voice') ?: 'it-IT-ElsaNeural';
        $theme = get_config('block_speakingavatar', 'theme') ?: 'light';
        $avatar = get_config('block_speakingavatar', 'avatar') ?: 'The Coach';
        $cdnjs = get_config('block_speakingavatar', 'cdn_js') ?: 'https://cdn.jsdelivr.net/npm/speaking-avatar@1.0.1/dist/speaking-avatar.umd.js';

        $coursename = $COURSE->fullname ?? '';

        $safe = function($v) { return htmlspecialchars($v, ENT_QUOTES, 'UTF-8'); };
        $bg = $theme === 'dark' ? '#1a1a2e' : '#ffffff';
        $border = $theme === 'dark' ? '#2a2a4a' : '#e2e8f0';

        $uid = uniqid();

        // Inject CDN script + avatar initialization into page footer
        $PAGE->requires->js_call_amd('block_speakingavatar/main', 'init', [
            json_encode([
                'mountId' => 'sa-mount-' . $uid,
                'ttsApi' => $apiurl . '/tts',
                'sttApi' => $apiurl . '/stt',
                'llmApi' => $apiurl . '/chat',
                'voice' => $voice,
                'avatar' => $avatar,
                'themeBg' => $bg,
                'themeBorder' => $border,
                'courseName' => $coursename,
                'cdnJs' => $cdnjs,
            ])
        ]);

        $this->content = new stdClass();
        $this->content->text = '<div id="sa-mount-' . $uid . '"></div>';
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
