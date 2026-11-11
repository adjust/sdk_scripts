#!/usr/bin/env python3
import sys
sys.dont_write_bytecode = True

import argparse, glob, json, os, shutil, subprocess, tempfile
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from utils import *

set_log_tag('MAUI-SDK')

ROOT = root_dir()
ANDROID_SDK = f'{ROOT}/ext/android/sdk'
IOS_SDK = f'{ROOT}/ext/ios/sdk'
ARTIFACTS = f'{ROOT}/.artifacts'
PACKAGES = f'{ARTIFACTS}/packages'

# lowest iOS version Xcode 27 still builds for
IOS_DEPLOYMENT_TARGET = '15.0'

# the projects pick their target frameworks from the .NET SDK in use, and global.json picks that SDK
DOTNET = {
    'net8': {
        'sdk': {'version': '8.0.402', 'rollForward': 'latestFeature'},
        'android': 'net8.0-android',
        'ios': 'net8.0-ios',
    },
    'net10': {
        'sdk': {'version': '10.0.101', 'rollForward': 'latestFeature', 'workloadVersion': '10.0.302.1'},
        'android': 'net10.0-android36.0',
        'ios': 'net10.0-ios26.5',
    },
}

# native Android libraries: gradle module -> where its release .aar goes
ANDROID_LIBS = {
    'sdk': {
        'sdk-core': f'{ROOT}/android/AdjustSdk.AndroidBinding/libs/adjust-android.aar',
    },
    'plugins': {
        'plugins/sdk-plugin-oaid': f'{ROOT}/android/AdjustOaid.AndroidBinding/libs/adjust-android-oaid.aar',
        'plugins/sdk-plugin-meta-referrer': f'{ROOT}/android/AdjustMetaReferrer.AndroidBinding/libs/adjust-android-meta-referrer.aar',
        'plugins/sdk-plugin-google-lvl': f'{ROOT}/android/AdjustGoogleLVL.AndroidBinding/libs/adjust-android-google-lvl.aar',
    },
    'test-library': {
        'tests/test-library': f'{ROOT}/test/plugin/TestLibrary.AndroidBinding/libs/test-library.aar',
        'tests/test-options': f'{ROOT}/test/plugin/TestLibrary.AndroidBinding/libs/test-options.aar',
    },
}

# native iOS libraries: what the native build leaves behind -> where it goes
IOS_LIBS = {
    'sdk': {
        f'{IOS_SDK}/sdk_distribution/xcframeworks-dynamic/AdjustSdk-iOS-Dynamic-xcframework/AdjustSdk.xcframework':
            f'{ROOT}/ios/AdjustSdk.iOSBinding/AdjustSdk.xcframework',
        f'{IOS_SDK}/AdjustSignature/AdjustSigSdk.xcframework':
            f'{ROOT}/ios/AdjustSdk.iOSBinding/AdjustSigSdk.xcframework',
    },
    'test-library': {
        f'{IOS_SDK}/sdk_distribution/test-static-framework-device/AdjustTestLibrary.framework':
            f'{ROOT}/test/plugin/TestLibrary.iOSBinding/AdjustTestLibrary.framework',
    },
    # the test library is a plain framework, so the simulator needs its own build of it
    'test-library-simulator': {
        f'{IOS_SDK}/sdk_distribution/test-static-framework-simulator/AdjustTestLibrary.framework':
            f'{ROOT}/test/plugin/TestLibrary.iOSBinding/AdjustTestLibrary.framework',
    },
}

# 'native' are the native libraries each app needs built before it can be built itself
APPS = {
    'example-app': {
        'project': f'{ROOT}/example/maui/ExampleApp',
        'package': 'com.adjust.examples',
        'native': {'android': ['sdk', 'plugins'], 'ios': ['sdk']},
    },
    'test-app': {
        'project': f'{ROOT}/test/app/maui/TestApp',
        'package': 'com.adjust.examples',
        'native': {'android': ['sdk', 'test-library'], 'ios': ['sdk', 'test-library']},
    },
}

# NuGet packages: nuspec -> the project that has to be built for it
NUGET_PACKAGES = {
    f'{ROOT}/AdjustSdk.nuspec': f'{ROOT}/AdjustSdk/AdjustSdk.csproj',
    f'{ROOT}/AdjustOaid.nuspec': f'{ROOT}/plugins/AdjustOaid/AdjustOaid.csproj',
    f'{ROOT}/AdjustMetaReferrer.nuspec': f'{ROOT}/plugins/AdjustMetaReferrer/AdjustMetaReferrer.csproj',
    f'{ROOT}/AdjustGoogleLVL.nuspec': f'{ROOT}/plugins/AdjustGoogleLVL/AdjustGoogleLVL.csproj',
}


def build_android(target):
    modules = ANDROID_LIBS[target]
    info(f'Building Android {target} ...')
    change_dir(f'{ANDROID_SDK}/Adjust')
    run(['./gradlew'] + [f':{module.replace("/", ":")}:assembleRelease' for module in modules])
    for module, destination in modules.items():
        copy_file(f'{ANDROID_SDK}/Adjust/{module}/build/outputs/aar/{os.path.basename(module)}-release.aar', destination)


def build_ios(target):
    info(f'Building iOS {target} ...')
    # the native projects are still on iOS 12.0, which Xcode 27 rejects; an xcconfig passed through the
    # environment also reaches the xcodebuild calls that the native build scripts make on their own
    with tempfile.NamedTemporaryFile('w', suffix='.xcconfig') as xcconfig:
        xcconfig.write(f'IPHONEOS_DEPLOYMENT_TARGET = {IOS_DEPLOYMENT_TARGET}\n')
        xcconfig.flush()
        env = {**os.environ, 'XCODE_XCCONFIG_FILE': xcconfig.name}
        if target == 'sdk':
            change_dir(IOS_SDK)
            run(['./scripts/build_frameworks.sh', '-xd', '-ios'], env=env)
        else:
            library = 'AdjustTestLibraryStaticSimulatorOnly' if target.endswith('simulator') else 'AdjustTestLibraryStatic'
            change_dir(f'{IOS_SDK}/AdjustTests/AdjustTestLibrary')
            run(['xcodebuild', '-project', 'AdjustTestLibrary.xcodeproj', '-target', library,
                 '-configuration', 'Debug', 'clean', 'build'], env=env)

    for built, destination in IOS_LIBS[target].items():
        if not os.path.isdir(built):
            error(f'{built} was not produced by the build.')
            sys.exit(1)
        remove_dir(destination)
        shutil.copytree(built, destination, symlinks=True)
        info(f'{built} -> {destination}')


def build_native(target, platform, force=True):
    sdk, libs = (ANDROID_SDK, ANDROID_LIBS) if platform == 'android' else (IOS_SDK, IOS_LIBS)
    require_dir(sdk)

    # native builds take minutes, so `run` and `pack` repeat one only when the native submodule has moved
    # since the last build or its output is gone; `build-native` always builds
    name = f'{platform}-{target.split("-simulator")[0]}'
    state = f'{target} {output(["git", "-C", sdk, "rev-parse", "HEAD"])}'
    stamp = f'{ARTIFACTS}/native/{name}'
    built = all(os.path.exists(path) for path in libs[target].values())
    if not force and built and os.path.isfile(stamp) and open(stamp).read() == state:
        info(f'Native {name} is already built from the current submodule commit.')
        return

    build_android(target) if platform == 'android' else build_ios(target)
    os.makedirs(os.path.dirname(stamp), exist_ok=True)
    with open(stamp, 'w') as file:
        file.write(state)


def use_dotnet(version):
    path = f'{ROOT}/global.json'
    wanted = {'sdk': DOTNET[version]['sdk']}
    if os.path.isfile(path) and json.load(open(path)) == wanted:
        return
    info(f'Switching to {version} ...')
    with open(path, 'w') as file:
        json.dump(wanted, file, indent=2)
    # a build server started for the other .NET version keeps build files locked
    run(['dotnet', 'build-server', 'shutdown'], allow_failure=True)


def check_setup(platform=None):
    tools = [('dotnet', 'install the .NET SDK: https://dotnet.microsoft.com/download')]
    if platform == 'android':
        tools.append(('adb', 'install Android SDK platform-tools and add them to PATH'))
    elif platform == 'ios':
        tools.append(('xcodebuild', 'install Xcode'))
    else:
        tools.append(('nuget', 'brew install nuget'))
    problems = [f'{tool} not found in PATH. Fix: {fix}' for tool, fix in tools if shutil.which(tool) is None]

    if problems:
        error('Setup is incomplete. Fix the following and re-run:')
        for problem in problems:
            error(f'  - {problem}')
        sys.exit(1)


def find_device(platform, simulator):
    if platform == 'android':
        device = output(['adb', 'devices']).splitlines()[1:]
        problem = 'No connected Android device found.'
    elif simulator:
        booted = json.loads(output(['xcrun', 'simctl', 'list', 'devices', 'booted', '--json']))['devices']
        device = next((device['udid'] for runtime in booted.values() for device in runtime), None)
        problem = 'No booted iOS simulator found. Fix: open the Simulator app and boot a device'
    else:
        device = connected_ios_device()
        problem = 'No connected iOS device found.'
    if not device:
        error(problem)
        sys.exit(1)
    return device


def run_app(target, platform, mode, simulator, version):
    app = APPS[target]
    project = app['project'] + ('-Net10' if version == 'net10' else '') + '.csproj'
    framework = DOTNET[version][platform]
    config = mode.capitalize()

    # look for the device first: without one the .NET build runs to the end before the run fails
    device = find_device(platform, simulator)
    for native in app['native'][platform]:
        if native == 'test-library' and simulator:
            native = 'test-library-simulator'
        build_native(native, platform, force=False)
    use_dotnet(version)

    if platform == 'android':
        run(['adb', 'uninstall', app['package']], allow_failure=True)
        info('Building and running the app ...')
        run(['dotnet', 'build', project, '-c', config, '-f', framework, '-t:Run'])
        return

    runtime = 'iossimulator-arm64' if simulator else 'ios-arm64'
    info('Building the app ...')
    # the .NET 10 iOS workload builds apps only with the one Xcode version it was released for, unless told otherwise
    run(['dotnet', 'build', project, '-c', config, '-f', framework, f'-p:RuntimeIdentifier={runtime}',
         '-p:ValidateXcodeVersion=false'])
    name = os.path.splitext(os.path.basename(project))[0]
    built = glob.glob(f'{ARTIFACTS}/{name}/bin/{config}/{framework}/{runtime}/*.app')
    if not built:
        error('The build did not produce an .app bundle.')
        sys.exit(1)

    # .NET deploys through mlaunch, which lags behind new Xcode and iOS versions, so install ourselves
    info(f'Installing and launching on {device} ...')
    if simulator:
        run(['xcrun', 'simctl', 'install', device, built[0]])
        run(['xcrun', 'simctl', 'launch', '--terminate-running-process', device, app['package']])
    else:
        run(['xcrun', 'devicectl', 'device', 'install', 'app', '--device', device, built[0]])
        run(['xcrun', 'devicectl', 'device', 'process', 'launch', '--terminate-existing', '--device', device, app['package']])


def pack():
    for platform, target in [('android', 'sdk'), ('android', 'plugins'), ('ios', 'sdk')]:
        build_native(target, platform, force=False)

    # every package carries both the .NET 8 and the .NET 10 build
    for version in DOTNET:
        use_dotnet(version)
        for project in NUGET_PACKAGES.values():
            info(f'Building {os.path.basename(project)} for {version} ...')
            run(['dotnet', 'build', project, '-c', 'Release'])

    recreate_dir(PACKAGES)
    for nuspec in NUGET_PACKAGES:
        run(['nuget', 'pack', nuspec, '-properties', 'Configuration=Release', '-OutputDirectory', PACKAGES])
    info(f'Packages are in {PACKAGES}')


def main():
    parser = argparse.ArgumentParser(
        description='Build and run the Adjust MAUI SDK apps, and pack the NuGet packages.',
        epilog='examples:\n'
               '  ./maui.py build-native sdk android\n'
               '  ./maui.py build-native plugins android\n'
               '  ./maui.py build-native test-library ios\n'
               '  ./maui.py build-native test-library ios --simulator\n'
               '  ./maui.py run example-app android\n'
               '  ./maui.py run test-app ios\n'
               '  ./maui.py run test-app ios --simulator\n'
               '  ./maui.py run example-app android release --net10\n'
               '  ./maui.py pack\n',
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('action', choices=['build-native', 'run', 'pack'])
    parser.add_argument('target', nargs='?', choices=['sdk', 'plugins', 'test-library', *APPS])
    parser.add_argument('platform', nargs='?', choices=['android', 'ios'])
    parser.add_argument('mode', nargs='?', default='debug', choices=['debug', 'release'])
    parser.add_argument('--simulator', action='store_true', help='run on the booted simulator instead of a connected device')
    parser.add_argument('--net10', action='store_true', help='build the app with .NET 10 instead of .NET 8')
    args = parser.parse_args()

    if args.action == 'pack':
        if args.target or args.platform:
            parser.error('pack takes no target or platform')
        check_setup()
        pack()
        return

    if not args.target or not args.platform:
        parser.error(f'{args.action} needs a target and a platform')
    if args.action == 'build-native' and args.target in APPS:
        parser.error('build-native takes sdk, plugins or test-library')
    if args.action == 'run' and args.target not in APPS:
        parser.error(f'run takes one of: {", ".join(APPS)}')
    if args.target == 'plugins' and args.platform == 'ios':
        parser.error('plugins exist on android only')
    if args.simulator and args.platform == 'android':
        parser.error('--simulator applies to ios only')

    check_setup(args.platform)
    if args.action == 'build-native':
        simulator = args.simulator and args.target == 'test-library'
        build_native(args.target + ('-simulator' if simulator else ''), args.platform)
    else:
        run_app(args.target, args.platform, args.mode, args.simulator, 'net10' if args.net10 else 'net8')


if __name__ == '__main__':
    try:
        main()
    except (subprocess.CalledProcessError, FileNotFoundError) as failure:
        error(f'Failed: {failure}')
        sys.exit(1)
