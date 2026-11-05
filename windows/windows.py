#!/usr/bin/env python3
import sys
sys.dont_write_bytecode = True

import argparse, os, shutil, subprocess
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from utils import *

set_log_tag('WINDOWS-SDK')

ROOT = root_dir()
SOLUTION = f'{ROOT}/Adjust.sln'
SDK_PROJECT = f'{ROOT}/AdjustSdk.DotNet/AdjustSdk.DotNet.csproj'
TEST_APP_PROJECT = f'{ROOT}/IntegrationTesting/TestAppDotNet/TestAppDotNet.csproj'
NUSPEC = f'{ROOT}/Adjust/Adjust.nuspec'
ARTIFACTS = f'{ROOT}/artifacts'

# the SDK, the console example, the test library and the console test app
def build(mode):
    info(f'Building the solution in {mode} mode ...')
    run(['dotnet', 'build', SOLUTION, '-c', mode.capitalize(), '-nologo', '-v', 'minimal'])

# release build of the SDK, packed as the Adjust NuGet package (netstandard2.0 + net8.0-windows10.0.19041)
def pack():
    if shutil.which('nuget') is None:
        error('nuget not found in PATH. Fix: brew install nuget (macOS) or winget install Microsoft.NuGet (Windows)')
        sys.exit(1)
    version = open(f'{ROOT}/VERSION').read().strip()

    info('Building the SDK in release mode ...')
    run(['dotnet', 'build', SDK_PROJECT, '-c', 'Release', '-nologo', '-v', 'minimal'])

    info(f'Packing Adjust {version} ...')
    os.makedirs(ARTIFACTS, exist_ok=True)
    run(['nuget', 'pack', NUSPEC, '-Version', version, '-OutputDirectory', ARTIFACTS, '-NoPackageAnalysis'])
    info(f'{ARTIFACTS}/Adjust.{version}.nupkg')

# runs the console test app against a running test server (https://github.com/adjust/sdk_test_server);
# it exits when the server says the session is over
def test(host, tests):
    info(f'Running the test app against {host} ...')
    run(['dotnet', 'run', '--project', TEST_APP_PROJECT, '-c', 'Debug', '--', '--host', host] + tests)

def main():
    parser = argparse.ArgumentParser(
        description='Build, test and pack the Adjust .NET SDK.',
        epilog='examples:\n'
               '  ./windows.py build [debug|release]\n'
               '  ./windows.py test                          # the tests this SDK supports (SupportedTests.cs)\n'
               '  ./windows.py test all                      # every test the server has for this SDK version\n'
               '  ./windows.py test session-count/           # one directory\n'
               '  ./windows.py test Test_SessionCount        # one test\n'
               '  ./windows.py test --host 192.168.1.10      # server on another machine\n'
               '  ./windows.py pack\n'
               '\n'
               'on Windows: python ext\\scripts\\windows\\windows.py ...\n',
        formatter_class=argparse.RawDescriptionHelpFormatter)
    actions = parser.add_subparsers(dest='action', required=True)

    build_parser = actions.add_parser('build', help='build the whole solution')
    build_parser.add_argument('mode', nargs='?', default='debug', choices=['debug', 'release'])

    test_parser = actions.add_parser('test', help='run the integration tests against a running test server')
    test_parser.add_argument('tests', nargs='*', help='tests and "directory/" entries to run, or "all"')
    test_parser.add_argument('--host', default='localhost', help='test server host, localhost by default')

    actions.add_parser('pack', help='release build and the Adjust NuGet package in artifacts/')
    args = parser.parse_args()

    if args.action == 'build':
        build(args.mode)
    elif args.action == 'test':
        test(args.host, args.tests)
    else:
        pack()

if __name__ == '__main__':
    try:
        main()
    except (subprocess.CalledProcessError, FileNotFoundError) as failure:
        error(f'Failed: {failure}')
        sys.exit(1)
