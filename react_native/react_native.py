#!/usr/bin/python

import os, sys
import argparse
import apps as apps
import natives as natives
from utils import *

# ------------------------------------------------------------------
# set script tag
# ------------------------------------------------------------------
set_log_tag('REACT-NATIVE-SDK')

# ------------------------------------------------------------------
# make sure script gets executed and not imported somewhere
# ------------------------------------------------------------------
if __name__ != "__main__":
    error('Error. Do not import this script, but run it explicitly.')
    exit()

# ------------------------------------------------------------------
# usage message
# ------------------------------------------------------------------
usage_message = """List of potential commands that can be executed:
                     react-native [action_type] [target_type] [platform] [build_mode]
                     react-native build-native sdk android debug
                     react-native build-native sdk android release
                     react-native build-native sdk ios debug
                     react-native build-native sdk ios release
                     react-native build-native test-library android debug
                     react-native build-native test-library android release
                     react-native build-native test-library ios debug
                     react-native build-native test-library ios release
                     react-native build-native test-options android debug
                     react-native build-native test-options android release
                     react-native build-native plugin-oaid android debug
                     react-native build-native plugin-oaid android release
                     react-native run example-app android
                     react-native run example-app ios
                     react-native run test-app android
                     react-native run test-app ios
                """

args_count = len(sys.argv)

# ------------------------------------------------------------------
# too few arguments
# ------------------------------------------------------------------
if args_count != 4 and args_count != 5:
    error('Error. Wrong number of arguments.')
    debug(usage_message)
    exit()

# ------------------------------------------------------------------
# at this point, valid number of arguments has been passed to the script
# let's check how many of them are there (can be either 4 or 5)
# ------------------------------------------------------------------
action_type = sys.argv[1].lower()
target_type = sys.argv[2].lower()
if args_count > 3:
    platform = sys.argv[3].lower()
if args_count > 4:
    build_mode = sys.argv[4].lower()

# ------------------------------------------------------------------
# check argument values
# ------------------------------------------------------------------
if action_type != 'build-native' and action_type != 'run':
    error('Error. Invalid parameter [action_type] passed: {0}'.format(action_type))
    debug(usage_message)
    exit()
if target_type != 'sdk' and target_type != 'test-library' and target_type != 'test-options' and target_type != 'example-app' and target_type != 'test-app' and target_type != 'plugin-oaid':
    error('Error. Invalid parameter [target_type] passed: {0}'.format(target_type))
    debug(usage_message)
    exit()
if args_count > 3 and platform != 'android' and platform != 'ios':
    error('Error. Invalid parameter [platform] passed: {0}'.format(platform))
    debug(usage_message)
    exit()
if args_count > 4 and build_mode != 'debug' and build_mode != 'release':
    error('Error. Invalid parameter [build_mode] passed: {0}'.format(build_mode))
    debug(usage_message)
    exit()

try:
    # ------------------------------------------------------------------
    # build native binaries
    # ------------------------------------------------------------------
    if args_count == 5 and action_type == 'build-native':
        if target_type == 'sdk':
            natives.build_native_sdk(platform, build_mode)
        elif target_type == 'test-library':
            natives.build_native_test_library(platform, build_mode)
        elif target_type == 'test-options':
            natives.build_native_test_options(platform, build_mode)
        # elif target_type == 'plugin-oaid':
        #     natives.build_native_plugin_oaid(platform, build_mode)
    # ------------------------------------------------------------------
    # run example or test app
    # ------------------------------------------------------------------
    elif args_count == 4 and action_type == 'run':
        if target_type == 'example-app':
            natives.build_native_sdk(platform)
            if platform == 'android':
                # natives.build_native_plugin_oaid(platform)
                apps.build_and_run_example_app_android()
            elif platform == 'ios':
                apps.build_and_run_example_app_ios()
        elif target_type == 'test-app':
            # natives.build_native_sdk(platform)
            natives.build_native_test_library(platform)
            natives.build_native_test_options(platform)
            if platform == 'android':
                # natives.build_native_plugin_oaid(platform)
                apps.build_and_run_test_app_android()
            elif platform == 'ios':
                apps.build_and_run_test_app_ios()
    else:
        error('Error. Wrong arguments.')
        debug(usage_message)
        exit()
finally:
    # ------------------------------------------------------------------
    # remove autocreated Python compiled files
    # ------------------------------------------------------------------
    remove_files_with_pattern('*.pyc', get_scripts_dir())
    debug_green('Script completed!')
