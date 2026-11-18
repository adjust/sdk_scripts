#!/usr/bin/env python3
# Unit tests for maui.py. They replace every external command, so they need no device, Gradle or Xcode.
# Run from the repository root: python3 -m unittest discover -s maui/tests
import sys
sys.dont_write_bytecode = True

import importlib.util, os, subprocess, unittest
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

    def test_waits_until_booted(self):
        answers = iter([subprocess.CalledProcessError(1, 'adb'), '', '1'])

        def boot_completed(cmd):
            answer = next(answers)
            if isinstance(answer, Exception):
                raise answer
            return answer

        with mock.patch.object(maui, 'output', side_effect=boot_completed) as output, \
                mock.patch.object(maui.time, 'sleep'):
            maui.wait_for_android_boot('emulator-5554')
        self.assertEqual(output.call_count, 3)
        output.assert_called_with(['adb', '-s', 'emulator-5554', 'shell', 'getprop', 'sys.boot_completed'])

    def test_boot_wait_times_out(self):
        clock = iter([0, 0, maui.ANDROID_BOOT_TIMEOUT + 1])
        with mock.patch.object(maui, 'output', return_value='0'), \
                mock.patch.object(maui.time, 'monotonic', side_effect=lambda: next(clock)), \
                mock.patch.object(maui.time, 'sleep'), self.assertRaises(SystemExit):
            maui.wait_for_android_boot('emulator-5554')


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


if __name__ == '__main__':
    unittest.main()
