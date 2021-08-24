import os
from configparser import ConfigParser

from decorators import only_mac_os
from utils import (execute_command, clear_dir, copy_files, rename_file, copy_dir_content, remove_dir_if_exists,
                   copy_content_to_temp_dir)


class ReactNative:

    def __init__(self, config: ConfigParser):
        self.project_root = config['React-Native'].get('project_path')
        self.android_sdk_path = config['Android'].get('android_sdk_path')
        self.android_build_dir = config['React-Native'].get('android_build_dir')
        self.jar_in = config['React-Native'].get('jar_in')
        self.jar_out = config['React-Native'].get('jar_out')

        self.ios_sdk_path = config['IOS'].get('ios_sdk_path')

    def build_native_sdk(self, build_platform, mode):
        if build_platform == 'android':
            self.__build_native_sdk_android(mode)
        elif build_platform == 'ios':
            self.__build_native_sdk_ios(mode)
        else:
            print(f'NOT FOUND BUILD_PLATFORM: {build_platform}')

    def build_native_test_library(self, build_platform, mode):
        if build_platform == 'android':
            self.__build_native_test_library_android(mode)
        elif build_platform == 'ios':
            self.__build_native_test_library_ios(mode)

    def build_native_test_options(self, build_platform, mode):
        if build_platform == 'android':
            self.__build_native_test_options_android(mode)
        else:
            print('Supports only android platform')

    def build_native_plugin_oaid(self, build_platform, mode):
        if build_platform == 'android':
            self.__build_native_plugin_oaid_android(mode)
        else:
            print('Supports only android platform')

    def __build_native_sdk_android(self, mode: str):
        os.chdir(self.android_sdk_path)
        if mode == 'release':
            print('Building native Android SDK in release mode ...')
            execute_command(os.path.join(self.android_sdk_path, 'gradlew'), 'clean', 'adjustCoreJarRelease')
        elif mode == 'debug':
            print('Building native Android SDK in debug mode ...')
            execute_command(os.path.join(self.android_sdk_path, 'gradlew'), 'clean', 'adjustCoreJarRelease')
        else:
            print(f'NOT FOUND MODE: {mode}')

        print('Moving native Android SDK JAR from {0} to {1} dir ...'.format(self.jar_in, self.jar_out))
        clear_dir(self.jar_out)
        if mode == 'release':
            copy_files('adjust-sdk-release.jar', self.jar_in, self.jar_out)
            rename_file('adjust-sdk-release.jar', 'adjust-android.jar', self.jar_out)
        else:
            copy_files('adjust-sdk-debug.jar', self.jar_in, self.jar_out)
            rename_file('adjust-sdk-debug.jar', 'adjust-android.jar', self.jar_out)

    def __build_native_test_library_android(self, mode):
        os.chdir(self.android_sdk_path)

        # ------------------------------------------------------------------
        # build the JAR
        # ------------------------------------------------------------------
        if mode == 'release':
            print('Building native Android test library in release mode ...')
            execute_command('./gradlew', 'clean', ':test-library:adjustTestLibraryJarRelease')
        else:
            print('Building native Android test library in debug mode ...')
            execute_command('./gradlew', 'clean', ':test-library:adjustTestLibraryJarDebug')

        # ------------------------------------------------------------------
        # move the built JAR to destination folder
        # ------------------------------------------------------------------
        print('Moving native Android test library JAR from {0} to {1} dir ...'.format(self.jar_in, self.jar_out))
        clear_dir(self.jar_out)
        if mode == 'release':
            copy_files('test-library-release.jar', self.jar_in, self.jar_out)
            rename_file('test-library-release.jar', 'adjust-test-library.jar', self.jar_out)
        else:
            copy_files('test-library-debug.jar', self.jar_in, self.jar_out)
            rename_file('test-library-debug.jar', 'adjust-test-library.jar', self.jar_out)

    def __build_native_test_options_android(self, mode):
        os.chdir(self.android_sdk_path)

        # ------------------------------------------------------------------
        # build the JAR
        # ------------------------------------------------------------------
        if mode == 'release':
            print('Building native Android test options in release mode ...')
            execute_command('./gradlew', 'clean', ':test-options:assembleRelease')
        else:
            print('Building native Android test options in debug mode ...')
            execute_command('./gradlew', 'clean', ':test-options:assembleDebug')

        # ------------------------------------------------------------------
        # move the built JAR to destination folder
        # ------------------------------------------------------------------
        print('Moving native Android test options JAR from {0} to {1} dir ...'.format(self.jar_in, self.jar_out))
        # skipping cleaning of folder for now since it will wipe out adjust-test-library.jar
        clear_dir(self.jar_out, ('adjust-test-library.jar',))
        if mode == 'release':
            copy_files('classes.jar', self.jar_in, self.jar_out)
            rename_file('classes.jar', 'adjust-test-options.jar', self.jar_out)
        else:
            copy_files('classes.jar', self.jar_in, self.jar_out)
            rename_file('classes.jar', 'adjust-test-options.jar', self.jar_out)

    def __build_native_plugin_oaid_android(self, mode):
        os.chdir(self.android_sdk_path)

        # ------------------------------------------------------------------
        # build the JAR
        # ------------------------------------------------------------------
        if mode == 'release':
            print('Building native Android OAID plugin in release mode ...')
            execute_command('./gradlew', 'clean', 'sdk-plugin-oaid:adjustOaidAndroidJar')
        else:
            print('Building native Android OAID plugin in debug mode ...')
            execute_command('./gradlew', 'clean', 'sdk-plugin-oaid:adjustOaidAndroidJar')

        # ------------------------------------------------------------------
        # move the built JAR to destination folder
        # ------------------------------------------------------------------
        print('Moving native Android OAID plugin JAR from {0} to {1} dir ...'.format(self.jar_in, self.jar_out))
        clear_dir(self.jar_out)
        if mode == 'release':
            copy_files('sdk-plugin-oaid.jar', self.jar_in, self.jar_out)
            rename_file('sdk-plugin-oaid.jar', 'adjust-android-oaid.jar', self.jar_out)
        else:
            copy_files('sdk-plugin-oaid.jar', self.jar_in, self.jar_out)
            rename_file('sdk-plugin-oaid.jar', 'adjust-android-oaid.jar', self.jar_out)

    def build_and_run_example_app_android(self):
        dir_app = os.path.join(self.project_root, 'example')
        dir_temp = os.path.join(self.project_root, 'temp')
        dir_node_modules_sdk = os.path.join(dir_app, 'node_modules/react-native-adjust')
        # dir_node_modules_oaid = os.path.join(dir_app, 'node_modules/react-native-adjust-oaid')

        # ------------------------------------------------------------------
        # uninstalling example app from device/emulator
        # ------------------------------------------------------------------
        print('Uninstalling example app from device/emulator ...')
        execute_command('adb', 'uninstall', 'com.adjust.examples')

        # ------------------------------------------------------------------
        # removing react-native-adjust from example app
        # ------------------------------------------------------------------
        os.chdir(dir_app)
        print('Removing react-native-adjust and react-native-adjust-oaid from example app ...')
        execute_command('yarn', 'remove', 'react-native-adjust')
        remove_dir_if_exists(dir_node_modules_sdk)
        execute_command('yarn', 'remove', 'react-native-adjust-oaid')
        self.__prepare_build(dir_node_modules_sdk, dir_app)
        print('Adding react-native-adjust-oaid to example app ...')
        execute_command('yarn', 'add', '../plugins/oaid')

        print('Cleanup ...')
        remove_dir_if_exists(dir_temp)

        # ------------------------------------------------------------------
        # building and running example app on device/emulator
        # ------------------------------------------------------------------
        print('Building and running example app on device/emulator ...')
        execute_command('react-native', 'run-android')

    def build_and_run_test_app_android(self):
        dir_app = os.path.join(self.project_root, 'test/app')
        dir_temp = os.path.join(self.project_root, 'temp')
        dir_node_modules_sdk = os.path.join(dir_app, 'node_modules/react-native-adjust')
        dir_node_modules_oaid = os.path.join(dir_app, 'node_modules/react-native-adjust-oaid')
        dir_node_modules_test = os.path.join(dir_app, 'node_modules/react-native-adjust-test')

        # ------------------------------------------------------------------
        # uninstalling test app from device/emulator
        # ------------------------------------------------------------------
        print('Uninstalling test app from device/emulator ...')
        execute_command('adb', 'uninstall', 'com.adjust.examples')

        # ------------------------------------------------------------------
        # removing react-native-adjust and react-native-adjust-test from test app
        # ------------------------------------------------------------------
        os.chdir(dir_app)
        print(
            'Removing react-native-adjust, react-native-adjust-oaid and react-native-adjust-test from test app ...')
        execute_command('yarn', 'remove', 'react-native-adjust')
        execute_command('yarn', 'remove', 'react-native-adjust-oaid')
        execute_command('yarn', 'remove', 'react-native-adjust-test')
        remove_dir_if_exists(dir_node_modules_sdk)
        remove_dir_if_exists(dir_node_modules_oaid)
        remove_dir_if_exists(dir_node_modules_test)

        # ------------------------------------------------------------------
        # installing dependencies
        # ------------------------------------------------------------------
        print('Check for dependencies updates [yarn upgrade] ...')
        execute_command('yarn', 'upgrade')
        print('Installing dependencies [yarn install] ...')
        execute_command('yarn', 'install')

        # ------------------------------------------------------------------
        # copying react-native-adjust content to temp directory
        # ------------------------------------------------------------------
        print('Copying react-native-adjust content to temp directory ...')
        copy_content_to_temp_dir(self.project_root)

        # ------------------------------------------------------------------
        # adding react-native-adjust and react-native-adjust-test to test app
        # ------------------------------------------------------------------
        os.chdir(dir_app)
        print('Adding react-native-adjust, react-native-adjust-oaid and react-native-adjust-test to test app ...')
        execute_command('yarn', 'add', '../../temp')
        execute_command('yarn', 'add', '../../plugins/oaid')
        execute_command('yarn', 'add', '../lib')

        # ------------------------------------------------------------------
        # cleaning up the temporary directory
        # ------------------------------------------------------------------
        print('Cleanup ...')
        remove_dir_if_exists(dir_temp)

        # ------------------------------------------------------------------
        # building and running test app on device/emulator
        # ------------------------------------------------------------------
        print('Building and running test app on device/emulator ...')
        execute_command('react-native', 'run-android')

    @only_mac_os
    def build_and_run_test_app_ios(self):
        dir_app = os.path.join(self.project_root, 'test/app')
        dir_temp = os.path.join(self.project_root, 'temp')
        dir_node_modules_sdk = os.path.join(dir_app, 'node_modules/react-native-adjust')
        dir_node_modules_test = os.path.join(dir_app, 'node_modules/react-native-adjust-test')

        # ------------------------------------------------------------------
        # removing react-native-adjust and react-native-adjust-test from test app
        # ------------------------------------------------------------------
        os.chdir(dir_app)
        print('Removing react-native-adjust and react-native-adjust-test from test app ...')
        execute_command('yarn', 'remove', 'react-native-adjust')
        execute_command('yarn', 'remove', 'react-native-adjust-test')
        remove_dir_if_exists(dir_node_modules_sdk)
        remove_dir_if_exists(dir_node_modules_test)

        # ------------------------------------------------------------------
        # installing dependencies
        # ------------------------------------------------------------------
        print('Check for dependencies updates [yarn upgrade] ...')
        execute_command('yarn', 'upgrade')
        print('Installing dependencies [yarn install] ...')
        execute_command('yarn', 'install')

        # ------------------------------------------------------------------
        # copying react-native-adjust content to temp directory
        # ------------------------------------------------------------------
        print('Copying react-native-adjust content to temp directory ...')
        copy_content_to_temp_dir(self.project_root)

        # ------------------------------------------------------------------
        # adding react-native-adjust and react-native-adjust-test to test app
        # ------------------------------------------------------------------
        os.chdir(dir_app)
        print('Adding react-native-adjust and react-native-adjust-test to test app ...')
        execute_command('yarn', 'add', '../../temp')
        execute_command('yarn', 'add', '../lib')

        # ------------------------------------------------------------------
        # update all the Pods if needed
        # ------------------------------------------------------------------
        os.chdir(os.path.join(dir_app, 'ios'))
        execute_command('pod', 'update')

        # ------------------------------------------------------------------
        # cleaning up the temporary directory
        # ------------------------------------------------------------------
        print('Cleanup ...')
        remove_dir_if_exists(dir_temp)

        # ------------------------------------------------------------------
        # info on how to run test app
        # ------------------------------------------------------------------
        print('Run test app from Xcode. Project location: {0}/ios ...'.format(dir_app))

    @only_mac_os
    def build_and_run_example_app_ios(self):
        dir_app = os.path.join(self.project_root, 'example')
        dir_temp = os.path.join(self.project_root, 'temp')
        dir_node_modules_sdk = os.path.join(dir_app, 'node_modules/react-native-adjust')

        # ------------------------------------------------------------------
        # removing react-native-adjust from example app
        # ------------------------------------------------------------------
        os.chdir(dir_app)
        print('Removing react-native-adjust from example app ...')
        execute_command('yarn', 'remove', 'react-native-adjust')
        self.__prepare_build(dir_node_modules_sdk, dir_app)

        # ------------------------------------------------------------------
        # update all the Pods if needed
        # ------------------------------------------------------------------
        os.chdir(os.path.join(dir_app, 'ios'))
        execute_command('pod', 'update')

        # ------------------------------------------------------------------
        # cleaning up the temporary directory
        # ------------------------------------------------------------------
        print('Cleanup ...')
        remove_dir_if_exists(dir_temp)

        # ------------------------------------------------------------------
        # # info on how to run example app
        # ------------------------------------------------------------------
        print('Run example app from Xcode. Project location: {0}/ios ...'.format(dir_app))

    @only_mac_os
    def __build_native_test_library_ios(self, mode):
        dir_src = os.path.join(self.ios_sdk_path, 'Adjust')
        dir_src_out = os.path.join(self.project_root, 'ios/Adjust')

        print('Copying iOS SDK source files from {0} to {1} ...'.format(dir_src, dir_src_out))
        copy_dir_content(dir_src, dir_src_out)

    @only_mac_os
    def __build_native_sdk_ios(self, mode: str):
        dir_src = os.path.join(self.ios_sdk_path, 'AdjustTests/AdjustTestLibrary/AdjustTestLibrary/')
        dir_src_out = os.path.join(self.project_root, 'test/lib/ios/AdjustTestLibrary/')

        print('Copying iOS test library source files from {0} to {1} ...'.format(dir_src, dir_src_out))
        copy_dir_content(dir_src, dir_src_out)

    def __prepare_build(self, dir_node_modules_sdk, dir_app):
        remove_dir_if_exists(dir_node_modules_sdk)

        # ------------------------------------------------------------------
        # installing dependencies
        # ------------------------------------------------------------------
        print('Check for dependencies updates [yarn upgrade] ...')
        execute_command('yarn', 'upgrade')
        print('Installing dependencies [yarn install] ...')
        execute_command('yarn', 'install')

        # ------------------------------------------------------------------
        # copying react-native-adjust content to temp directory
        # ------------------------------------------------------------------
        print('Copying react-native-adjust content to temp directory ...')
        copy_content_to_temp_dir(self.project_root)

        # ------------------------------------------------------------------
        # adding react-native-adjust to example app
        # ------------------------------------------------------------------
        os.chdir(dir_app)
        print('Adding react-native-adjust to example app ...')
        execute_command('yarn', 'add', '../temp')
