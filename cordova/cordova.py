#!/usr/bin/env python3
import sys
sys.dont_write_bytecode = True

import argparse, os, subprocess
from utils import *

set_log_tag('CORDOVA-SDK')

ROOT = root_dir()
PLUGIN_TEMP = f'{ROOT}/temp_plugin'
ANDROID_SDK = f'{ROOT}/ext/android/sdk'
IOS_SDK = f'{ROOT}/ext/ios/sdk'

SDK_PLUGIN = 'com.adjust.sdk'
TEST_PLUGIN = 'com.adjust.test'

# files and dirs that make up the com.adjust.sdk plugin
PLUGIN_DIRS = ['www', 'src']
PLUGIN_FILES = ['package.json', 'plugin.xml']

# third party plugins per app and platform, kept exactly as they have always been
APPS = {
    'example-app': {
        'dir': f'{ROOT}/example-cordova',
        'package': 'com.adjust.examples',
        'local': [[PLUGIN_TEMP, '--verbose', '--nofetch']],
        'plugins': {
            'android': [
                ['cordova-plugin-console'],
                ['cordova-plugin-customurlscheme', '--variable', 'URL_SCHEME=adjust-example'],
                ['cordova-plugin-dialogs'],
                ['cordova-plugin-whitelist'],
                ['https://github.com/apache/cordova-plugin-device.git'],
            ],
            'ios': [
                ['cordova-plugin-console'],
                ['cordova-plugin-customurlscheme', '--variable', 'URL_SCHEME=adjust-example'],
                ['cordova-plugin-dialogs'],
                ['cordova-plugin-whitelist'],
                ['https://github.com/apache/cordova-plugin-device.git'],
            ],
        },
    },
    'test-app': {
        'dir': f'{ROOT}/test/app',
        'package': 'com.adjust.examples',
        'local': [[PLUGIN_TEMP, '--verbose', '--nofetch'], [f'{ROOT}/test/plugin', '--verbose', '--nofetch']],
        'plugins': {
            'android': [
                ['cordova-plugin-device', '--verbose'],
                ['cordova-plugin-customurlscheme', '--variable', 'URL_SCHEME=adjust-test'],
            ],
            'ios': [
                ['cordova-plugin-customurlscheme', '--variable', 'URL_SCHEME=adjust-test'],
            ],
        },
    },
}


def build_android_jar(module, mode):
    require_dir(ANDROID_SDK)
    info(f'Building Android {module} in {mode} mode ...')
    change_dir(f'{ANDROID_SDK}/Adjust')
    run(['./gradlew', 'clean', f':tests:{module}:assemble{mode.capitalize()}'])
    jars = f'{ANDROID_SDK}/Adjust/tests/{module}/build/intermediates/aar_main_jar/{mode}/sync{mode.capitalize()}LibJars'
    copy_file(f'{jars}/classes.jar', f'{ROOT}/test/plugin/src/android/adjust-{module}.jar')


def build_test_library(platform, mode):
    if platform == 'android':
        build_android_jar('test-library', mode)
        return

    require_dir(IOS_SDK)
    # the static target builds both slices itself and dittos the result into sdk_distribution
    built = f'{IOS_SDK}/sdk_distribution/test-static-framework-device/AdjustTestLibrary.framework'
    out = f'{ROOT}/test/plugin/src/ios/AdjustTestLibrary.framework'

    info('Building iOS test library framework ...')
    change_dir(f'{IOS_SDK}/AdjustTests/AdjustTestLibrary')
    run(['xcodebuild', '-project', 'AdjustTestLibrary.xcodeproj', '-target', 'AdjustTestLibraryStatic',
         '-configuration', 'Debug', 'clean', 'build'])

    if not os.path.isdir(built):
        error(f'{built} was not produced by the build.')
        sys.exit(1)

    remove_dir(out)
    copy_dir(built, out)
    remove_dir(f'{out}/Versions')


def assemble_plugin():
    recreate_dir(PLUGIN_TEMP)
    for name in PLUGIN_DIRS:
        copy_dir(f'{ROOT}/{name}', f'{PLUGIN_TEMP}/{name}')
    for name in PLUGIN_FILES:
        copy_file(f'{ROOT}/{name}', f'{PLUGIN_TEMP}/{name}')


def run_app(target, platform, simulator=False):
    app = APPS[target]
    app_dir = app['dir']

    if platform == 'android':
        run(['adb', 'uninstall', app['package']], allow_failure=True)

    info(f'Assembling {SDK_PLUGIN} plugin in {PLUGIN_TEMP} ...')
    assemble_plugin()

    info(f'Reinstalling the {platform} platform ...')
    change_dir(app_dir)
    run(['cordova', 'platform', 'remove', platform], allow_failure=True)
    run(['cordova', 'platform', 'add', platform])

    info('Reinstalling plugins ...')
    for plugin in [SDK_PLUGIN, TEST_PLUGIN]:
        run(['cordova', 'plugin', 'remove', plugin], allow_failure=True)
    for plugin in app['local'] + app['plugins'][platform]:
        run(['cordova', 'plugin', 'add'] + plugin)

    if platform == 'android':
        info('Building and running the app ...')
        run(['cordova', 'build', 'android'])
        run(['adb', 'install', '-r', 'platforms/android/app/build/outputs/apk/debug/app-debug.apk'])
        run(['adb', 'shell', 'monkey', '-p', app['package'], '1'])
    elif simulator:
        info('Building and running the app ...')
        run(['cordova', 'run', 'ios'])
    else:
        # cordova deploys through ios-deploy, which cannot reach iOS 17 and newer, so install ourselves
        info('Building the app ...')
        run(['cordova', 'build', 'ios', '--device'])
        udid = output(['sh', '-c', "xcrun devicectl list devices --hide-headers | grep -w connected"
                                  " | grep -oE '[0-9A-F]{8}-([0-9A-F]{4}-){3}[0-9A-F]{12}' | head -1"])
        if not udid:
            error('No connected iOS device found.')
            sys.exit(1)
        info(f'Installing and launching on {udid} ...')
        run(['sh', '-c', f'xcrun devicectl device install app --device {udid}'
                         f' "{app_dir}"/platforms/ios/build/Debug-iphoneos/*.ipa'])
        run(['xcrun', 'devicectl', 'device', 'process', 'launch', '--device', udid, app['package']])

    remove_dir(PLUGIN_TEMP)


def main():
    parser = argparse.ArgumentParser(
        description='Build and run the Adjust Cordova SDK apps.',
        epilog='examples:\n'
               '  ./cordova.py build-native test-library android [debug|release]\n'
               '  ./cordova.py build-native test-options android [debug|release]\n'
               '  ./cordova.py run example-app android\n'
               '  ./cordova.py run test-app ios\n'
               '  ./cordova.py run test-app ios --simulator\n',
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('action', choices=['build-native', 'run'])
    parser.add_argument('target', choices=['test-library', 'test-options', 'example-app', 'test-app'])
    parser.add_argument('platform', choices=['android', 'ios'])
    parser.add_argument('mode', nargs='?', default='debug', choices=['debug', 'release'])
    parser.add_argument('--simulator', action='store_true', help='run on a simulator instead of a connected device')
    args = parser.parse_args()

    if args.action == 'build-native' and args.target not in ['test-library', 'test-options']:
        parser.error('build-native takes test-library or test-options')
    if args.action == 'run' and args.target not in ['example-app', 'test-app']:
        parser.error('run takes example-app or test-app')
    if args.target == 'test-options' and args.platform == 'ios':
        parser.error('test-options exists on android only')
    if args.simulator and args.platform == 'android':
        parser.error('--simulator applies to ios only')

    if args.action == 'build-native':
        if args.target == 'test-library':
            build_test_library(args.platform, args.mode)
        else:
            build_android_jar('test-options', args.mode)
    else:
        if args.target == 'test-app':
            build_test_library(args.platform, args.mode)
            if args.platform == 'android':
                build_android_jar('test-options', args.mode)
        run_app(args.target, args.platform, args.simulator)


if __name__ == '__main__':
    try:
        main()
    except (subprocess.CalledProcessError, FileNotFoundError) as failure:
        error(f'Failed: {failure}')
        sys.exit(1)
