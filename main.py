import platform
from configparser import ConfigParser

import click

from adobe_air import Adobe
from react_native import ReactNative
from utils import convert_to_abspath

PLATFORM = platform.system()
CONFIG = ConfigParser()


@click.group()
@click.option('--config_file', '-c', help='config file path', type=click.File('r'), default='scripts_config.ini')
def main(config_file):
    click.secho(f'Platform: {PLATFORM}', fg='bright_green')
    click.secho(f'Reading config file: {config_file.name}', fg='bright_green')
    CONFIG.read_file(config_file)
    for section in CONFIG.sections():
        for key, value in CONFIG[section].items():
            if value.startswith(('.', '..', '~')):
                CONFIG[section][key] = convert_to_abspath(value)


@main.command('print-config', help='shows config variables')
def print_config():
    for section in CONFIG.sections():
        click.secho(f'[{section}]', fg='blue')
        for key, value in CONFIG[section].items():
            click.secho(f'{key}: {value}')


@main.group(help='adobe sub-command')
def adobe():
    click.secho('Running: Adobe', fg='bright_magenta')


@main.group(help='react-native sub-command')
def react_native():
    click.secho('Running: React Native', fg='bright_magenta')


@react_native.command()
@click.option('--target-type', type=click.Choice(['sdk', 'test-library', 'test-options', 'plugin-oaid']))
@click.option('--build-platform', type=click.Choice(['android', 'ios']))
@click.option('--mode', type=click.Choice(['debug', 'release']))
def build_native(target_type, build_platform, mode):
    react = ReactNative(CONFIG)
    if target_type == 'sdk':
        react.build_native_sdk(build_platform, mode)
    elif target_type == 'test-library':
        react.build_native_test_library(build_platform, mode)
    elif target_type == 'test-options':
        react.build_native_test_options(build_platform, mode)
    elif target_type == 'plugin-oaid':
        react.build_native_plugin_oaid(build_platform, mode)


@react_native.command()
@click.option('--target-type', type=click.Choice(['example-app', 'test-app']))
@click.option('--build-platform', type=click.Choice(['android', 'ios']))
@click.option('--mode', type=click.Choice(['debug', 'release']))
def run(target_type, build_platform, mode):
    react = ReactNative(CONFIG)
    if target_type == 'example-app':
        react.build_native_sdk(build_platform, mode)
        if build_platform == 'android':
            react.build_native_plugin_oaid(build_platform, mode)
            react.build_and_run_example_app_android()
        elif build_platform == 'ios':
            react.build_and_run_example_app_ios()
    elif target_type == 'test-app':
        react.build_native_sdk(build_platform, mode)
        react.build_native_test_library(build_platform, mode)
        react.build_native_test_options(build_platform, mode)
        if build_platform == 'android':
            react.build_native_plugin_oaid(build_platform, mode)
            react.build_and_run_test_app_android()
        elif build_platform == 'ios':
            react.build_and_run_test_app_ios()


@adobe.command()
@click.option('--app-type', type=click.Choice(['sdk', 'test']))
@click.option('--build-platform', type=click.Choice(['android', 'ios']))
@click.option('--mode', type=click.Choice(['debug', 'release']))
def build_extension(mode, app_type, build_platform):
    click.secho(f'Building {app_type}. Mode: {mode} for {build_platform}', fg='green')
    adobe_runner = Adobe(CONFIG)
    if app_type == 'sdk':
        adobe_runner.build_extension_sdk(build_platform, mode)
    elif app_type == 'test':
        adobe_runner.build_extension_test(build_platform, mode)
    else:
        click.secho(f'Error! {app_type} not found!', fg='red')


@adobe.command()
@click.option('--app-type', type=click.Choice(['sdk', 'test']))
def build_ane(app_type):
    adobe_runner = Adobe(CONFIG)
    if app_type == 'sdk':
        adobe_runner.build_ane_sdk()
    elif app_type == 'test':
        adobe_runner.build_ane_test()
    else:
        click.secho(f'Error! {app_type} not found!', fg='red')


@adobe.command()
@click.option('--app-type', type=click.Choice(['sdk', 'test', 'example']))
@click.option('--build-platform', type=click.Choice(['android', 'ios']))
def run_app(app_type, build_platform):
    adobe_runner = Adobe(CONFIG)
    if app_type == 'example':
        adobe_runner.build_extension_sdk(build_platform, 'release')
        adobe_runner.build_ane_sdk()
        if build_platform == 'android':
            adobe_runner.build_and_run_app_example_android()
        elif build_platform == 'ios':
            adobe_runner.build_and_run_app_example_ios()
    elif app_type == 'test':
        adobe_runner.build_extension_sdk(build_platform, 'release')
        adobe_runner.build_extension_sdk(build_platform, 'debug')
        adobe_runner.build_ane_sdk()
        adobe_runner.build_ane_test()
        if build_platform == 'android':
            adobe_runner.build_and_run_app_test_android()
        elif build_platform == 'ios':
            adobe_runner.build_and_run_app_test_ios()


if __name__ == '__main__':
    main()
