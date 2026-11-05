#!/usr/bin/env python3
import sys
sys.dont_write_bytecode = True

import argparse, glob, json, os, re, shutil, subprocess
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from utils import *

set_log_tag('UNITY-SDK')

ROOT = root_dir()
SCRIPTS = os.path.dirname(os.path.abspath(__file__))
WINDOWS = sys.platform == 'win32'
# outside the repo, kept between runs so Unity does not import everything again each time
TEMP = os.path.expandvars('%LOCALAPPDATA%/adjust-unity-sdk') if WINDOWS else os.path.expanduser('~/Library/Caches/adjust-unity-sdk')
ANDROID_SDK = f'{ROOT}/ext/android/sdk'
IOS_SDK = f'{ROOT}/ext/ios/sdk'
# the .NET SDK behind the Windows layer; ADJUST_WINDOWS_SDK_DIR points at another checkout of it
WINDOWS_SDK = os.environ.get('ADJUST_WINDOWS_SDK_DIR') or f'{ROOT}/ext/windows/sdk'
TEST_NATIVE = f'{ROOT}/Assets/Test/Native'
EDITORS = 'C:/Program Files/Unity/Hub/Editor' if WINDOWS else '/Applications/Unity/Hub/Editor'
# the editor binary and the player modules, relative to the editor version folder
UNITY, PLAYBACK_ENGINES = ('Editor/Unity.exe', 'Editor/Data/PlaybackEngines') if WINDOWS else ('Unity.app/Contents/MacOS/Unity', 'PlaybackEngines')
EDM4U = 'https://github.com/googlesamples/unity-jar-resolver.git?path=upm#v1.2.190'
NEWTONSOFT = '3.2.1'

# "windows" builds the desktop player of the machine the script runs on
if sys.platform == 'darwin':
    DESKTOP_TARGET, DESKTOP_MODULE, DESKTOP_SUFFIX = 'OSXUniversal', 'MacStandaloneSupport', '.app'
elif sys.platform == 'win32':
    DESKTOP_TARGET, DESKTOP_MODULE, DESKTOP_SUFFIX = 'Win64', 'WindowsStandaloneSupport', '.exe'
else:
    DESKTOP_TARGET, DESKTOP_MODULE, DESKTOP_SUFFIX = 'Linux64', 'LinuxStandaloneSupport', ''

APPS = {
    'example-app': {
        'scene': 'Assets/Example/Example.unity',
        'package': 'com.adjust.examples',
    },
    'test-app': {
        'scene': 'Assets/Test/TestApp/TestApp.unity',
        'package': 'com.adjust.examples',
    },
}

def build_android_aar(module, mode):
    require_dir(ANDROID_SDK)
    info(f'Building Android {module} in {mode} mode ...')
    change_dir(f'{ANDROID_SDK}/Adjust')
    run(['./gradlew', '--init-script', f'{SCRIPTS}/platform/java8.gradle', 'clean', f':tests:{module}:assemble{mode.capitalize()}'])
    copy_file(f'{ANDROID_SDK}/Adjust/tests/{module}/build/outputs/aar/{module}-{mode}.aar', f'{TEST_NATIVE}/Android/adjust-{module}.aar')

# builds one project of the .NET SDK and drops its dll into the Unity package
def build_dotnet(project, mode, destination):
    require_dir(WINDOWS_SDK)
    name = os.path.basename(project)
    info(f'Building {name} in {mode} mode ...')
    run(['dotnet', 'build', f'{WINDOWS_SDK}/{project}/{name}.csproj', '-c', mode.capitalize(), '-f', 'netstandard2.0', '-nologo', '-v', 'minimal'])
    copy_file(f'{WINDOWS_SDK}/{project}/bin/{mode.capitalize()}/netstandard2.0/{name}.dll', f'{destination}/{name}.dll')

# the tests the .NET SDK can run, kept next to its own console test app
def supported_tests():
    source = f'{WINDOWS_SDK}/IntegrationTesting/TestAppDotNet/SupportedTests.cs'
    if not os.path.isfile(source):
        error(f'{source} is missing. Fix: git submodule update --init --recursive, or set ADJUST_WINDOWS_SDK_DIR')
        sys.exit(1)
    return ','.join(re.findall(r'"(Test_\w+)"', open(source).read()))

def build_test_library(platform, mode):
    if platform == 'android':
        build_android_aar('test-library', mode)
        return
    if platform == 'windows':
        build_dotnet('IntegrationTesting/TestLibrary', mode, f'{TEST_NATIVE}/Windows')
        return

    require_dir(IOS_SDK)
    # the static target starts its own simulator build that drops our settings, so build the device library directly;
    # Xcode 27 builds for iOS 15.0 and newer only, while the project still says 12.0
    out = f'{TEMP}/ios-test-library'
    built = f'{out}/{mode.capitalize()}-iphoneos'

    info('Building iOS test library ...')
    remove_dir(out)
    change_dir(f'{IOS_SDK}/AdjustTests/AdjustTestLibrary')
    run(['xcodebuild', '-project', 'AdjustTestLibrary.xcodeproj', '-target', 'AdjustTestLibrary', '-configuration', mode.capitalize(),
         '-sdk', 'iphoneos', 'IPHONEOS_DEPLOYMENT_TARGET=15.0', f'SYMROOT={out}', f'OBJROOT={out}/obj', 'build'])

    copy_file(f'{built}/libAdjustTestLibrary.a', f'{TEST_NATIVE}/iOS/AdjustTestLibrary.a')
    for header in glob.glob(f'{built}/usr/local/include/*.h'):
        copy_file(header, f'{TEST_NATIVE}/iOS/{os.path.basename(header)}')

def unity_version(requested):
    installed = os.listdir(EDITORS) if os.path.isdir(EDITORS) else []
    # newest final release, unless a version is asked for
    releases = [v for v in installed if re.fullmatch(r'[\d.]+f\d+', v)]
    version = requested or max(releases, key=lambda v: [int(n) for n in re.findall(r'\d+', v)], default=None)
    if version not in installed:
        error(f'Unity {version or "release"} is not installed in {EDITORS}. Fix: install it with Unity Hub')
        sys.exit(1)
    return version

def check_setup(platform, version):
    module = {'android': 'AndroidPlayer', 'ios': 'iOSSupport', 'windows': DESKTOP_MODULE}[platform]
    tool, fix = {'android': ('adb', 'install Android SDK platform-tools and add them to PATH'),
                 'ios': ('pod', 'sudo gem install cocoapods'),
                 'windows': ('dotnet', 'install the .NET SDK from https://dotnet.microsoft.com/download')}[platform]
    problems = []
    if not os.path.isdir(f'{EDITORS}/{version}/{PLAYBACK_ENGINES}/{module}'):
        problems.append(f'Unity {version} has no {platform} build support. Fix: add it in Unity Hub > Installs > {version} > Add modules')
    if shutil.which(tool) is None:
        problems.append(f'{tool} not found in PATH. Fix: {fix}')

    if problems:
        error('Setup is incomplete. Fix the following and re-run:')
        for problem in problems:
            error(f'  - {problem}')
        sys.exit(1)

def run_unity(version, log, args):
    info(f'Running Unity {version}, log: {log} ...')
    if subprocess.call([f'{EDITORS}/{version}/{UNITY}', '-batchmode', '-nographics', '-quit', '-logFile', log] + args) != 0:
        error(f'Unity failed, see {log}')
        sys.exit(1)


def prepare_project(version):
    project = f'{TEMP}/{version}'
    if not os.path.isdir(project):
        info(f'Creating Unity project in {project} ...')
        os.makedirs(TEMP, exist_ok=True)
        run_unity(version, f'{TEMP}/create-{version}.log', ['-createProject', project])

    # the example app needs uGUI, which the empty project does not have, and the SDK needs EDM4U
    # and Newtonsoft.Json (the same dependency its package.json declares)
    manifest = json.load(open(f'{project}/Packages/manifest.json'))
    manifest['dependencies']['com.unity.ugui'] = '2.0.0' if int(version.split('.')[0]) >= 6000 else '1.0.0'
    manifest['dependencies']['com.google.external-dependency-manager'] = EDM4U
    manifest['dependencies']['com.unity.nuget.newtonsoft-json'] = NEWTONSOFT
    json.dump(manifest, open(f'{project}/Packages/manifest.json', 'w'), indent=2)

    for name in ['Adjust', 'Example', 'Test']:
        if not os.path.islink(f'{project}/Assets/{name}'):
            # windows needs to know it is a folder link; works without admin in developer mode
            os.symlink(f'{ROOT}/Assets/{name}', f'{project}/Assets/{name}', target_is_directory=True)
    copy_file(f'{SCRIPTS}/platform/AdjustAppBuilder.cs', f'{project}/Assets/Editor/AdjustAppBuilder.cs')

    # EDM4U adds the Android dependencies to these templates; nothing to copy without the Android module
    android = f'{EDITORS}/{version}/{PLAYBACK_ENGINES}/AndroidPlayer'
    for name in ['mainTemplate.gradle', 'settingsTemplate.gradle', 'gradleTemplate.properties']:
        if os.path.isdir(android) and not os.path.isfile(f'{project}/Assets/Plugins/Android/{name}'):
            copy_file(f'{android}/Tools/GradleTemplates/{name}', f'{project}/Assets/Plugins/Android/{name}')
    return project

def run_app(target, platform, mode, version, tests=None, il2cpp=False):
    app = APPS[target]
    project = prepare_project(version)
    out = f'{project}/Builds/{target}-{platform}'
    remove_dir(out)

    if platform == 'android':
        build_target, output = platform, f'{out}/{target}.apk'
    elif platform == 'windows':
        build_target, output = DESKTOP_TARGET, f'{out}/{target}{DESKTOP_SUFFIX}'
    else:
        build_target, output = platform, out

    info('Building the app with Unity ...')
    args = ['-projectPath', project, '-buildTarget', build_target, '-executeMethod', 'AdjustAppBuilder.Build',
            '-adjustScene', app['scene'], '-adjustPackage', app['package'], '-adjustMode', mode, '-adjustOutput', output,
            '-adjustBackend', 'il2cpp' if il2cpp else 'mono']
    run_unity(version, f'{project}/build-{target}-{platform}.log', args)

    if platform == 'android':
        run(['adb', 'uninstall', app['package']], allow_failure=True)
        run(['adb', 'install', '-r', f'{out}/{target}.apk'])
        run(['adb', 'shell', 'monkey', '-p', app['package'], '1'])
        return

    if platform == 'windows':
        run_desktop_app(target, output, tests)
        return

    # sign with the team of the first Apple Development certificate in the keychain
    team = output(['sh', '-c', 'security find-certificate -c "Apple Development" -p | openssl x509 -noout -subject'
                               " | grep -oE 'OU ?= ?[A-Z0-9]{10}' | grep -oE '[A-Z0-9]{10}$'"])
    if not team:
        error('No Apple Development certificate found. Fix: sign in to Xcode with your Apple ID')
        sys.exit(1)

    info('Building the app with Xcode ...')
    # Xcode 27 builds for iOS 15.0 and newer only, while the Adjust pods still say 12.0
    run(['xcodebuild', '-workspace', f'{out}/Unity-iPhone.xcworkspace', '-scheme', 'Unity-iPhone', '-configuration', mode.capitalize(),
         '-destination', 'generic/platform=iOS', '-derivedDataPath', f'{out}/build', '-allowProvisioningUpdates',
         f'DEVELOPMENT_TEAM={team}', 'CODE_SIGN_STYLE=Automatic', 'IPHONEOS_DEPLOYMENT_TARGET=15.0', 'build'])

    udid = output(['sh', '-c', "xcrun devicectl list devices --hide-headers | grep -w connected"
                              " | grep -oE '[0-9A-F]{8}-[0-9A-F-]{16,27}' | head -1"])
    if not udid:
        error('No connected iOS device found.')
        sys.exit(1)
    info(f'Installing and launching on {udid} ...')
    run(['xcrun', 'devicectl', 'device', 'uninstall', 'app', '--device', udid, app['package']], allow_failure=True)
    run(['sh', '-c', f'xcrun devicectl device install app --device {udid} "{out}"/build/Build/Products/*-iphoneos/*.app'])
    run(['xcrun', 'devicectl', 'device', 'process', 'launch', '--device', udid, app['package']])

# starts the desktop player and returns; the test app quits by itself when the session is over
def run_desktop_app(target, app, tests):
    executable = glob.glob(f'{app}/Contents/MacOS/*')[0] if DESKTOP_SUFFIX == '.app' else app
    log = f'{os.path.dirname(app)}/{target}.log'
    env = dict(os.environ)
    if target == 'test-app':
        # TestApp.Start() reads these and starts the session without the button
        env['ADJUST_TEST_AUTOSTART'] = '1'
        env['ADJUST_TEST_NAMES'] = tests
    info(f'Launching {app}, log: {log} ...')
    subprocess.Popen([executable, '-logFile', log], env=env, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)

def main():
    parser = argparse.ArgumentParser(
        description='Build and run the Adjust Unity SDK apps.',
        epilog='examples:\n'
               '  ./unity.py build-native test-library android [debug|release]\n'
               '  ./unity.py build-native test-library ios [debug|release]\n'
               '  ./unity.py build-native test-options android [debug|release]\n'
               '  ./unity.py build-native sdk windows\n'
               '  ./unity.py run example-app android\n'
               '  ./unity.py run test-app ios\n'
               '  ./unity.py run test-app android --unity 2022.3.62f3\n'
               '  ./unity.py run test-app windows --tests "session-count/,Test_Event_tracking"\n',
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('action', choices=['build-native', 'run'])
    parser.add_argument('target', choices=['sdk', 'test-library', 'test-options', 'example-app', 'test-app'])
    parser.add_argument('platform', choices=['android', 'ios', 'windows'])
    parser.add_argument('mode', nargs='?', default='debug', choices=['debug', 'release'])
    parser.add_argument('--unity', help='Unity version to build with, newest installed release by default')
    parser.add_argument('--il2cpp', action='store_true', help='windows only: build the player with IL2CPP instead of Mono')
    parser.add_argument('--tests', help='windows test app only: comma separated tests and "directory/" entries to run, '
                                        'or "all" for every test the server has; the tests the .NET SDK supports by default')
    args = parser.parse_args()

    if args.action == 'build-native' and args.target not in ['sdk', 'test-library', 'test-options']:
        parser.error('build-native takes sdk, test-library or test-options')
    if args.action == 'run' and args.target not in ['example-app', 'test-app']:
        parser.error('run takes example-app or test-app')
    if args.target == 'test-options' and args.platform == 'ios':
        parser.error('test-options exists on android only')
    if args.target == 'sdk' and args.platform != 'windows':
        parser.error('sdk is built from source on windows only, android and ios get theirs through EDM4U')
    if args.tests and (args.target, args.platform) != ('test-app', 'windows'):
        parser.error('--tests works with the windows test app only')

    if args.action == 'build-native':
        if args.target == 'sdk':
            build_dotnet('AdjustSdk.DotNet', 'release', f'{ROOT}/Assets/Adjust/Native/Windows')
        elif args.target == 'test-library':
            build_test_library(args.platform, args.mode)
        else:
            build_android_aar('test-options', args.mode)
    else:
        version = unity_version(args.unity)
        check_setup(args.platform, version)
        tests = None
        if args.target == 'test-app':
            if args.platform == 'windows':
                tests = '' if args.tests == 'all' else args.tests or supported_tests()
            build_test_library(args.platform, args.mode)
            if args.platform == 'android':
                build_android_aar('test-options', args.mode)
        if args.platform == 'windows':
            # the SDK ships inside the package, so the player gets a fresh build of it
            build_dotnet('AdjustSdk.DotNet', 'release', f'{ROOT}/Assets/Adjust/Native/Windows')
        run_app(args.target, args.platform, args.mode, version, tests, args.il2cpp)

if __name__ == '__main__':
    try:
        main()
    except (subprocess.CalledProcessError, FileNotFoundError) as failure:
        error(f'Failed: {failure}')
        sys.exit(1)
