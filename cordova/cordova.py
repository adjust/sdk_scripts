#!/usr/bin/python

import os, sys
import argparse
import apps as apps
import natives as natives
from utils import *

# ------------------------------------------------------------------
# set script tag
# ------------------------------------------------------------------
set_log_tag('CORDOVA-SDK')

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
                     cordova [action_type] [target_type] [platform] [build_mode]
                     cordova build-native test-library android debug
                     cordova build-native test-library android release
                     cordova build-native test-library ios debug
                     cordova build-native test-library ios release
                     cordova build-native test-options android debug
                     cordova build-native test-options android release
                     cordova run example-app android
                     cordova run example-app ios
                     cordova run test-app android
                     cordova run test-app ios
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
if target_type != 'test-library' and target_type != 'test-options' and target_type != 'example-app' and target_type != 'test-app':
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
        if target_type == 'test-library':
            natives.build_native_test_library(platform, build_mode)
        elif target_type == 'test-options':
            natives.build_native_test_options(platform, build_mode)
    # ------------------------------------------------------------------
    # run example or test app
    # ------------------------------------------------------------------
    elif args_count == 4 and action_type == 'run':
        if target_type == 'example-app':
            if platform == 'android':
                apps.build_and_run_example_app_android()
            elif platform == 'ios':
                apps.build_and_run_example_app_ios()
        elif target_type == 'test-app':
            natives.build_native_test_library(platform)
            natives.build_native_test_options(platform)
            if platform == 'android':
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
    # ------------------------------------------------------------------
    # TODO: figure out proper way to remove __pycache__ directory
    # ------------------------------------------------------------------
    remove_dir_if_exists('__pycache__')
    debug_green('Script completed!')
