#!/usr/bin/env python3
import sys
sys.dont_write_bytecode = True

import argparse, hashlib, json, os, shutil, subprocess, tempfile
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from utils import *

set_log_tag('CORDOVA-SDK')

ROOT = root_dir()
ANDROID_SDK = f'{ROOT}/ext/android/sdk'
IOS_SDK = f'{ROOT}/ext/ios/sdk'

# lowest iOS version Xcode 27 still builds for
IOS_DEPLOYMENT_TARGET = '15.0'

SDK_PLUGIN = 'com.adjust.sdk'
TEST_PLUGIN = 'com.adjust.test'
# optional iOS plugin that adds Google ODM, installed from this repo with --odm
ODM_PLUGIN = 'com.adjust.sdk.odm'
ODM_DIR = f'{ROOT}/plugins/odm'

# the Ionic wrapper: our index.ts is the source, the awesome-cordova-plugins checkout is only the build tool
WRAPPER_SOURCE = f'{ROOT}/ionic-native/index.ts'
WRAPPER_REPO = f'{ROOT}/ext/awesome-cordova-plugins'
WRAPPER_PLUGIN = 'src/@awesome-cordova-plugins/plugins/adjust/index.ts'
WRAPPER_DIST = f'{WRAPPER_REPO}/dist/@awesome-cordova-plugins'
WRAPPER_STAMP = f'{WRAPPER_DIST}/.adjust-build'

# keeps the Angular and Capacitor command line tools from prompting or sending usage data
QUIET = {**os.environ, 'CI': 'true', 'NG_CLI_ANALYTICS': 'false'}

# 'local' are the Adjust plugins, installed from this repo; each app has an .npmrc that makes npm pack them
# instead of linking them, so the app gets the same files a published package would have.
# 'plugins' are the third party plugins each app needs on top of that.
APPS = {
    'example-app': {
        'dir': f'{ROOT}/example-cordova',
        'package': 'com.adjust.examples',
        'local': [[ROOT]],
        'plugins': [
            ['cordova-plugin-customurlscheme', '--variable', 'URL_SCHEME=adjust-example'],
            ['cordova-plugin-dialogs'],
        ],
    },
    'test-app': {
        'dir': f'{ROOT}/test/app/cordova',
        'package': 'com.adjust.examples',
        'local': [[ROOT], [f'{ROOT}/test/plugin']],
        'plugins': [
            ['cordova-plugin-device'],
            ['cordova-plugin-customurlscheme', '--variable', 'URL_SCHEME=adjust-test'],
        ],
    },
}

# Ionic apps run on Capacitor; 'plist' holds the Info.plist entries the generated iOS project needs, as plutil arguments
IONIC_APPS = {
    'ionic-example-app': {
        'dir': f'{ROOT}/example-ionic-capacitor',
        'package': 'com.adjust.examples',
        'plist': [['NSUserTrackingUsageDescription', '-string',
                   'The example app asks for tracking permission to show how the Adjust SDK handles it.']],
    },
    'ionic-test-app': {
        'dir': f'{ROOT}/test/app/ionic',
        'package': 'com.adjust.examples',
        # the test server is reached over plain http and ws
        'plist': [['NSAppTransportSecurity', '-json', '{"NSAllowsArbitraryLoads": true}']],
        # the test plugin links AdjustTestLibrary as a static .framework, which Capacitor can't add to a Swift package
        'cocoapods_only': True,
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
    # the project is still on iOS 12.0, which Xcode 27 rejects; the static target builds its second slice
    # with a nested xcodebuild that ignores our command line, so pass the override through the environment
    with tempfile.NamedTemporaryFile('w', suffix='.xcconfig') as xcconfig:
        xcconfig.write(f'IPHONEOS_DEPLOYMENT_TARGET = {IOS_DEPLOYMENT_TARGET}\n')
        xcconfig.flush()
        run(['xcodebuild', '-project', 'AdjustTestLibrary.xcodeproj', '-target', 'AdjustTestLibraryStatic',
             '-configuration', 'Debug', 'clean', 'build'], env={**os.environ, 'XCODE_XCCONFIG_FILE': xcconfig.name})

    if not os.path.isdir(built):
        error(f'{built} was not produced by the build.')
        sys.exit(1)

    remove_dir(out)
    copy_dir(built, out)
    remove_dir(f'{out}/Versions')


def file_hash(path):
    with open(path, 'rb') as file:
        return hashlib.sha256(file.read()).hexdigest()


def read_stamp(path):
    return open(path).read() if os.path.isfile(path) else None


def write_stamp(path, content):
    with open(path, 'w') as file:
        file.write(content)


def build_ionic_wrapper():
    require_dir(WRAPPER_REPO)
    # rebuild only when our index.ts or the checked out awesome-cordova-plugins commit changed
    state = f'{file_hash(WRAPPER_SOURCE)} {output(["git", "-C", WRAPPER_REPO, "rev-parse", "HEAD"])}'
    if read_stamp(WRAPPER_STAMP) == state:
        info('The Ionic wrapper is already built from the current index.ts.')
        return

    info(f'Building the Ionic wrapper from {WRAPPER_SOURCE} ...')
    change_dir(WRAPPER_REPO)
    copy_file(WRAPPER_SOURCE, f'{WRAPPER_REPO}/{WRAPPER_PLUGIN}')
    try:
        lock, lock_stamp = file_hash('package-lock.json'), 'node_modules/.adjust-lock'
        if read_stamp(lock_stamp) != lock:
            # no lifecycle scripts: their prepare step would install git hooks into the submodule
            run(['npm', 'ci', '--ignore-scripts', '--no-audit', '--no-fund'])
            write_stamp(lock_stamp, lock)
        run(['npm', 'run', 'build'])
    finally:
        # leave the submodule exactly as it was checked out
        run(['git', 'checkout', '--', WRAPPER_PLUGIN])
    write_stamp(WRAPPER_STAMP, state)


def install_ionic_wrapper(app_dir):
    # the build output has the same files as the published packages, so replacing them in place is enough
    modules = f'{app_dir}/node_modules/@awesome-cordova-plugins'
    copy_dir(f'{WRAPPER_DIST}/core', f'{modules}/core')
    copy_dir(f'{WRAPPER_DIST}/plugins/adjust', f'{modules}/adjust')


def check_setup(target=None, platform=None):
    tools = [('node', 'install Node with nvm: https://github.com/nvm-sh/nvm')]
    if target in APPS:
        tools.append(('cordova', 'npm install -g cordova'))
    if platform == 'android':
        tools.append(('adb', 'install Android SDK platform-tools and add them to PATH'))
    elif platform == 'ios':
        tools.append(('pod', 'sudo gem install cocoapods'))
    problems = [f'{tool} not found in PATH. Fix: {fix}' for tool, fix in tools if shutil.which(tool) is None]

    nvmrc = f'{ROOT}/.nvmrc'
    if shutil.which('node') and os.path.isfile(nvmrc):
        wanted = open(nvmrc).read().strip()
        have = output(['node', '--version']).lstrip('v')
        if have.split('.')[0] != wanted.split('.')[0]:
            problems.append(f'The apps and the Ionic wrapper build need Node {wanted}.x (see {nvmrc}), you have {have}. '
                            f'Fix: nvm install {wanted} && nvm use {wanted}')

    if problems:
        error('Setup is incomplete. Fix the following and re-run:')
        for problem in problems:
            error(f'  - {problem}')
        sys.exit(1)


def run_ionic_app(target, platform, odm=False):
    app = IONIC_APPS[target]
    app_dir = app['dir']

    build_ionic_wrapper()

    if platform == 'android':
        run(['adb', 'uninstall', app['package']], allow_failure=True)

    info('Installing the app dependencies ...')
    change_dir(app_dir)
    # Capacitor only picks up plugins listed in package.json, so --odm adds the ODM plugin there for this run
    # and the original file is put back once the native project is generated
    package_json = f'{app_dir}/package.json'
    original_package = open(package_json).read()
    if odm:
        package = json.loads(original_package)
        package['dependencies'][ODM_PLUGIN] = f'file:{os.path.relpath(ODM_DIR, app_dir)}'
        write_stamp(package_json, json.dumps(package, indent=2) + '\n')
    else:
        remove_dir(f'{app_dir}/node_modules/{ODM_PLUGIN}')
    try:
        run(['npm', 'install', '--no-audit', '--no-fund'])
        prepare_ionic_app(app, platform)
    finally:
        write_stamp(package_json, original_package)
    if platform == 'android':
        info('Building and running the app ...')
        change_dir(f'{app_dir}/android')
        run(['./gradlew', 'assembleDebug'])
        run(['adb', 'install', '-r', 'app/build/outputs/apk/debug/app-debug.apk'])
        run(['adb', 'shell', 'monkey', '-p', app['package'], '1'])
        return
    build_ionic_ios_app(app)


def prepare_ionic_app(app, platform):
    app_dir = app['dir']
    info('Replacing the published Ionic wrapper with the local build ...')
    install_ionic_wrapper(app_dir)

    info('Building the web app ...')
    # the Angular build cache does not notice files replaced inside node_modules
    remove_dir(f'{app_dir}/.angular')
    run(['npx', 'ng', 'build', '--configuration', 'development'], env=QUIET)

    info(f'Generating the {platform} project ...')
    remove_dir(f'{app_dir}/{platform}')
    if platform == 'android':
        run(['npx', 'cap', 'add', 'android'], env=QUIET)
        return

    # Capacitor pick the package manager: SPM from Capacitor 8 on, CocoaPods before.
    # To check CocoaPods, install a lower @capacitor version in the app.
    run(['npx', 'cap', 'add', 'ios', *(['--packagemanager', 'CocoaPods'] if app.get('cocoapods_only') else [])],
        env=QUIET)
    spm = os.path.isdir(f'{app_dir}/ios/App/CapApp-SPM')
    info(f'Capacitor set up the iOS project with {"SPM" if spm else "CocoaPods"}')
    for entry in app['plist']:
        run(['plutil', '-replace', *entry, 'ios/App/App/Info.plist'])


def build_ionic_ios_app(app):
    app_dir = app['dir']
    change_dir(app_dir)
    spm = os.path.isdir(f'{app_dir}/ios/App/CapApp-SPM')
    team = apple_development_team()
    if not team:
        error('No Apple Development certificate found. Fix: sign in to Xcode with your Apple ID')
        sys.exit(1)
    info('Building the app ...')
    # an SPM project has no workspace, the packages are part of the Xcode project
    project = ['-project', 'ios/App/App.xcodeproj'] if spm else ['-workspace', 'ios/App/App.xcworkspace']
    run(['xcodebuild', *project, '-scheme', 'App', '-configuration', 'Debug',
         '-destination', 'generic/platform=iOS', '-derivedDataPath', 'ios/build', '-allowProvisioningUpdates',
         f'DEVELOPMENT_TEAM={team}', 'CODE_SIGN_STYLE=Automatic', 'build'])

    udid = connected_ios_device()
    if not udid:
        error('No connected iOS device found.')
        sys.exit(1)
    info(f'Installing and launching on {udid} ...')
    run(['xcrun', 'devicectl', 'device', 'install', 'app', '--device', udid, 'ios/build/Build/Products/Debug-iphoneos/App.app'])
    run(['xcrun', 'devicectl', 'device', 'process', 'launch', '--terminate-existing', '--device', udid, app['package']])


def run_app(target, platform, simulator=False, odm=False):
    app = APPS[target]
    app_dir = app['dir']

    if platform == 'android':
        run(['adb', 'uninstall', app['package']], allow_failure=True)

    info(f'Reinstalling the {platform} platform ...')
    change_dir(app_dir)
    # platform remove also drops cordova-<platform> from package.json, and platform add then picks the latest version,
    # so read the version the app asks for first and pass it explicitly
    with open(f'{app_dir}/package.json') as package_json:
        package = json.load(package_json)
    spec = {**package.get('dependencies', {}), **package.get('devDependencies', {})}.get(f'cordova-{platform}')
    run(['cordova', 'platform', 'remove', platform], allow_failure=True)
    # remove the Adjust plugins before platform add: it would otherwise restore them from their saved file: specs,
    # which cordova resolves against the wrong directory, or reuse stale copies. They're added again below.
    # The ODM plugin depends on the SDK plugin, so it has to go first.
    for plugin in [ODM_PLUGIN, SDK_PLUGIN, TEST_PLUGIN]:
        run(['cordova', 'plugin', 'remove', plugin], allow_failure=True)
        remove_dir(f'{app_dir}/plugins/{plugin}')
        remove_dir(f'{app_dir}/node_modules/{plugin}')
    # plugin remove leaves package.json alone for a plugin that isn't installed, and platform add would then
    # restore it from there, so drop any entry that is left
    with open(f'{app_dir}/package.json') as package_json:
        package = json.load(package_json)
    for section in [package.get('dependencies', {}), package.get('devDependencies', {}),
                    package.get('cordova', {}).get('plugins', {})]:
        for plugin in [ODM_PLUGIN, SDK_PLUGIN, TEST_PLUGIN]:
            section.pop(plugin, None)
    write_stamp(f'{app_dir}/package.json', json.dumps(package, indent=2) + '\n')
    run(['cordova', 'platform', 'add', f'{platform}@{spec}' if spec else platform])

    info('Reinstalling plugins ...')
    for plugin in app['local'] + ([[ODM_DIR]] if odm else []) + app['plugins']:
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
        udid = connected_ios_device()
        if not udid:
            error('No connected iOS device found.')
            sys.exit(1)
        info(f'Installing and launching on {udid} ...')
        run(['sh', '-c', f'xcrun devicectl device install app --device {udid}'
                         f' "{app_dir}"/platforms/ios/build/Debug-iphoneos/*.ipa'])
        run(['xcrun', 'devicectl', 'device', 'process', 'launch', '--device', udid, app['package']])


def main():
    parser = argparse.ArgumentParser(
        description='Build and run the Adjust Cordova SDK apps.',
        epilog='examples:\n'
               '  ./cordova.py build-native test-library android [debug|release]\n'
               '  ./cordova.py build-native test-options android [debug|release]\n'
               '  ./cordova.py build-wrapper\n'
               '  ./cordova.py run example-app android\n'
               '  ./cordova.py run test-app ios\n'
               '  ./cordova.py run test-app ios --simulator\n'
               '  ./cordova.py run example-app ios --odm\n'
               '  ./cordova.py run ionic-example-app ios\n'
               '  ./cordova.py run ionic-example-app ios --odm\n'
               '  ./cordova.py run ionic-test-app android\n',
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('action', choices=['build-native', 'build-wrapper', 'run'])
    parser.add_argument('target', nargs='?', choices=['test-library', 'test-options', *APPS, *IONIC_APPS])
    parser.add_argument('platform', nargs='?', choices=['android', 'ios'])
    parser.add_argument('mode', nargs='?', default='debug', choices=['debug', 'release'])
    parser.add_argument('--simulator', action='store_true', help='run on a simulator instead of a connected device')
    parser.add_argument('--odm', action='store_true', help='also install the Google ODM plugin (ios only)')
    args = parser.parse_args()

    if args.action == 'build-wrapper':
        if args.target or args.platform:
            parser.error('build-wrapper takes no target or platform')
        check_setup()
        build_ionic_wrapper()
        return

    if not args.target or not args.platform:
        parser.error(f'{args.action} needs a target and a platform')
    if args.action == 'build-native' and args.target not in ['test-library', 'test-options']:
        parser.error('build-native takes test-library or test-options')
    if args.action == 'run' and args.target not in [*APPS, *IONIC_APPS]:
        parser.error(f'run takes one of: {", ".join([*APPS, *IONIC_APPS])}')
    if args.target == 'test-options' and args.platform == 'ios':
        parser.error('test-options exists on android only')
    if args.simulator and args.platform == 'android':
        parser.error('--simulator applies to ios only')
    if args.simulator and args.target in IONIC_APPS:
        parser.error('--simulator is not supported for the Ionic apps')
    if args.odm and (args.action != 'run' or args.platform != 'ios'):
        parser.error('--odm applies to run on ios only')

    if args.action == 'build-native':
        if args.target == 'test-library':
            build_test_library(args.platform, args.mode)
        else:
            build_android_jar('test-options', args.mode)
        return

    check_setup(args.target, args.platform)
    if args.target in ['test-app', 'ionic-test-app']:
        build_test_library(args.platform, args.mode)
        if args.platform == 'android':
            build_android_jar('test-options', args.mode)
    if args.target in IONIC_APPS:
        run_ionic_app(args.target, args.platform, args.odm)
    else:
        run_app(args.target, args.platform, args.simulator, args.odm)


if __name__ == '__main__':
    try:
        main()
    except (subprocess.CalledProcessError, FileNotFoundError) as failure:
        error(f'Failed: {failure}')
        sys.exit(1)
