#!/usr/bin/env python3
import sys
sys.dont_write_bytecode = True

import argparse, glob, json, os, shutil, socket, subprocess, tempfile
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
    # the native build leaves a device and a simulator framework behind, and build_ios joins the two into this one
    'test-library': {
        f'{IOS_SDK}/sdk_distribution/test-static-xcframework/AdjustTestLibrary.xcframework':
            f'{ROOT}/test/plugin/TestLibrary.iOSBinding/AdjustTestLibrary.xcframework',
    },
}

# every app is installed under the same ID
PACKAGE = 'com.adjust.examples'

# 'native' are the native libraries an app needs built before it can be built itself.
# Apps with 'packages' take the SDK from the NuGet packages that `pack` builds, not from the source.
# The MAUI apps have one project for both platforms and a second one for .NET 10 ({net});
# the plain .NET apps have one project per platform ({platform}) and are .NET 8 only.
APPS = {
    'example-app': {
        'project': f'{ROOT}/example/maui/ExampleApp{{net}}.csproj',
        'native': {'android': ['sdk', 'plugins'], 'ios': ['sdk']},
    },
    'nuget-example-app': {
        'project': f'{ROOT}/example/maui/ExampleApp-Nuget{{net}}.csproj',
        'packages': True,
    },
    'test-app': {
        'project': f'{ROOT}/test/app/maui/TestApp{{net}}.csproj',
        'native': {'android': ['sdk', 'test-library'], 'ios': ['sdk', 'test-library']},
    },
    'dotnet-example-app': {
        'project': f'{ROOT}/example/dotnet/DotNetExample{{platform}}/DotNetExample{{platform}}.csproj',
        'packages': True,
    },
    'dotnet-test-app': {
        'project': f'{ROOT}/test/app/dotnet/DotNetTest{{platform}}/DotNetTest{{platform}}.csproj',
        # the test library bindings are built from source, and the Android one needs the SDK's .aar next to it
        'native': {'android': ['sdk', 'test-library'], 'ios': ['test-library']},
        'packages': True,
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


def join_ios_test_library(xcframework):
    # one xcframework holds both builds, so an app builds for a device and for the simulator without a rebuild
    frameworks = f'{IOS_SDK}/sdk_distribution/test-static-framework-'
    with tempfile.TemporaryDirectory() as temp:
        # the device framework also carries an Intel simulator build, and an xcframework takes one platform per framework
        device = f'{temp}/AdjustTestLibrary.framework'
        shutil.copytree(f'{frameworks}device/AdjustTestLibrary.framework', device, symlinks=True)
        binary = os.path.realpath(f'{device}/AdjustTestLibrary')
        run(['lipo', '-thin', 'arm64', binary, '-output', binary])
        remove_dir(xcframework)
        run(['xcodebuild', '-create-xcframework', '-framework', device,
             '-framework', f'{frameworks}simulator/AdjustTestLibrary.framework', '-output', xcframework])


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
            change_dir(f'{IOS_SDK}/AdjustTests/AdjustTestLibrary')
            for library in ['AdjustTestLibraryStatic', 'AdjustTestLibraryStaticSimulatorOnly']:
                run(['xcodebuild', '-project', 'AdjustTestLibrary.xcodeproj', '-target', library,
                     '-configuration', 'Debug', 'clean', 'build'], env=env)
            join_ios_test_library(next(iter(IOS_LIBS[target])))

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
    name = f'{platform}-{target}'
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


def local_ip():
    # the address other devices on the network reach this machine at; connecting a UDP socket sends nothing
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
        probe.connect(('10.255.255.255', 1))
        return probe.getsockname()[0]


def local_packages():
    packages = glob.glob(f'{PACKAGES}/*.nupkg')
    if not packages:
        error('No packages found. Fix: ./maui.py pack')
        sys.exit(1)
    # NuGet keeps its own unpacked copy of every package version it has seen and would keep using
    # the one from an earlier pack, so drop its copies of the packages we are about to install
    version = open(f'{ROOT}/VERSION').read().strip()
    for package in packages:
        name = os.path.basename(package)[:-len(f'.{version}.nupkg')].lower()
        remove_dir(os.path.expanduser(f'~/.nuget/packages/{name}/{version}'))
    return f'-p:RestoreAdditionalProjectSources={PACKAGES}'


def run_app(target, platform, mode, simulator, version):
    app = APPS[target]
    plain = '{platform}' in app['project']
    project = app['project'].format(net='-Net10' if version == 'net10' else '', platform=platform.capitalize())
    config = mode.capitalize()
    build = ['dotnet', 'build', project, '-c', config]
    if not plain:
        # the MAUI projects build for both platforms, so say which one
        build += ['-f', DOTNET[version][platform]]
    if app.get('packages'):
        build.append(local_packages())
    if target.endswith('test-app'):
        # the test apps connect to the test server on this machine
        build.append(f'-p:TestServerIp={local_ip()}')

    # look for the device first: without one the .NET build runs to the end before the run fails
    device = find_device(platform, simulator)
    for native in app.get('native', {}).get(platform, []):
        build_native(native, platform, force=False)
    use_dotnet(version)

    if platform == 'android':
        run(['adb', 'uninstall', PACKAGE], allow_failure=True)
        info('Building and running the app ...')
        run(build + ['-t:Run'])
        return

    runtime = 'iossimulator-arm64' if simulator else 'ios-arm64'
    info('Building the app ...')
    # the .NET 10 iOS workload builds apps only with the one Xcode version it was released for, unless told otherwise
    run(build + [f'-p:RuntimeIdentifier={runtime}', '-p:ValidateXcodeVersion=false'])
    name = os.path.splitext(os.path.basename(project))[0]
    built = glob.glob(f'{ARTIFACTS}/{name}/bin/{config}/*/{runtime}/*.app')
    if not built:
        error('The build did not produce an .app bundle.')
        sys.exit(1)

    # .NET deploys through mlaunch, which lags behind new Xcode and iOS versions, so install ourselves
    info(f'Installing and launching on {device} ...')
    if simulator:
        run(['xcrun', 'simctl', 'install', device, built[0]])
        run(['xcrun', 'simctl', 'launch', '--terminate-running-process', device, PACKAGE])
    else:
        run(['xcrun', 'devicectl', 'device', 'install', 'app', '--device', device, built[0]])
        run(['xcrun', 'devicectl', 'device', 'process', 'launch', '--terminate-existing', '--device', device, PACKAGE])


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
               '  ./maui.py run example-app android\n'
               '  ./maui.py run test-app ios\n'
               '  ./maui.py run test-app ios --simulator\n'
               '  ./maui.py run example-app android release --net10\n'
               '  ./maui.py run nuget-example-app ios\n'
               '  ./maui.py run dotnet-example-app android\n'
               '  ./maui.py run dotnet-test-app ios\n'
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
    if args.simulator and (args.action == 'build-native' or args.platform == 'android'):
        parser.error('--simulator applies to running an app on ios only')
    if args.net10 and args.target.startswith('dotnet-'):
        parser.error('the plain .NET apps are .NET 8 only')

    check_setup(args.platform)
    if args.action == 'build-native':
        build_native(args.target, args.platform)
    else:
        run_app(args.target, args.platform, args.mode, args.simulator, 'net10' if args.net10 else 'net8')


if __name__ == '__main__':
    try:
        main()
    except (subprocess.CalledProcessError, FileNotFoundError) as failure:
        error(f'Failed: {failure}')
        sys.exit(1)
