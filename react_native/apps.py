from decorators import only_mac_os
from react_native.utils import *

dir_root = get_root_dir()


def build_and_run_example_app_android():
    dir_app = os.path.join(dir_root, 'example')
    dir_temp = os.path.join(dir_root, 'temp')
    dir_node_modules_sdk = os.path.join(dir_app, 'node_modules/react-native-adjust')
    dir_node_modules_oaid = os.path.join(dir_app, 'node_modules/react-native-adjust-oaid')

    # ------------------------------------------------------------------
    # uninstalling example app from device/emulator
    # ------------------------------------------------------------------
    debug_green('Uninstalling example app from device/emulator ...')
    execute_command(['adb', 'uninstall', 'com.adjust.examples'])

    # ------------------------------------------------------------------
    # removing react-native-adjust from example app
    # ------------------------------------------------------------------
    change_dir(dir_app)
    debug_green('Removing react-native-adjust and react-native-adjust-oaid from example app ...')
    execute_command(['yarn', 'remove', 'react-native-adjust'])
    remove_dir_if_exists(dir_node_modules_sdk)
    execute_command(['yarn', 'remove', 'react-native-adjust-oaid'])
    remove_dir_if_exists(dir_node_modules_oaid)

    # ------------------------------------------------------------------
    # installing dependencies
    # ------------------------------------------------------------------
    debug_green('Check for dependencies updates [yarn upgrade] ...')
    execute_command(['yarn', 'upgrade'])
    debug_green('Installing dependencies [yarn install] ...')
    execute_command(['yarn', 'install'])

    # ------------------------------------------------------------------
    # copying react-native-adjust content to temp directory
    # ------------------------------------------------------------------
    debug_green('Copying react-native-adjust content to temp directory ...')
    copy_content_to_temp_dir()

    # ------------------------------------------------------------------
    # adding react-native-adjust to example app
    # ------------------------------------------------------------------
    change_dir(dir_app)
    debug_green('Adding react-native-adjust to example app ...')
    execute_command(['yarn', 'add', '../temp'])
    debug_green('Adding react-native-adjust-oaid to example app ...')
    execute_command(['yarn', 'add', '../plugins/oaid'])

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


@only_mac_os
def build_and_run_example_app_ios():
    dir_app = os.path.join(dir_root, 'example')
    dir_temp = os.path.join(dir_root, 'temp')
    dir_node_modules_sdk = os.path.join(dir_app, 'node_modules/react-native-adjust')

    # ------------------------------------------------------------------
    # removing react-native-adjust from example app
    # ------------------------------------------------------------------
    change_dir(dir_app)
    debug_green('Removing react-native-adjust from example app ...')
    execute_command(['yarn', 'remove', 'react-native-adjust'])
    remove_dir_if_exists(dir_node_modules_sdk)

    # ------------------------------------------------------------------
    # installing dependencies
    # ------------------------------------------------------------------
    debug_green('Check for dependencies updates [yarn upgrade] ...')
    execute_command(['yarn', 'upgrade'])
    debug_green('Installing dependencies [yarn install] ...')
    execute_command(['yarn', 'install'])

    # ------------------------------------------------------------------
    # copying react-native-adjust content to temp directory
    # ------------------------------------------------------------------
    debug_green('Copying react-native-adjust content to temp directory ...')
    copy_content_to_temp_dir()

    # ------------------------------------------------------------------
    # adding react-native-adjust to example app
    # ------------------------------------------------------------------
    change_dir(dir_app)
    debug_green('Adding react-native-adjust to example app ...')
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
    change_dir(os.path.join(dir_app, 'ios'))
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
    dir_app = os.path.join(dir_root, 'test/app')
    dir_temp = os.path.join(dir_root, 'temp')
    dir_node_modules_sdk = os.path.join(dir_app, 'node_modules/react-native-adjust')
    dir_node_modules_oaid = os.path.join(dir_app, 'node_modules/react-native-adjust-oaid')
    dir_node_modules_test = os.path.join(dir_app, 'node_modules/react-native-adjust-test')

    # ------------------------------------------------------------------
    # uninstalling test app from device/emulator
    # ------------------------------------------------------------------
    debug_green('Uninstalling test app from device/emulator ...')
    execute_command(['adb', 'uninstall', 'com.adjust.examples'])

    # ------------------------------------------------------------------
    # removing react-native-adjust and react-native-adjust-test from test app
    # ------------------------------------------------------------------
    change_dir(dir_app)
    debug_green('Removing react-native-adjust, react-native-adjust-oaid and react-native-adjust-test from test app ...')
    execute_command(['yarn', 'remove', 'react-native-adjust'])
    execute_command(['yarn', 'remove', 'react-native-adjust-oaid'])
    execute_command(['yarn', 'remove', 'react-native-adjust-test'])
    remove_dir_if_exists(dir_node_modules_sdk)
    remove_dir_if_exists(dir_node_modules_oaid)
    remove_dir_if_exists(dir_node_modules_test)

    # ------------------------------------------------------------------
    # installing dependencies
    # ------------------------------------------------------------------
    debug_green('Check for dependencies updates [yarn upgrade] ...')
    execute_command(['yarn', 'upgrade'])
    debug_green('Installing dependencies [yarn install] ...')
    execute_command(['yarn', 'install'])

    # ------------------------------------------------------------------
    # copying react-native-adjust content to temp directory
    # ------------------------------------------------------------------
    debug_green('Copying react-native-adjust content to temp directory ...')
    copy_content_to_temp_dir()

    # ------------------------------------------------------------------
    # adding react-native-adjust and react-native-adjust-test to test app
    # ------------------------------------------------------------------
    change_dir(dir_app)
    debug_green('Adding react-native-adjust, react-native-adjust-oaid and react-native-adjust-test to test app ...')
    execute_command(['yarn', 'add', '../../temp'])
    execute_command(['yarn', 'add', '../../plugins/oaid'])
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


@only_mac_os
def build_and_run_test_app_ios():
    dir_app = os.path.join(dir_root, 'test/app')
    dir_temp = os.path.join(dir_root, 'temp')
    dir_node_modules_sdk = os.path.join(dir_app, 'node_modules/react-native-adjust')
    dir_node_modules_test = os.path.join(dir_app, 'node_modules/react-native-adjust-test')

    # ------------------------------------------------------------------
    # removing react-native-adjust and react-native-adjust-test from test app
    # ------------------------------------------------------------------
    change_dir(dir_app)
    debug_green('Removing react-native-adjust and react-native-adjust-test from test app ...')
    execute_command(['yarn', 'remove', 'react-native-adjust'])
    execute_command(['yarn', 'remove', 'react-native-adjust-test'])
    remove_dir_if_exists(dir_node_modules_sdk)
    remove_dir_if_exists(dir_node_modules_test)

    # ------------------------------------------------------------------
    # installing dependencies
    # ------------------------------------------------------------------
    debug_green('Check for dependencies updates [yarn upgrade] ...')
    execute_command(['yarn', 'upgrade'])
    debug_green('Installing dependencies [yarn install] ...')
    execute_command(['yarn', 'install'])

    # ------------------------------------------------------------------
    # copying react-native-adjust content to temp directory
    # ------------------------------------------------------------------
    debug_green('Copying react-native-adjust content to temp directory ...')
    copy_content_to_temp_dir()

    # ------------------------------------------------------------------
    # adding react-native-adjust and react-native-adjust-test to test app
    # ------------------------------------------------------------------
    change_dir(dir_app)
    debug_green('Adding react-native-adjust and react-native-adjust-test to test app ...')
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
    change_dir(os.path.join(dir_app, 'ios'))
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
    dir_temp = os.path.join(dir_root, 'temp')
    dir_ios = os.path.join(dir_root, 'ios')
    dir_android = os.path.join(dir_root, 'android')

    recreate_dir(dir_temp)
    copy_dir_content(dir_android, os.path.join(dir_temp, 'android'))
    copy_dir_content(dir_ios, os.path.join(dir_temp, 'ios'))
    copy_file(os.path.join(dir_root, 'package.json'), os.path.join(dir_temp, 'package.json'))
    copy_file(os.path.join(dir_root, 'react-native-adjust.podspec'),
              os.path.join(dir_temp, 'react-native-adjust.podspec'))
    copy_file(os.path.join(dir_root, 'index.js'), os.path.join(dir_temp, 'index.js'))
