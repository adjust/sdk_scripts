import platform

import click

from adobe import anes as adobe_ane
from adobe import apps as adobe_app
from adobe import extensions as adobe_extensions
from react_native import apps as react_app
from react_native import natives as react_natives

PLATFORM = platform.system()


@click.group()
def main(*args, **kwargs):
    click.secho(f'Platform: {PLATFORM}', fg='bright_green')


@main.group(help='adobe sub-command')
def adobe(*args, **kwargs):
    click.secho('Running: Adobe', fg='bright_magenta')


@main.group(help='react-native sub-command')
def react_native(*args, **kwargs):
    click.secho('Running: React Native', fg='bright_magenta')


@adobe.command()
@click.option('--app_type', type=click.Choice(['sdk', 'test']))
@click.option('--build_platform', type=click.Choice(['android', 'ios']))
@click.option('--mode', type=click.Choice(['debug', 'release']))
def build_extension(mode, app_type, build_platform):
    click.secho(f'Building {app_type}. Mode: {mode} for {build_platform}', fg='green')
    if app_type == 'sdk':
        adobe_extensions.build_extension_sdk(build_platform, mode)
    elif app_type == 'test':
        adobe_extensions.build_extension_test(build_platform, mode)
    else:
        click.secho(f'Error! {app_type} not found!', fg='red')


@adobe.command()
@click.option('--app_type', type=click.Choice(['sdk', 'test']))
def build_ane(app_type):
    if app_type == 'sdk':
        adobe_ane.build_ane_sdk()
    elif app_type == 'test':
        adobe_ane.build_ane_test()
    else:
        click.secho(f'Error! {app_type} not found!', fg='red')


@adobe.command()
@click.option('--app_type', type=click.Choice(['sdk', 'test', 'example']))
@click.option('--build_platform', type=click.Choice(['android', 'ios']))
def run_app(app_type, build_platform):
    if app_type == 'example':
        adobe_extensions.build_extension_sdk_android_release()
        adobe_extensions.build_extension_sdk_ios_release()
        adobe_ane.build_ane_sdk()
        if build_platform == 'android':
            adobe_app.build_and_run_app_example_android()
        elif build_platform == 'ios':
            adobe_app.build_and_run_app_example_ios()
    elif app_type == 'test':
        adobe_extensions.build_extension_sdk_android_release()
        adobe_extensions.build_extension_sdk_ios_release()
        adobe_extensions.build_extension_test_android_debug()
        adobe_extensions.build_extension_test_ios_debug()
        adobe_ane.build_ane_sdk()
        adobe_ane.build_ane_test()
        if build_platform == 'android':
            adobe_app.build_and_run_app_test_android()
        elif build_platform == 'ios':
            adobe_app.build_and_run_app_test_ios()


@react_native.command()
@click.option('--target_type', type=click.Choice(['sdk', 'test-library', 'test-options', 'plugin-oaid']))
@click.option('--build_platform', type=click.Choice(['android', 'ios']))
@click.option('--mode', type=click.Choice(['debug', 'release']))
def build_native(target_type, build_platform, mode):
    if target_type == 'sdk':
        react_natives.build_native_sdk(build_platform, mode)
    elif target_type == 'test-library':
        react_natives.build_native_test_library(build_platform, mode)
    elif target_type == 'test-options':
        react_natives.build_native_test_options(build_platform, mode)
    elif target_type == 'plugin-oaid':
        react_natives.build_native_plugin_oaid(build_platform, mode)


@react_native.command()
@click.option('--target_type', type=click.Choice(['example-app', 'test-app']))
@click.option('--build_platform', type=click.Choice(['android', 'ios']))
def run(target_type, build_platform):
    if target_type == 'example-app':
        react_natives.build_native_sdk(build_platform)
        if build_platform == 'android':
            react_natives.build_native_plugin_oaid(build_platform)
            react_app.build_and_run_example_app_android()
        elif build_platform == 'ios':
            react_app.build_and_run_example_app_ios()
    elif target_type == 'test-app':
        react_natives.build_native_sdk(build_platform)
        react_natives.build_native_test_library(build_platform)
        react_natives.build_native_test_options(build_platform)
        if build_platform == 'android':
            react_natives.build_native_plugin_oaid(build_platform)
            react_app.build_and_run_test_app_android()
        elif build_platform == 'ios':
            react_app.build_and_run_test_app_ios()


if __name__ == '__main__':
    main()
