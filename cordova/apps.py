import os, subprocess
from utils import *

dir_root = get_root_dir()

def build_and_run_example_app_android():
    # ------------------------------------------------------------------
    # paths
    # ------------------------------------------------------------------
    plugin_temp_dir     = '{0}/temp_plugin'.format(dir_root)
    example_app_dir     = '{0}/example-cordova'.format(dir_root)
    sdk_plugin_package  = 'com.adjust.sdk'
    example_app_package = 'com.adjust.examples'

    # ------------------------------------------------------------------
    # remove example app from test device
    # ------------------------------------------------------------------
    debug_green('Removing example app from test device ...')
    adb_uninstall(example_app_package)

    # ------------------------------------------------------------------
    # package plugin content to custom directory
    # ------------------------------------------------------------------
    debug_green('Packaging plugin content to custom directory ...')
    _recreate_plugin_temp_dir(plugin_temp_dir)

    # ------------------------------------------------------------------
    # remove 'android' platform from example app
    # ------------------------------------------------------------------
    debug_green('Installing \'android\' platform from example app ...')
    change_dir(example_app_dir)
    cordova_remove_platform('android')

    # ------------------------------------------------------------------
    # install 'android' platform in example app
    # ------------------------------------------------------------------
    debug_green('Installing \'android\' platform in example app ...')
    cordova_add_platform('android')

    # ------------------------------------------------------------------
    # re-install plugins to example app
    # ------------------------------------------------------------------
    debug_green('Re-installing plugins to example app ...')
    cordova_remove_plugin(sdk_plugin_package)
    cordova_add_plugin(plugin_temp_dir, options=['--verbose', '--nofetch'])
    cordova_add_plugin('cordova-plugin-console')
    cordova_add_plugin('cordova-plugin-customurlscheme', options=['--variable', 'URL_SCHEME=adjust-example'])
    cordova_add_plugin('cordova-plugin-dialogs')
    cordova_add_plugin('cordova-plugin-whitelist')
    cordova_add_plugin('https://github.com/apache/cordova-plugin-device.git')
    cordova_add_plugin('cordova-universal-links-plugin')

    # ------------------------------------------------------------------
    # build Cordova example app project
    # ------------------------------------------------------------------
    debug_green('Building Cordova example app project ...')
    cordova_build('android', options=['--verbose'])

    # ------------------------------------------------------------------
    # run Cordova example app
    # cordova_run('android') # <-- does not seem to work, some Cordova specific error
    # ------------------------------------------------------------------
    debug_green('Installing & running Cordova example app ...')
    adb_install_apk('platforms/android/app/build/outputs/apk/debug/app-debug.apk')
    adb_shell(example_app_package)

    # ------------------------------------------------------------------
    # clean up temporary stuff
    # ------------------------------------------------------------------
    debug_green('Cleaning up temporary directorie(s) ...')
    remove_dir_if_exists(plugin_temp_dir)

def build_and_run_example_app_ios():
    # ------------------------------------------------------------------
    # paths
    # ------------------------------------------------------------------
    temp_plugin_dir    = '{0}/temp_plugin'.format(dir_root)
    example_app_dir    = '{0}/example-cordova'.format(dir_root)
    sdk_plugin_package = 'com.adjust.sdk'

    # ------------------------------------------------------------------
    # package plugin content to custom directory
    # ------------------------------------------------------------------
    debug_green('Packaging plugin content to custom directory ...')
    _recreate_plugin_temp_dir(temp_plugin_dir)

    # ------------------------------------------------------------------
    # remove 'ios' platform from example app
    # ------------------------------------------------------------------
    debug_green('Removing \'ios\' platform from example app ...')
    change_dir(example_app_dir)
    cordova_remove_platform('ios')

    # ------------------------------------------------------------------
    # install 'ios' platform to example app
    # ------------------------------------------------------------------
    debug_green('Installing \'ios\' platform to example app ...')
    cordova_add_platform('ios')

    # ------------------------------------------------------------------
    # re-install plugins to example app
    # ------------------------------------------------------------------
    debug_green('Re-installing plugins ...')
    cordova_remove_plugin(sdk_plugin_package)
    cordova_add_plugin(temp_plugin_dir)
    cordova_add_plugin('cordova-plugin-console')
    cordova_add_plugin('cordova-plugin-customurlscheme', options=['--variable', 'URL_SCHEME=adjust-example'])
    cordova_add_plugin('cordova-plugin-dialogs')
    cordova_add_plugin('cordova-plugin-whitelist')
    cordova_add_plugin('https://github.com/apache/cordova-plugin-device.git')

    # ------------------------------------------------------------------
    # run example app
    # ------------------------------------------------------------------
    debug_green('Running Cordova example app project ...')
    cordova_run('ios')

    # ------------------------------------------------------------------
    # build successful!
    # ------------------------------------------------------------------
    debug_green('Build successful! (You can also run it from Xcode ({0}/platforms/ios/)).'.format(example_app_dir))
    remove_dir_if_exists(temp_plugin_dir)

def build_and_run_test_app_android():
    # ------------------------------------------------------------------
    # paths
    # ------------------------------------------------------------------
    test_app_dir        = '{0}/test/app'.format(dir_root)
    test_plugin_dir     = '{0}/test/plugin'.format(dir_root)
    scripts_dir         = '{0}/scripts'.format(dir_root)
    plugin_temp_dir     = '{0}/temp_plugin'.format(dir_root)
    sdk_plugin_package  = 'com.adjust.sdk'
    test_plugin_package = 'com.adjust.test'
    test_app_package    = 'com.adjust.examples'

    # ------------------------------------------------------------------
    # remove test app from test device
    # ------------------------------------------------------------------
    debug_green('Removing test app package [{0}] from test device ...'.format(test_app_package))
    adb_uninstall(test_app_package)

    # ------------------------------------------------------------------
    # package plugin content to custom directory
    # ------------------------------------------------------------------
    debug_green('Packaging plugin content to custom directory [{0}] ...'.format(plugin_temp_dir))
    _recreate_plugin_temp_dir(plugin_temp_dir)

    # ------------------------------------------------------------------
    # remove 'android' platform
    # ------------------------------------------------------------------
    debug_green('Removing \'android\' platform in [{0}] ...'.format(test_app_dir))
    change_dir(test_app_dir)
    cordova_remove_platform('android')

    # ------------------------------------------------------------------
    # install 'android' platform
    # ------------------------------------------------------------------
    debug_green('Installing \'android\' platform in [{0}] ...'.format(test_app_dir))
    cordova_add_platform('android')

    # ------------------------------------------------------------------
    # re-install plugins to test app
    # ------------------------------------------------------------------
    debug_green('Re-installing plugins to test app ...')
    cordova_remove_plugin(sdk_plugin_package)
    cordova_remove_plugin(test_plugin_package)
    cordova_add_plugin(plugin_temp_dir, options=['--verbose', '--nofetch'])
    cordova_add_plugin(test_plugin_dir, options=['--verbose', '--nofetch'])
    cordova_add_plugin('cordova-plugin-device', options=['--verbose'])
    cordova_add_plugin('cordova-universal-links-plugin')
    cordova_add_plugin('cordova-plugin-customurlscheme', options=['--variable', 'URL_SCHEME=adjust-test'])

    # ------------------------------------------------------------------
    # build Cordova test app project
    # ------------------------------------------------------------------
    debug_green('Building Cordova test app project ...')
    cordova_build('android', options=['--verbose'])
    
    # ------------------------------------------------------------------
    # run Cordova test app
    # ------------------------------------------------------------------
    debug_green('Installing & running Cordova test app ...')
    adb_install_apk('platforms/android/app/build/outputs/apk/debug/app-debug.apk')
    adb_shell(test_app_package)

    # ------------------------------------------------------------------
    # clean up temporary stuff
    # ------------------------------------------------------------------
    debug_green('Cleaning up temporary directorie(s) ...')
    remove_dir_if_exists(plugin_temp_dir)

def build_and_run_test_app_ios():
    # ------------------------------------------------------------------
    # paths
    # ------------------------------------------------------------------
    test_app_dir        = '{0}/test/app'.format(dir_root)
    scripts_dir         = '{0}/scripts'.format(dir_root)
    test_plugin_dir     = '{0}/test/plugin'.format(dir_root)
    temp_plugin_dir     = '{0}/temp_plugin'.format(dir_root)
    sdk_plugin_package  = 'com.adjust.sdk'
    test_plugin_package = 'com.adjust.test'
    test_app_package    = 'com.adjust.examples'

    # ------------------------------------------------------------------
    # package plugin content to custom directory
    # ------------------------------------------------------------------
    debug_green('Packaging plugin content to custom directory [{0}] ...'.format(temp_plugin_dir))
    _recreate_plugin_temp_dir(temp_plugin_dir)

    # ------------------------------------------------------------------
    # remove 'android' platform from test app
    # ------------------------------------------------------------------
    debug_green('Removing \'android\' platform from test app in [{0}] ...'.format(test_app_dir))
    change_dir(test_app_dir)
    cordova_remove_platform('ios')

    # ------------------------------------------------------------------
    # install 'android' platform to test app
    # ------------------------------------------------------------------
    debug_green('Installing \'android\' platform to test app in [{0}] ...'.format(test_app_dir))
    cordova_add_platform('ios')

    # ------------------------------------------------------------------
    # re-install plugins to test app
    # ------------------------------------------------------------------
    debug_green('Re-installing plugins to test app ...')
    cordova_remove_plugin(sdk_plugin_package)
    cordova_remove_plugin(test_plugin_package)
    cordova_add_plugin('cordova-plugin-customurlscheme', options=['--variable', 'URL_SCHEME=adjust-test'])
    cordova_add_plugin(temp_plugin_dir, options=['--verbose', '--nofetch'])
    cordova_add_plugin(test_plugin_dir, options=['--verbose', '--nofetch'])

    # ------------------------------------------------------------------
    # run test app
    # ------------------------------------------------------------------
    debug_green('Running Cordova test app project ...')
    cordova_run('ios')

    # ------------------------------------------------------------------
    # build successful!
    # ------------------------------------------------------------------
    debug_green('Build successful! (You can also run it from Xcode ({0}/platforms/ios/))'.format(test_app_dir))
    remove_dir_if_exists(temp_plugin_dir)

def _recreate_plugin_temp_dir(plugin_temp_dir):
    recreate_dir(plugin_temp_dir)
    copy_dir_contents('{0}/www'.format(dir_root), '{0}/www'.format(plugin_temp_dir))
    copy_dir_contents('{0}/src'.format(dir_root), '{0}/src'.format(plugin_temp_dir))
    copy_file('{0}/package.json'.format(dir_root), '{0}/package.json'.format(plugin_temp_dir))
    copy_file('{0}/plugin.xml'.format(dir_root), '{0}/plugin.xml'.format(plugin_temp_dir))
