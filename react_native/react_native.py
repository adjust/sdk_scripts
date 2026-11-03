#!/usr/bin/env python3
import sys
sys.dont_write_bytecode = True

import argparse, os, shutil, subprocess
from utils import *

set_log_tag('REACT-NATIVE-SDK')

ROOT = root_dir()
TEMP = f'{ROOT}/temp'
ANDROID_SDK = f'{ROOT}/ext/android/sdk'
IOS_SDK = f'{ROOT}/ext/ios/sdk'
METRO_LOG = '/tmp/react-native-adjust-metro.log'

# files that make up the react-native-adjust package, alongside the android and ios dirs
PACKAGE_FILES = ['package.json', 'react-native-adjust.podspec', 'react-native.config.js', 'index.js', 'index.d.ts']

APPS = {
    'example-app': {
        'dir': f'{ROOT}/example',
        'package': 'com.adjustexample',
        'deps': {
            'react-native-adjust': '../temp',
            'react-native-adjust-oaid': '../plugins/oaid',
        },
    },
    'test-app': {
        'dir': f'{ROOT}/test/app',
        'package': 'com.adjust.examples',
        'deps': {
            'react-native-adjust': '../../temp',
            'react-native-adjust-oaid': '../../plugins/oaid',
            'react-native-adjust-test': '../lib',
        },
    },
}


def build_android_jar(module, mode):
    require_dir(ANDROID_SDK)
    info(f'Building Android {module} in {mode} mode ...')
    change_dir(f'{ANDROID_SDK}/Adjust')
    run(['./gradlew', 'clean', f':tests:{module}:assemble{mode.capitalize()}'])
    jars = f'{ANDROID_SDK}/Adjust/tests/{module}/build/intermediates/aar_main_jar/{mode}/sync{mode.capitalize()}LibJars'
    copy_file(f'{jars}/classes.jar', f'{ROOT}/test/lib/android/libs/adjust-{module}.jar')


def build_test_library(platform, mode):
    if platform == 'android':
        build_android_jar('test-library', mode)
    else:
        require_dir(IOS_SDK)
        info('Copying iOS test library sources ...')
        copy_dir(f'{IOS_SDK}/AdjustTests/AdjustTestLibrary/AdjustTestLibrary', f'{ROOT}/test/lib/ios/AdjustTestLibrary')


def assemble_package():
    recreate_dir(TEMP)
    copy_dir(f'{ROOT}/android', f'{TEMP}/android', '.gradle', 'build')
    copy_dir(f'{ROOT}/ios', f'{TEMP}/ios', 'build', 'Build')
    for name in PACKAGE_FILES:
        copy_file(f'{ROOT}/{name}', f'{TEMP}/{name}')


def start_metro(app_dir):
    # run Metro ourselves, otherwise the CLI opens a terminal window for it on every single run
    run(['sh', '-c', 'lsof -ti tcp:8081 | xargs kill'], allow_failure=True)
    run_background(['npx', 'react-native', 'start', '--no-interactive'], app_dir, METRO_LOG)
    info('Waiting for Metro ...')
    run(['sh', '-c', 'for i in $(seq 30); do lsof -ti tcp:8081 >/dev/null && exit 0; sleep 1; done; exit 1'])


def check_setup(target, platform):
    app_dir = APPS[target]['dir']
    tools = [('node', 'install Node via nvm: https://github.com/nvm-sh/nvm'),
             ('yarn', 'npm install -g yarn')]
    if platform == 'android':
        tools.append(('adb', 'install Android SDK platform-tools and add them to PATH'))
    else:
        tools.append(('pod', 'sudo gem install cocoapods'))
    problems = [f'{tool} not found in PATH. Fix: {fix}' for tool, fix in tools if shutil.which(tool) is None]

    nvmrc = f'{app_dir}/.nvmrc'
    if shutil.which('node') and os.path.isfile(nvmrc):
        wanted = open(nvmrc).read().strip()
        have = output(['node', '--version']).lstrip('v')
        if have.split('.')[0] != wanted.split('.')[0]:
            problems.append(f'{target} needs Node {wanted}.x (see {nvmrc}), you have {have}. Fix: nvm install {wanted} && nvm use {wanted}')

    if problems:
        error('Setup is incomplete. Fix the following and re-run:')
        for problem in problems:
            error(f'  - {problem}')
        sys.exit(1)


def run_app(target, platform, simulator=False):
    app = APPS[target]
    app_dir = app['dir']
    deps = app['deps']

    if platform == 'android':
        run(['adb', 'uninstall', app['package']], allow_failure=True)

    # the app points at temp/, which does not exist yet, so unlink the local packages before installing
    info('Unlinking local Adjust packages ...')
    change_dir(app_dir)
    for name in deps:
        run(['yarn', 'remove', name], allow_failure=True)
        remove_dir(f'{app_dir}/node_modules/{name}')

    info('Installing app dependencies ...')
    run(['yarn', 'install'])

    info(f'Assembling react-native-adjust in {TEMP} ...')
    assemble_package()

    info('Linking local Adjust packages ...')
    for path in deps.values():
        run(['yarn', 'add', path])

    if platform == 'ios':
        change_dir(f'{app_dir}/ios')
        run(['pod', 'update'])
        change_dir(app_dir)

    remove_dir(TEMP)
    start_metro(app_dir)

    if platform == 'android':
        run(['npx', 'react-native', 'run-android', '--no-packager'])
    else:
        cmd = ['npx', 'react-native', 'run-ios', '--no-packager']
        if not simulator:
            cmd.append('--device')
        run(cmd)


def main():
    parser = argparse.ArgumentParser(
        description='Build and run the Adjust React Native SDK apps.',
        epilog='examples:\n'
               '  ./react_native.py build-native test-library android [debug|release]\n'
               '  ./react_native.py build-native test-options android [debug|release]\n'
               '  ./react_native.py run example-app android\n'
               '  ./react_native.py run test-app ios\n'
               '  ./react_native.py run test-app ios --simulator\n',
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
        check_setup(args.target, args.platform)
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
