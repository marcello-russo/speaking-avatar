<?php
if ($hassiteconfig) {
    $settings = new admin_settingpage('block_speakingavatar', get_string('pluginname', 'block_speakingavatar'));

    $settings->add(new admin_setting_configtext('block_speakingavatar/api_url',
        get_string('api_url', 'block_speakingavatar'),
        get_string('api_url_desc', 'block_speakingavatar'),
        'http://localhost:8000/api/v1', PARAM_URL));

    $settings->add(new admin_setting_configtext('block_speakingavatar/cdn_js',
        get_string('cdn_js', 'block_speakingavatar'),
        get_string('cdn_js_desc', 'block_speakingavatar'),
        'https://cdn.jsdelivr.net/npm/speaking-avatar/dist/speaking-avatar.umd.js', PARAM_URL));

    $settings->add(new admin_setting_configtext('block_speakingavatar/voice',
        get_string('voice', 'block_speakingavatar'),
        '', 'it-IT-ElsaNeural', PARAM_TEXT));

    $settings->add(new admin_setting_configselect('block_speakingavatar/theme',
        get_string('theme', 'block_speakingavatar'),
        '', 'light',
        array('light' => 'Light', 'dark' => 'Dark')));

    $settings->add(new admin_setting_configtext('block_speakingavatar/avatar',
        get_string('avatar', 'block_speakingavatar'),
        '', 'The Coach', PARAM_TEXT));

    $ADMIN->add('blocksettings', $settings);
}
