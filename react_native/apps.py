import os, subprocess
from utils import *

dir_root = get_root_dir()

def build_and_run_example_app_android():
    dir_app                 = '{0}/example'.format(dir_root)
    dir_temp                = '{0}/temp'.format(dir_root)
    dir_plugin_node_modules = '{0}/node_modules/react-native-adjust'.format(dir_app)

    # ------------------------------------------------------------------
    # uninstalling example app from device/emulator
    # ------------------------------------------------------------------
    debug_green('Uninstalling example app from device/emulator ...')
    execute_command(['adb', 'uninstall', 'com.adjust.examples'])

    # ------------------------------------------------------------------
    # removing and unlinking react-native-adjust from example app
    # ------------------------------------------------------------------
    debug_green('Removing and unlinking react-native-adjust from example app ...')
    change_dir(dir_app)
    execute_command(['react-native', 'unlink', 'react-native-adjust'])
    execute_command(['yarn', 'remove', 'react-native-adjust'])
    remove_dir_if_exists(dir_plugin_node_modules)

    # ------------------------------------------------------------------
    # installing node dependencies
    # ------------------------------------------------------------------
    debug_green('Installing node dependencies [npm install] ...')
    execute_command(['npm', 'install'])

    # ------------------------------------------------------------------
    # fixing node dependencies
    # ------------------------------------------------------------------
    debug_green('Fixing node dependencies [npm audit fix --force] ...')
    execute_command(['npm', 'audit', 'fix', '--force'])

    # ------------------------------------------------------------------
    # copying react-native-adjust content to temp directory
    # ------------------------------------------------------------------
    debug_green('Copying react-native-adjust content to temp directory ...')
    copy_content_to_temp_dir()

    # ------------------------------------------------------------------
    # adding react-native-adjust to example app
    # ------------------------------------------------------------------
    debug_green('Adding react-native-adjust to example app ...')
    change_dir(dir_app)
    execute_command(['yarn', 'add', '../temp'])

    # TODO: check if this is needed, seems it's not
    #       error React Native CLI uses autolinking for native dependencies,
    #       but the following modules are linked manually
    # ------------------------------------------------------------------
    # linking react-native-adjust
    # ------------------------------------------------------------------
    # debug_green('Linking react-native-adjust ...')
    # execute_command(['react-native', 'link', 'react-native-adjust'])

    # ------------------------------------------------------------------
    # cleaning up the temporary directory
    # ------------------------------------------------------------------
    debug_green('Cleanup ...')
    remove_dir_if_exists(dir_temp)

    # ------------------------------------------------------------------
    # building and running example app on device/emulator
    # ------------------------------------------------------------------
    debug_green('Building and running example app on device/emulator ...')
    execute_command(['react-native', 'run-android'])

def build_and_run_example_app_ios():
    dir_app                 = '{0}/example'.format(dir_root)
    dir_temp                = '{0}/temp'.format(dir_root)
    dir_plugin_node_modules = '{0}/node_modules/react-native-adjust'.format(dir_app)

    # ------------------------------------------------------------------
    # removing and unlinking react-native-adjust from example app
    # ------------------------------------------------------------------
    debug_green('Removing and unlinking react-native-adjust from example app ...')
    change_dir(dir_app)
    execute_command(['react-native', 'unlink', 'react-native-adjust'])
    execute_command(['yarn', 'remove', 'react-native-adjust'])
    remove_dir_if_exists(dir_plugin_node_modules)

    # ------------------------------------------------------------------
    # installing node dependencies
    # ------------------------------------------------------------------
    debug_green('Installing node dependencies [npm install] ...')
    execute_command(['npm', 'install'])

    # ------------------------------------------------------------------
    # fixing node dependencies
    # ------------------------------------------------------------------
    debug_green('Fixing node dependencies [npm audit fix --force] ...')
    execute_command(['npm', 'audit', 'fix', '--force'])

    # ------------------------------------------------------------------
    # copying react-native-adjust content to temp directory
    # ------------------------------------------------------------------
    debug_green('Copying react-native-adjust content to temp directory ...')
    copy_content_to_temp_dir()

    # ------------------------------------------------------------------
    # adding react-native-adjust to example app
    # ------------------------------------------------------------------
    debug_green('Adding react-native-adjust to example app ...')
    change_dir(dir_app)
    execute_command(['yarn', 'add', '../temp'])

    # TODO: check if this is needed, seems it's not
    #       error React Native CLI uses autolinking for native dependencies,
    #       but the following modules are linked manually
    # ------------------------------------------------------------------
    # linking react-native-adjust
    # ------------------------------------------------------------------
    # debug_green('Linking react-native-adjust ...')
    # execute_command(['react-native', 'link', 'react-native-adjust'])

    # ------------------------------------------------------------------
    # update all the Pods if needed
    # ------------------------------------------------------------------
    change_dir('{0}/{1}'.format(dir_app, 'ios'))
    execute_command(['pod', 'update'])

    # ------------------------------------------------------------------
    # cleaning up the temporary directory
    # ------------------------------------------------------------------
    debug_green('Cleanup ...')
    remove_dir_if_exists(dir_temp)

    # ------------------------------------------------------------------
    # # info on how to run example app
    # ------------------------------------------------------------------
    debug_green('Run example app from Xcode. Project location: {0}/ios ...'.format(dir_app))

def build_and_run_test_app_android():
    dir_app                         = '{0}/test/app'.format(dir_root)
    dir_temp                        = '{0}/temp'.format(dir_root)
    dir_plugin_node_modules         = '{0}/node_modules/react-native-adjust'.format(dir_app)
    dir_plugin_node_modules_test    = '{0}/node_modules/react-native-adjust-test'.format(dir_app)

    # ------------------------------------------------------------------
    # uninstalling test app from device/emulator
    # ------------------------------------------------------------------
    debug_green('Uninstalling test app from device/emulator ...')
    execute_command(['adb', 'uninstall', 'com.adjust.test.app'])

    # ------------------------------------------------------------------
    # removing and unlinking react-native-adjust and react-native-adjust-test from test app
    # ------------------------------------------------------------------
    debug_green('Removing and unlinking react-native-adjust and react-native-adjust-test from test app ...')
    change_dir(dir_app)
    execute_command(['react-native', 'unlink', 'react-native-adjust'])
    execute_command(['react-native', 'unlink', 'react-native-adjust-test'])
    execute_command(['yarn', 'remove', 'react-native-adjust'])
    execute_command(['yarn', 'remove', 'react-native-adjust-test'])
    remove_dir_if_exists(dir_plugin_node_modules)
    remove_dir_if_exists(dir_plugin_node_modules_test)

    # ------------------------------------------------------------------
    # installing node dependencies
    # ------------------------------------------------------------------
    debug_green('Installing node dependencies [npm install] ...')
    execute_command(['npm', 'install'])

    # ------------------------------------------------------------------
    # fixing node dependencies
    # ------------------------------------------------------------------
    debug_green('Fixing node dependencies [npm audit fix --force] ...')
    execute_command(['npm', 'audit', 'fix', '--force'])

    # ------------------------------------------------------------------
    # copying react-native-adjust content to temp directory
    # ------------------------------------------------------------------
    debug_green('Copying react-native-adjust content to temp directory ...')
    copy_content_to_temp_dir()

    # ------------------------------------------------------------------
    # adding react-native-adjust and react-native-adjust-test to test app
    # ------------------------------------------------------------------
    debug_green('Adding react-native-adjust and react-native-adjust-test to test app ...')
    change_dir(dir_app)
    execute_command(['yarn', 'add', '../../temp'])
    execute_command(['yarn', 'add', '../lib'])

    # TODO: check if this is needed, seems it's not
    #       error React Native CLI uses autolinking for native dependencies,
    #       but the following modules are linked manually
    # ------------------------------------------------------------------
    # linking react-native-adjust
    # ------------------------------------------------------------------
    # debug_green('Linking react-native-adjust ...')
    # execute_command(['react-native', 'link', 'react-native-adjust'])

    # ------------------------------------------------------------------
    # cleaning up the temporary directory
    # ------------------------------------------------------------------
    debug_green('Cleanup ...')
    remove_dir_if_exists(dir_temp)

    # ------------------------------------------------------------------
    # building and running test app on device/emulator
    # ------------------------------------------------------------------
    debug_green('Building and running test app on device/emulator ...')
    execute_command(['react-native', 'run-android'])

def build_and_run_test_app_ios():
    dir_app                         = '{0}/test/app'.format(dir_root)
    dir_temp                        = '{0}/temp'.format(dir_root)
    dir_plugin_node_modules         = '{0}/node_modules/react-native-adjust'.format(dir_app)
    dir_plugin_node_modules_test    = '{0}/node_modules/react-native-adjust-test'.format(dir_app)

    # ------------------------------------------------------------------
    # removing and unlinking react-native-adjust and react-native-adjust-test from test app
    # ------------------------------------------------------------------
    debug_green('Removing and unlinking react-native-adjust and react-native-adjust-test from test app ...')
    change_dir(dir_app)
    execute_command(['react-native', 'unlink', 'react-native-adjust'])
    execute_command(['react-native', 'unlink', 'react-native-adjust-test'])
    execute_command(['yarn', 'remove', 'react-native-adjust'])
    execute_command(['yarn', 'remove', 'react-native-adjust-test'])
    remove_dir_if_exists(dir_plugin_node_modules)
    remove_dir_if_exists(dir_plugin_node_modules_test)

    # ------------------------------------------------------------------
    # installing node dependencies
    # ------------------------------------------------------------------
    debug_green('Installing node dependencies [npm install] ...')
    execute_command(['npm', 'install'])

    # ------------------------------------------------------------------
    # fixing node dependencies
    # ------------------------------------------------------------------
    debug_green('Fixing node dependencies [npm audit fix --force] ...')
    execute_command(['npm', 'audit', 'fix', '--force'])

    # ------------------------------------------------------------------
    # copying react-native-adjust content to temp directory
    # ------------------------------------------------------------------
    debug_green('Copying react-native-adjust content to temp directory ...')
    copy_content_to_temp_dir()

    # ------------------------------------------------------------------
    # adding react-native-adjust and react-native-adjust-test to test app
    # ------------------------------------------------------------------
    debug_green('Adding react-native-adjust and react-native-adjust-test to test app ...')
    change_dir(dir_app)
    execute_command(['yarn', 'add', '../../temp'])
    execute_command(['yarn', 'add', '../lib'])

    # TODO: check if this is needed, seems it's not
    #       error React Native CLI uses autolinking for native dependencies,
    #       but the following modules are linked manually
    # ------------------------------------------------------------------
    # linking react-native-adjust
    # ------------------------------------------------------------------
    # debug_green('Linking react-native-adjust ...')
    # execute_command(['react-native', 'link', 'react-native-adjust'])

    # ------------------------------------------------------------------
    # update all the Pods if needed
    # ------------------------------------------------------------------
    change_dir('{0}/{1}'.format(dir_app, 'ios'))
    execute_command(['pod', 'update'])

    # ------------------------------------------------------------------
    # cleaning up the temporary directory
    # ------------------------------------------------------------------
    debug_green('Cleanup ...')
    remove_dir_if_exists(dir_temp)

    # ------------------------------------------------------------------
    # info on how to run test app
    # ------------------------------------------------------------------
    debug_green('Run test app from Xcode. Project location: {0}/ios ...'.format(dir_app))

def copy_content_to_temp_dir():
    dir_temp    = '{0}/temp'.format(dir_root)
    dir_ios     = '{0}/ios'.format(dir_root)
    dir_android = '{0}/android'.format(dir_root)

    recreate_dir(dir_temp)
    copy_dir_content(dir_android, dir_temp + '/android')
    copy_dir_content(dir_ios, dir_temp + '/ios')
    copy_file('{0}/package.json'.format(dir_root), '{0}/package.json'.format(dir_temp))
    copy_file('{0}/react-native-adjust.podspec'.format(dir_root), '{0}/react-native-adjust.podspec'.format(dir_temp))
    copy_file('{0}/index.js'.format(dir_root), '{0}/index.js'.format(dir_temp))
