#!/usr/bin/env python3
import sys
sys.dont_write_bytecode = True

import argparse, glob, hashlib, json, os, shutil, socket, subprocess, tempfile, time
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


def native_source_state(sdk):
    # what a native build is made from: the checked-out commit, uncommitted changes to tracked files and
    # the contents of untracked files Git does not ignore (new sources); ignored files, such as build output, don't count
    digest = hashlib.sha256(subprocess.check_output(['git', '-C', sdk, 'diff', 'HEAD', '--binary']))
    untracked = subprocess.check_output(['git', '-C', sdk, 'ls-files', '--others', '--exclude-standard', '-z'])
    for path in sorted(filter(None, untracked.split(b'\0'))):
        full = os.path.join(sdk, os.fsdecode(path))
        digest.update(path + b'\0')
        if os.path.islink(full):
            digest.update(os.fsencode(os.readlink(full)))
        else:
            with open(full, 'rb') as file:
                digest.update(file.read())
    return f'{output(["git", "-C", sdk, "rev-parse", "HEAD"])} {digest.hexdigest()}'


def require_committed_native_source():
    # a release package is built only from committed native source: list what isn't, and leave it alone
    for sdk in (ANDROID_SDK, IOS_SDK):
        require_dir(sdk)
        changes = output(['git', '-C', sdk, 'status', '--porcelain', '--untracked-files=all'])
        if changes:
            error(f'{sdk} has uncommitted or untracked changes; a release is packed only from a committed native revision:')
            for line in changes.splitlines():
                error(f'  {line}')
            sys.exit(1)


def build_native(target, platform, force=True):
    sdk, libs = (ANDROID_SDK, ANDROID_LIBS) if platform == 'android' else (IOS_SDK, IOS_LIBS)
    require_dir(sdk)

    # native builds take minutes, so `run` repeats one only when the native source has changed since the last
    # build (a new submodule commit, an edit or a new untracked file) or its output is gone; `build-native` always builds
    name = f'{platform}-{target}'
    state = f'{target} {native_source_state(sdk)}'
    stamp = f'{ARTIFACTS}/native/{name}'
    built = all(os.path.exists(path) for path in libs[target].values())
    if not force and built and os.path.isfile(stamp) and open(stamp).read() == state:
        info(f'Native {name} is already built from the current native source.')
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


# how long to wait for a connected Android device to finish booting
ANDROID_BOOT_TIMEOUT = 300


def android_devices():
    # serial -> state for every device `adb devices` lists; only 'device' can be installed on,
    # the others are e.g. 'offline' (still booting) or 'unauthorized' (USB debugging not allowed yet)
    devices = {}
    for line in output(['adb', 'devices']).splitlines()[1:]:
        fields = line.split()
        if len(fields) >= 2:
            devices[fields[0]] = fields[1]
    return devices


def find_android_device(serial):
    devices = android_devices()
    ready = [name for name, state in devices.items() if state == 'device']
    not_ready = [f'{name} ({state})' for name, state in devices.items() if state != 'device']
    if serial:
        if serial not in ready:
            error(f'Android device {serial} is not ready: {devices.get(serial, "not connected")}.')
            sys.exit(1)
        return serial
    if not ready:
        error('No connected Android device is ready.' + (f' Not ready: {", ".join(not_ready)}' if not_ready else ''))
        sys.exit(1)
    if len(ready) > 1:
        error(f'More than one Android device is ready: {", ".join(ready)}. Fix: pick one with --device <serial>')
        sys.exit(1)
    return ready[0]


def wait_for_android_boot(serial):
    deadline = time.monotonic() + ANDROID_BOOT_TIMEOUT
    waiting = False
    while True:
        try:
            if output(['adb', '-s', serial, 'shell', 'getprop', 'sys.boot_completed']) == '1':
                return
        except subprocess.CalledProcessError:
            pass
        if time.monotonic() >= deadline:
            error(f'{serial} did not finish booting within {ANDROID_BOOT_TIMEOUT} seconds.')
            sys.exit(1)
        if not waiting:
            info(f'Waiting for {serial} to finish booting ...')
            waiting = True
        time.sleep(2)


def find_ios_simulator(name):
    # the booted simulator to run on: the one named (by name or UDID), or the only one booted
    booted = json.loads(output(['xcrun', 'simctl', 'list', 'devices', 'booted', '--json']))['devices']
    simulators = [simulator for runtime in booted.values() for simulator in runtime]
    if name:
        match = next((simulator for simulator in simulators if name in (simulator['name'], simulator['udid'])), None)
        if not match:
            error(f'No booted iOS simulator is named {name}. Booted: '
                  + (', '.join(f'{simulator["name"]} ({simulator["udid"]})' for simulator in simulators) or 'none'))
            sys.exit(1)
        return match['udid']
    if len(simulators) > 1:
        error('More than one iOS simulator is booted: '
              + ', '.join(f'{simulator["name"]} ({simulator["udid"]})' for simulator in simulators)
              + '. Fix: pick one with --device <name or UDID>')
        sys.exit(1)
    return simulators[0]['udid'] if simulators else None


def find_device(platform, simulator, name=None):
    if platform == 'android':
        device = find_android_device(name)
        wait_for_android_boot(device)
        return device
    elif simulator:
        device = find_ios_simulator(name)
        problem = 'No booted iOS simulator found. Fix: open the Simulator app and boot a device'
    else:
        # devicectl checks a named device itself when installing
        device = name or connected_ios_device()
        problem = 'No connected iOS device found.'
    if not device:
        error(problem)
        sys.exit(1)
    return device


def local_ip():
    # the address other devices on the network reach this machine at; connecting a UDP socket sends nothing.
    # None without a network route: the test apps then use their own default (the simulator's or emulator's host)
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
            probe.connect(('10.255.255.255', 1))
            return probe.getsockname()[0]
    except OSError as failure:
        info(f'No network address found ({failure}); the test app uses its default test server address.')
        return None


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


def build_ios_app(project, build):
    # build, and ask the iOS SDK where this very build put the app bundle (_AppBundlePath, relative to the project):
    # other target frameworks may have left older bundles next to it. -getProperty needs an explicit -t:Build,
    # or MSBuild only evaluates the project; -getResultOutputFile keeps the build log on the console
    with tempfile.TemporaryDirectory() as temp:
        result = f'{temp}/app-bundle-path'
        run(build + ['-t:Build', '-getProperty:_AppBundlePath', f'-getResultOutputFile:{result}'])
        with open(result) as file:
            bundle = file.read().strip()
    app_bundle = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(project)), bundle)) if bundle else None
    if not app_bundle or not os.path.isdir(app_bundle):
        error(f'The build did not produce an .app bundle (reported: {bundle or "nothing"}).')
        sys.exit(1)
    return app_bundle


def run_app(target, platform, mode, simulator, version, device_name=None):
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
        ip = local_ip()
        if ip:
            build.append(f'-p:TestServerIp={ip}')

    # look for the device first: without one the .NET build runs to the end before the run fails
    device = find_device(platform, simulator, device_name)
    for native in app.get('native', {}).get(platform, []):
        build_native(native, platform, force=False)
    use_dotnet(version)

    if platform == 'android':
        # name the device everywhere: with more than one connected, adb and the Run target refuse to pick
        run(['adb', '-s', device, 'uninstall', PACKAGE], allow_failure=True)
        info(f'Building and running the app on {device} ...')
        run(build + ['-t:Run', f'-p:AdbTarget=-s {device}'])
        return

    runtime = 'iossimulator-arm64' if simulator else 'ios-arm64'
    info('Building the app ...')
    # the .NET 10 iOS workload builds apps only with the one Xcode version it was released for, unless told otherwise
    app_bundle = build_ios_app(project, build + [f'-p:RuntimeIdentifier={runtime}', '-p:ValidateXcodeVersion=false'])

    # .NET deploys through mlaunch, which lags behind new Xcode and iOS versions, so install ourselves
    info(f'Installing and launching on {device} ...')
    if simulator:
        run(['xcrun', 'simctl', 'install', device, app_bundle])
        run(['xcrun', 'simctl', 'launch', '--terminate-running-process', device, PACKAGE])
    else:
        run(['xcrun', 'devicectl', 'device', 'install', 'app', '--device', device, app_bundle])
        run(['xcrun', 'devicectl', 'device', 'process', 'launch', '--terminate-existing', '--device', device, PACKAGE])


def pack():
    # the packages ship the native libraries, so build them again from committed source, never from a cache
    require_committed_native_source()
    for platform, target in [('android', 'sdk'), ('android', 'plugins'), ('ios', 'sdk')]:
        build_native(target, platform, force=True)

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
               '  ./maui.py run example-app android --device emulator-5554\n'
               '  ./maui.py run test-app ios\n'
               '  ./maui.py run test-app ios --simulator\n'
               '  ./maui.py run test-app ios --simulator --device "iPhone 17 Pro"\n'
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
    parser.add_argument('--device', help='the device to run on when more than one is available: an Android serial, '
                                         'an iOS simulator name or UDID (with --simulator) or an iOS device UDID')
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
    if args.device and args.action != 'run':
        parser.error('--device applies to running an app only')

    check_setup(args.platform)
    if args.action == 'build-native':
        build_native(args.target, args.platform)
    else:
        run_app(args.target, args.platform, args.mode, args.simulator, 'net10' if args.net10 else 'net8', args.device)


if __name__ == '__main__':
    try:
        main()
    except (subprocess.CalledProcessError, FileNotFoundError) as failure:
        error(f'Failed: {failure}')
        sys.exit(1)
