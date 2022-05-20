import os, subprocess
from utils import *

dir_root = get_root_dir()

def build_and_run_example_app_android():
    # ------------------------------------------------------------------
    # paths
    # ------------------------------------------------------------------
    dir_plugin_temp     = '{0}/temp_plugin'.format(dir_root)
    dir_example_app     = '{0}/example-cordova'.format(dir_root)
    package_sdk_plugin  = 'com.adjust.sdk'
    package_example_app = 'com.adjust.examples'

    # ------------------------------------------------------------------
    # remove example app from test device
    # ------------------------------------------------------------------
    debug_green('Removing example app from test device ...')
    adb_uninstall(package_example_app)

    # ------------------------------------------------------------------
    # package plugin content to custom directory
    # ------------------------------------------------------------------
    debug_green('Packaging plugin content to custom directory ...')
    _recreate_dir_plugin_temp(dir_plugin_temp)

    # ------------------------------------------------------------------
    # remove 'android' platform from example app
    # ------------------------------------------------------------------
    debug_green('Installing \'android\' platform from example app ...')
    change_dir(dir_example_app)
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
    cordova_remove_plugin(package_sdk_plugin)
    cordova_add_plugin(dir_plugin_temp, options=['--verbose', '--nofetch'])
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
    adb_shell(package_example_app)

    # ------------------------------------------------------------------
    # clean up temporary stuff
    # ------------------------------------------------------------------
    debug_green('Cleaning up temporary directorie(s) ...')
    remove_dir_if_exists(dir_plugin_temp)

def build_and_run_example_app_ios():
    # ------------------------------------------------------------------
    # paths
    # ------------------------------------------------------------------
    dir_plugin_temp    = '{0}/temp_plugin'.format(dir_root)
    dir_example_app    = '{0}/example-cordova'.format(dir_root)
    package_sdk_plugin = 'com.adjust.sdk'

    # ------------------------------------------------------------------
    # package plugin content to custom directory
    # ------------------------------------------------------------------
    debug_green('Packaging plugin content to custom directory ...')
    _recreate_dir_plugin_temp(dir_plugin_temp)

    # ------------------------------------------------------------------
    # remove 'ios' platform from example app
    # ------------------------------------------------------------------
    debug_green('Removing \'ios\' platform from example app ...')
    change_dir(dir_example_app)
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
    cordova_remove_plugin(package_sdk_plugin)
    cordova_add_plugin(dir_plugin_temp)
    cordova_add_plugin('cordova-plugin-console')
    cordova_add_plugin('cordova-plugin-customurlscheme', options=['--variable', 'URL_SCHEME=adjust-example'])
    cordova_add_plugin('cordova-plugin-dialogs')
    cordova_add_plugin('cordova-plugin-whitelist')
    cordova_add_plugin('https://github.com/apache/cordova-plugin-device.git')

    # ------------------------------------------------------------------
    # run example app
    # NOTE: let's not this for now, tends to be annoying
    # ------------------------------------------------------------------
    # debug_green('Running Cordova example app project ...')
    # cordova_run('ios')

    # ------------------------------------------------------------------
    # build successful!
    # ------------------------------------------------------------------
    debug_green('Build successful! (You can also run it from Xcode ({0}/platforms/ios/)).'.format(dir_example_app))
    remove_dir_if_exists(dir_plugin_temp)

def build_and_run_test_app_android():
    # ------------------------------------------------------------------
    # paths
    # ------------------------------------------------------------------
    dir_test_app        = '{0}/test/app'.format(dir_root)
    dir_test_plugin     = '{0}/test/plugin'.format(dir_root)
    dir_plugin_temp     = '{0}/temp_plugin'.format(dir_root)
    package_sdk_plugin  = 'com.adjust.sdk'
    package_test_plugin = 'com.adjust.test'
    package_test_app    = 'com.adjust.examples'

    # ------------------------------------------------------------------
    # remove test app from test device
    # ------------------------------------------------------------------
    debug_green('Removing test app package [{0}] from test device ...'.format(package_test_app))
    adb_uninstall(package_test_app)

    # ------------------------------------------------------------------
    # package plugin content to custom directory
    # ------------------------------------------------------------------
    debug_green('Packaging plugin content to custom directory [{0}] ...'.format(dir_plugin_temp))
    _recreate_dir_plugin_temp(dir_plugin_temp)

    # ------------------------------------------------------------------
    # remove 'android' platform
    # ------------------------------------------------------------------
    debug_green('Removing \'android\' platform in [{0}] ...'.format(dir_test_app))
    change_dir(dir_test_app)
    cordova_remove_platform('android')

    # ------------------------------------------------------------------
    # install 'android' platform
    # ------------------------------------------------------------------
    debug_green('Installing \'android\' platform in [{0}] ...'.format(dir_test_app))
    cordova_add_platform('android')

    # ------------------------------------------------------------------
    # re-install plugins to test app
    # ------------------------------------------------------------------
    debug_green('Re-installing plugins to test app ...')
    cordova_remove_plugin(package_sdk_plugin)
    cordova_remove_plugin(package_test_plugin)
    cordova_add_plugin(dir_plugin_temp, options=['--verbose', '--nofetch'])
    cordova_add_plugin(dir_test_plugin, options=['--verbose', '--nofetch'])
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
    adb_shell(package_test_app)

    # ------------------------------------------------------------------
    # clean up temporary stuff
    # ------------------------------------------------------------------
    debug_green('Cleaning up temporary directorie(s) ...')
    remove_dir_if_exists(dir_plugin_temp)

def build_and_run_test_app_ios():
    # ------------------------------------------------------------------
    # paths
    # ------------------------------------------------------------------
    dir_test_app        = '{0}/test/app'.format(dir_root)
    dir_test_plugin     = '{0}/test/plugin'.format(dir_root)
    dir_plugin_temp     = '{0}/temp_plugin'.format(dir_root)
    package_sdk_plugin  = 'com.adjust.sdk'
    package_test_plugin = 'com.adjust.test'
    package_test_app    = 'com.adjust.examples'

    # ------------------------------------------------------------------
    # package plugin content to custom directory
    # ------------------------------------------------------------------
    debug_green('Packaging plugin content to custom directory [{0}] ...'.format(dir_plugin_temp))
    _recreate_dir_plugin_temp(dir_plugin_temp)

    # ------------------------------------------------------------------
    # remove 'android' platform from test app
    # ------------------------------------------------------------------
    debug_green('Removing \'android\' platform from test app in [{0}] ...'.format(dir_test_app))
    change_dir(dir_test_app)
    cordova_remove_platform('ios')

    # ------------------------------------------------------------------
    # install 'android' platform to test app
    # ------------------------------------------------------------------
    debug_green('Installing \'android\' platform to test app in [{0}] ...'.format(dir_test_app))
    cordova_add_platform('ios')

    # ------------------------------------------------------------------
    # re-install plugins to test app
    # ------------------------------------------------------------------
    debug_green('Re-installing plugins to test app ...')
    cordova_remove_plugin(package_sdk_plugin)
    cordova_remove_plugin(package_test_plugin)
    cordova_add_plugin('cordova-plugin-customurlscheme', options=['--variable', 'URL_SCHEME=adjust-test'])
    cordova_add_plugin(dir_plugin_temp, options=['--verbose', '--nofetch'])
    cordova_add_plugin(dir_test_plugin, options=['--verbose', '--nofetch'])

    # ------------------------------------------------------------------
    # run test app
    # NOTE: let's not this for now, tends to be annoying
    # ------------------------------------------------------------------
    # debug_green('Running Cordova test app project ...')
    # cordova_run('ios')

    # ------------------------------------------------------------------
    # build successful!
    # ------------------------------------------------------------------
    debug_green('Build successful! (You can also run it from Xcode ({0}/platforms/ios/))'.format(dir_test_app))
    remove_dir_if_exists(dir_plugin_temp)

def _recreate_dir_plugin_temp(dir_plugin_temp):
    recreate_dir(dir_plugin_temp)
    copy_dir_content('{0}/www'.format(dir_root), '{0}/www'.format(dir_plugin_temp))
    copy_dir_content('{0}/src'.format(dir_root), '{0}/src'.format(dir_plugin_temp))
    copy_file('{0}/package.json'.format(dir_root), '{0}/package.json'.format(dir_plugin_temp))
    copy_file('{0}/plugin.xml'.format(dir_root), '{0}/plugin.xml'.format(dir_plugin_temp))
