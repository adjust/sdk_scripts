#!/usr/bin/python
from utils import *
import anes as ane
import apps as app
import extensions as extension
import argparse

# Set script tag.
set_log_tag('ADOBE-AIR-SDK')

# Make sure script gets executed and not imported somewhere.
if __name__ != "__main__":
    error('Error. Do not import this script, but run it explicitly.')
    exit()

dir_scripts = os.path.dirname(os.path.realpath(__file__))

# ------------------------------------------------------------------
# Arguments check.
# ------------------------------------------------------------------

# Usage message.
usage_message = """List of potential commands that can be executed:
                     adobe build-extension sdk android debug
                     adobe build-extension sdk android release
                     adobe build-extension sdk ios debug
                     adobe build-extension sdk ios release
                     adobe build-extension test android debug
                     adobe build-extension test android release
                     adobe build-extension test ios debug
                     adobe build-extension test ios release
                     adobe build-ane sdk
                     adobe build-ane test
                     adobe run-app example android
                     adobe run-app example ios
                     adobe run-app test android
                     adobe run-app test ios
                """

args_count = len(sys.argv)

# Too few arguments.
if args_count < 3 or args_count > 5:
    error('Error. Wrong number of arguments.')
    debug(usage_message)
    exit()

# At this point, valid number of arguments has been passed to the script.
# Let's check how many of them are there (can be either 4 or 5).

action = sys.argv[1].lower()
app_type = sys.argv[2].lower()
if args_count > 3:
    platform = sys.argv[3].lower()
if args_count > 4:
    build_mode = sys.argv[4].lower()

# Check argument values.
if action != 'build-extension' and action != 'build-ane' and action != 'run-app':
    error('Error. Invalid parameter [action] passed: {0}'.format(build_mode))
    debug(usage_message)
    exit()
if app_type != 'sdk' and app_type != 'test' and app_type != 'example':
    error('Error. Invalid parameter [app_type] passed: {0}'.format(app_type))
    debug(usage_message)
    exit()
if args_count > 3 and platform != 'android' and platform != 'ios':
    error('Error. Invalid parameter [platform] passed: {0}'.format(app_type))
    debug(usage_message)
    exit()
if args_count > 4 and build_mode != 'debug' and platform != 'release':
    error('Error. Invalid parameter [build_mode] passed: {0}'.format(app_type))
    debug(usage_message)
    exit()

try:
    if args_count == 5:
        # In here we build native extension.

        if action == 'build-extension':
            if app_type == 'sdk':
                if platform == 'android':
                    extension.build_extension_sdk_android(build_mode)
                elif platform == 'ios':
                    extension.build_extension_sdk_ios(build_mode)
            elif app_type == 'test':
                if platform == 'android':
                    extension.build_extension_test_android(build_mode)
                elif platform == 'ios':
                    extension.build_extension_test_ios(build_mode)

    elif args_count == 3:
        # In here we build ANE.

        if action == 'build-ane':
            if app_type == 'sdk':
                extension.build_extension_sdk_android_release()
                extension.build_extension_sdk_ios_release()
                ane.build_ane_sdk()
            elif app_type == 'test':
                extension.build_extension_test_android_debug()
                extension.build_extension_test_ios_debug()
                ane.build_ane_test()

    elif action == 'run-app':
            if app_type == 'example':
                if platform == 'android':
                    extension.build_extension_sdk_android_release()
                    extension.build_extension_sdk_ios_release()
                    ane.build_ane_sdk()
                    app.build_and_run_app_example_android()
                elif platform == 'ios':
                    extension.build_extension_sdk_android_release()
                    extension.build_extension_sdk_ios_release()
                    ane.build_ane_sdk()
                    app.build_and_run_app_example_ios()
            elif app_type == 'test':
                if platform == 'android':
                    extension.build_extension_sdk_android_release()
                    extension.build_extension_sdk_ios_release()
                    extension.build_extension_test_android_debug()
                    extension.build_extension_test_ios_debug()
                    ane.build_ane_sdk()
                    ane.build_ane_test()
                    app.build_and_run_app_test_android()
                elif platform == 'ios':
                    extension.build_extension_sdk_android_release()
                    extension.build_extension_sdk_ios_release()
                    extension.build_extension_test_android_debug()
                    extension.build_extension_test_ios_debug()
                    ane.build_ane_sdk()
                    ane.build_ane_test()
                    app.build_and_run_app_test_ios()
finally:
    # Remove autocreated Python compiled files.
    remove_files_with_pattern('*.pyc', dir_scripts)
    debug_green('Script completed!')
