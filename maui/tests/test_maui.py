#!/usr/bin/env python3
# Unit tests for maui.py. They replace every external command, so they need no device, Gradle or Xcode.
# Run from the repository root: python3 -m unittest discover -s maui/tests
import sys
sys.dont_write_bytecode = True

import importlib.util, json, os, subprocess, tempfile, unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('maui', os.path.join(HERE, '..', 'maui.py'))
maui = importlib.util.module_from_spec(spec)
spec.loader.exec_module(maui)


class QuietTestCase(unittest.TestCase):
    def setUp(self):
        for name in ('info', 'error'):
            patcher = mock.patch.object(maui, name)
            patcher.start()
            self.addCleanup(patcher.stop)


ADB_DEVICES = '''List of devices attached
emulator-5554\tdevice
R58M123ABC\tunauthorized
emulator-5556\toffline
'''


class AndroidDeviceTest(QuietTestCase):
    def devices(self, text):
        return mock.patch.object(maui, 'output', return_value=text)

    def test_reads_every_listed_state(self):
        with self.devices(ADB_DEVICES):
            self.assertEqual(maui.android_devices(),
                             {'emulator-5554': 'device', 'R58M123ABC': 'unauthorized', 'emulator-5556': 'offline'})

    def test_picks_the_only_ready_device(self):
        with self.devices(ADB_DEVICES):
            self.assertEqual(maui.find_android_device(None), 'emulator-5554')

    def test_stops_when_no_device_is_ready(self):
        with self.devices('List of devices attached\nR58M123ABC\tunauthorized\n'), self.assertRaises(SystemExit):
            maui.find_android_device(None)

    def test_stops_when_several_are_ready_and_none_is_named(self):
        with self.devices('List of devices attached\nemulator-5554\tdevice\nR58M123ABC\tdevice\n'), \
                self.assertRaises(SystemExit):
            maui.find_android_device(None)

    def test_takes_the_named_device(self):
        with self.devices('List of devices attached\nemulator-5554\tdevice\nR58M123ABC\tdevice\n'):
            self.assertEqual(maui.find_android_device('R58M123ABC'), 'R58M123ABC')

    def test_stops_when_the_named_device_is_not_ready(self):
        with self.devices(ADB_DEVICES), self.assertRaises(SystemExit):
            maui.find_android_device('R58M123ABC')

    @staticmethod
    def adb_answers(*answers):
        # each answer is the getprop output, or an exception adb's run raises (e.g. a timeout)
        answers = iter(answers)

        def adb(cmd, **kwargs):
            answer = next(answers)
            if isinstance(answer, Exception):
                raise answer
            return subprocess.CompletedProcess(cmd, 0 if answer is not None else 1, stdout=f'{answer or ""}\n')
        return mock.patch.object(maui.subprocess, 'run', side_effect=adb)

    def test_waits_until_booted(self):
        with self.adb_answers(None, '', '1') as run, mock.patch.object(maui.time, 'sleep'):
            maui.wait_for_android_boot('emulator-5554')
        self.assertEqual(run.call_count, 3)
        self.assertEqual(run.call_args.args[0], ['adb', '-s', 'emulator-5554', 'shell', 'getprop', 'sys.boot_completed'])

    def test_boot_wait_times_out(self):
        clock = iter([0, 0, 1, maui.ANDROID_BOOT_TIMEOUT + 1])
        with self.adb_answers('0'), \
                mock.patch.object(maui.time, 'monotonic', side_effect=lambda: next(clock)), \
                mock.patch.object(maui.time, 'sleep'), self.assertRaises(SystemExit):
            maui.wait_for_android_boot('emulator-5554')

    def test_each_adb_call_is_bounded_by_the_time_left(self):
        # adb hangs until it is killed: the first check gets the whole wait, and the deadline then ends it
        now = [0.0]

        def hang(cmd, timeout, **kwargs):
            now[0] += timeout
            raise subprocess.TimeoutExpired(cmd, timeout)

        with mock.patch.object(maui.subprocess, 'run', side_effect=hang) as run, \
                mock.patch.object(maui.time, 'monotonic', side_effect=lambda: now[0]), \
                mock.patch.object(maui.time, 'sleep'), self.assertRaises(SystemExit):
            maui.wait_for_android_boot('emulator-5554')
        # killed at the deadline, so an answer adb would only have given later never counts as booted
        self.assertEqual(run.call_count, 1)
        self.assertEqual(run.call_args.kwargs['timeout'], maui.ANDROID_BOOT_TIMEOUT)


def simctl_booted(*simulators):
    return json.dumps({'devices': {'com.apple.CoreSimulator.SimRuntime.iOS-27-0': [
        {'name': name, 'udid': udid, 'state': 'Booted'} for name, udid in simulators]}})


IPHONE = ('iPhone 17 Pro', 'AAAA-1111')
IPAD = ('iPad Air', 'BBBB-2222')


class IosDeviceTest(QuietTestCase):
    def booted(self, *simulators):
        return mock.patch.object(maui, 'output', return_value=simctl_booted(*simulators))

    def test_picks_the_only_booted_simulator(self):
        with self.booted(IPHONE):
            self.assertEqual(maui.find_device('ios', True), 'AAAA-1111')

    def test_stops_when_none_is_booted(self):
        with self.booted(), self.assertRaises(SystemExit):
            maui.find_device('ios', True)

    def test_stops_when_several_are_booted_and_none_is_named(self):
        with self.booted(IPHONE, IPAD), self.assertRaises(SystemExit):
            maui.find_device('ios', True)

    def test_takes_the_simulator_named_by_name_or_udid(self):
        with self.booted(IPHONE, IPAD):
            self.assertEqual(maui.find_device('ios', True, 'iPad Air'), 'BBBB-2222')
            self.assertEqual(maui.find_device('ios', True, 'AAAA-1111'), 'AAAA-1111')

    def test_stops_when_the_named_simulator_is_not_booted(self):
        with self.booted(IPHONE), self.assertRaises(SystemExit):
            maui.find_device('ios', True, 'iPad Air')

    def test_takes_the_named_physical_device(self):
        with mock.patch.object(maui, 'connected_ios_device') as connected:
            self.assertEqual(maui.find_device('ios', False, '00008110-000A'), '00008110-000A')
        connected.assert_not_called()


def git(repo, *args):
    subprocess.check_call(['git', '-C', repo, '-c', 'user.name=test', '-c', 'user.email=test@example.com', *args],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as file:
        file.write(text)


class NativeCheckoutTestCase(QuietTestCase):
    # a real Git repository stands in for the native checkout; only the native build itself is replaced
    def setUp(self):
        super().setUp()
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        # laid out like the MAUI repository: the native checkout sits at <root>/ext/android/sdk
        self.root = os.path.join(temp.name, 'maui')
        self.native = os.path.join(self.root, 'ext', 'android', 'sdk')
        self.artifact = os.path.join(temp.name, 'out', 'adjust-android.aar')
        os.makedirs(self.native)
        git(self.native, 'init', '-q')
        write(f'{self.native}/.gitignore', 'build/\n')
        write(f'{self.native}/src/Adjust.java', 'version one')
        git(self.native, 'add', '-A')
        git(self.native, 'commit', '-q', '-m', 'initial')

        self.builds = []

        def build_android(target):
            self.builds.append(target)
            write(self.artifact, 'built')

        for name, value in (('ANDROID_SDK', self.native), ('IOS_SDK', self.native),
                            ('ANDROID_LIBS', {'sdk': {'sdk-core': self.artifact}}),
                            ('ARTIFACTS', os.path.join(temp.name, 'artifacts')), ('build_android', build_android)):
            patcher = mock.patch.object(maui, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

class NativeBuildCacheTest(NativeCheckoutTestCase):
    def build(self):
        maui.build_native('sdk', 'android', force=False)
        return len(self.builds)

    def test_reuses_a_build_of_unchanged_source(self):
        self.assertEqual(self.build(), 1)
        self.assertEqual(self.build(), 1)

    def test_rebuilds_after_a_tracked_edit(self):
        self.build()
        write(f'{self.native}/src/Adjust.java', 'version two')
        self.assertEqual(self.build(), 2)

    def test_rebuilds_after_a_new_untracked_source(self):
        self.build()
        write(f'{self.native}/src/UntrackedNativeSource.java', 'new')
        self.assertEqual(self.build(), 2)
        write(f'{self.native}/src/UntrackedNativeSource.java', 'changed')
        self.assertEqual(self.build(), 3)

    def test_ignores_ignored_files(self):
        self.build()
        write(f'{self.native}/build/output.txt', 'build output')
        self.assertEqual(self.build(), 1)

    def test_rebuilds_after_a_new_commit(self):
        self.build()
        write(f'{self.native}/src/Adjust.java', 'version two')
        git(self.native, 'commit', '-q', '-am', 'second')
        self.assertEqual(self.build(), 2)

    def test_rebuilds_when_the_output_is_gone(self):
        self.build()
        os.remove(self.artifact)
        self.assertEqual(self.build(), 2)


class PackTest(NativeCheckoutTestCase):
    # the MAUI repository pins the native checkout's current commit, as `git submodule update` leaves it
    def setUp(self):
        super().setUp()
        git(self.root, 'init', '-q')
        self.pin(self.head())
        patcher = mock.patch.object(maui, 'ROOT', self.root)
        patcher.start()
        self.addCleanup(patcher.stop)

    def head(self):
        return subprocess.check_output(['git', '-C', self.native, 'rev-parse', 'HEAD'], text=True).strip()

    def pin(self, commit):
        git(self.root, 'update-index', '--add', '--cacheinfo', f'160000,{commit},ext/android/sdk')
        git(self.root, 'commit', '-q', '--allow-empty', '-m', f'pin {commit}')

    def pack(self):
        with mock.patch.object(maui, 'build_native') as build_native, mock.patch.object(maui, 'use_dotnet'), \
                mock.patch.object(maui, 'run'), mock.patch.object(maui, 'recreate_dir'):
            maui.pack()
        return build_native

    def test_stops_on_a_tracked_edit(self):
        write(f'{self.native}/src/Adjust.java', 'version two')
        with self.assertRaises(SystemExit):
            self.pack()

    def test_stops_on_an_untracked_source(self):
        write(f'{self.native}/src/UntrackedNativeSource.java', 'new')
        with self.assertRaises(SystemExit):
            self.pack()
        self.assertTrue(os.path.exists(f'{self.native}/src/UntrackedNativeSource.java'))

    def test_stops_when_a_clean_checkout_is_not_at_the_pinned_commit(self):
        pinned = self.head()
        write(f'{self.native}/src/Adjust.java', 'version two')
        git(self.native, 'commit', '-q', '-am', 'local commit')
        with self.assertRaises(SystemExit):
            self.pack()
        self.assertNotEqual(self.head(), pinned)

    def test_builds_when_the_pin_moves_to_the_checked_out_commit(self):
        write(f'{self.native}/src/Adjust.java', 'version two')
        git(self.native, 'commit', '-q', '-am', 'new release')
        self.pin(self.head())
        self.assertTrue(self.pack().call_args_list)

    def test_stops_when_nothing_is_pinned(self):
        git(self.root, 'rm', '-q', '--cached', 'ext/android/sdk')
        git(self.root, 'commit', '-q', '-m', 'unpin')
        with self.assertRaises(SystemExit):
            self.pack()

    def test_always_builds_from_clean_source(self):
        write(f'{self.native}/build/output.txt', 'build output')
        build_native = self.pack()
        self.assertTrue(build_native.call_args_list)
        self.assertTrue(all(call.kwargs == {'force': True} for call in build_native.call_args_list))


class RunAppTest(QuietTestCase):
    def setUp(self):
        super().setUp()
        for name, value in (('build_native', None), ('use_dotnet', None), ('local_ip', '192.168.1.20')):
            patcher = mock.patch.object(maui, name, return_value=value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_android_run_targets_the_chosen_device(self):
        with mock.patch.object(maui, 'find_device', return_value='R58M123ABC') as find_device, \
                mock.patch.object(maui, 'run') as run:
            maui.run_app('test-app', 'android', 'debug', False, 'net8', 'R58M123ABC')
        find_device.assert_called_once_with('android', False, 'R58M123ABC')
        uninstall, build = run.call_args_list
        self.assertEqual(uninstall.args[0], ['adb', '-s', 'R58M123ABC', 'uninstall', maui.PACKAGE])
        self.assertIn('-t:Run', build.args[0])
        self.assertIn('-p:AdbTarget=-s R58M123ABC', build.args[0])
        self.assertIn('-p:TestServerIp=192.168.1.20', build.args[0])


class IosAppBundleTest(QuietTestCase):
    # the build is replaced by one that answers -getResultOutputFile the way the iOS SDK does: the
    # _AppBundlePath of this build, relative to the project directory
    def setUp(self):
        super().setUp()
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = temp.name
        self.project = f'{self.root}/test/app/maui/TestApp.csproj'
        write(self.project, '<Project />')

    def build_reporting(self, bundle):
        def run(cmd, **kwargs):
            result = next(argument.split(':', 1)[1] for argument in cmd if argument.startswith('-getResultOutputFile:'))
            write(result, bundle + '\n')
        return mock.patch.object(maui, 'run', side_effect=run)

    def test_installs_the_bundle_this_build_reports(self):
        current = f'{self.root}/.artifacts/TestApp/bin/Debug/net8.0-ios/iossimulator-arm64/TestApp.app'
        stale = f'{self.root}/.artifacts/TestApp/bin/Debug/net8.0-ios18.0/iossimulator-arm64/TestApp.app'
        write(f'{current}/TestApp', 'new build')
        write(f'{stale}/TestApp', 'old build')
        os.utime(current, (1, 1))  # the current bundle's folder looks older; only its contents changed
        with self.build_reporting('../../../.artifacts/TestApp/bin/Debug/net8.0-ios/iossimulator-arm64/TestApp.app/') as run:
            app_bundle = maui.build_ios_app(self.project, ['dotnet', 'build', self.project])
        self.assertEqual(app_bundle, current)
        self.assertIn('-t:Build', run.call_args.args[0])
        self.assertIn('-getProperty:_AppBundlePath', run.call_args.args[0])

    def test_stops_when_the_reported_bundle_is_missing(self):
        with self.build_reporting('bin/Debug/net8.0-ios/iossimulator-arm64/TestApp.app/'), self.assertRaises(SystemExit):
            maui.build_ios_app(self.project, ['dotnet', 'build', self.project])

    def test_stops_when_nothing_is_reported(self):
        with self.build_reporting(''), self.assertRaises(SystemExit):
            maui.build_ios_app(self.project, ['dotnet', 'build', self.project])


class LocalPackagesTest(QuietTestCase):
    def setUp(self):
        super().setUp()
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.packages = f'{temp.name}/.artifacts/packages'
        write(f'{temp.name}/VERSION', '5.8.0\n')
        for name, value in (('ROOT', temp.name), ('PACKAGES', self.packages)):
            patcher = mock.patch.object(maui, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_drops_only_nugets_cached_copies_of_the_packed_versions(self):
        for package in ('Adjust.Maui.Sdk', 'Adjust.Maui.Sdk.Meta.Referrer', 'Adjust.Maui.Sdk.Google.LVL'):
            write(f'{self.packages}/{package}.5.8.0.nupkg', '')
        with mock.patch.object(maui, 'remove_dir') as remove_dir:
            argument = maui.local_packages()
        self.assertEqual(argument, f'-p:RestoreAdditionalProjectSources={self.packages}')
        cache = os.path.expanduser('~/.nuget/packages')
        self.assertEqual(sorted(call.args[0] for call in remove_dir.call_args_list), [
            f'{cache}/adjust.maui.sdk.google.lvl/5.8.0',
            f'{cache}/adjust.maui.sdk.meta.referrer/5.8.0',
            f'{cache}/adjust.maui.sdk/5.8.0',
        ])

    def test_stops_when_nothing_was_packed(self):
        os.makedirs(self.packages)
        with mock.patch.object(maui, 'remove_dir') as remove_dir, self.assertRaises(SystemExit):
            maui.local_packages()
        remove_dir.assert_not_called()


class LocalIpTest(QuietTestCase):
    def test_returns_none_without_a_network_route(self):
        with mock.patch.object(maui.socket.socket, 'connect', side_effect=OSError(51, 'Network is unreachable')):
            self.assertIsNone(maui.local_ip())

    def test_test_app_build_leaves_the_address_out_when_offline(self):
        with mock.patch.object(maui, 'local_ip', return_value=None), \
                mock.patch.object(maui, 'find_device', return_value='emulator-5554'), \
                mock.patch.object(maui, 'build_native'), mock.patch.object(maui, 'use_dotnet'), \
                mock.patch.object(maui, 'run') as run:
            maui.run_app('test-app', 'android', 'debug', False, 'net8')
        build = run.call_args_list[-1].args[0]
        self.assertFalse(any(argument.startswith('-p:TestServerIp') for argument in build))


if __name__ == '__main__':
    unittest.main()
