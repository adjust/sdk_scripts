import glob
import os
from configparser import ConfigParser

from decorators import only_mac_os
from utils import (recreate_dir, copy_file, copy_dir_content, remove_file_if_exists, execute_command,
                   xcode_rebuild_custom_destination, xcode_rebuild, remove_files_with_pattern,
                   create_dir_if_not_present, adb_uninstall, adb_install_apk, adb_shell_monkey)


class Adobe:

    def __init__(self, config: ConfigParser):
        self.project_root = config['Adobe'].get('project_path')
        self._version_path = config['Adobe'].get('version_file_path')
        self.version = open(self._version_path).readlines()[0].strip()

    def build_extension_sdk(self, build_platform, build_mode='release'):
        if build_platform == 'android':
            self.build_extension_sdk_android(build_mode)
        elif build_platform == 'ios':
            self.build_extension_sdk_ios(build_mode)

    def build_extension_test(self, build_platform, build_mode='release'):
        if build_platform == 'android':
            self.build_extension_test_android(build_mode)
        elif build_platform == 'ios':
            self.build_extension_test_ios(build_mode)

    def build_extension_test_android(self, build_mode='release'):
        dir_plugin = os.path.join(self.project_root, 'test/plugin/android')
        dir_bld_extension = os.path.join(dir_plugin, 'src/AdjustTestExtension')
        dir_src_extension = os.path.join(dir_bld_extension, 'extension/src/main/java/com/adjust/test')
        dir_src_test = os.path.join(self.project_root,
                                    'ext/android/sdk/Adjust/test-library/src/main/java/com/adjust/test')
        dir_src_jar = os.path.join(dir_bld_extension, 'extension/build/libs/', build_mode)

        # Update Android test extension source files from SDK extension directory.
        print('Update all Android SDK test library source files in the extension source directory ...')
        excluded_files = [
            os.path.join(dir_src_extension, 'AdjustTestExtension.java'),
            os.path.join(dir_src_extension, 'AdjustTestFunction.java'),
            os.path.join(dir_src_extension, 'AdjustTestContext.java'),
            os.path.join(dir_src_extension, 'CommandListener.java')]
        os.chdir(self.project_root)
        remove_files_with_pattern('*', dir_src_extension, excluded_files)
        copy_dir_content(dir_src_test, dir_src_extension)

        # Build Android test extension JAR.
        print('Building adjust-android-test.jar of the Android test extension ...')
        os.chdir(dir_bld_extension)
        print(f'{dir_bld_extension=}')
        if build_mode == 'release':
            execute_command('./gradlew', 'clean', 'makeReleaseJar')
        else:
            execute_command('./gradlew', 'clean', 'makeDebugJar')

        # Copy generated Android test extension JAR to it's destination directory.
        print('Copying generated adjust-android-test.jar from {0} to {1} ...'.format(dir_src_jar, dir_plugin))
        copy_file(os.path.join(dir_src_jar, 'adjust-android-test.jar'),
                  os.path.join(dir_plugin, 'adjust-android-test.jar'))

    @only_mac_os
    def build_extension_test_ios(self, build_mode='release'):
        dir_plugin = os.path.join(self.project_root, 'test/plugin/ios')
        dir_ext = os.path.join(self.project_root, 'ext/ios')
        dir_src_extension = os.path.join(self.project_root, 'test/plugin/ios/src/AdjustTestExtension')
        dir_test_lib = os.path.join(dir_ext, 'sdk/AdjustTests/AdjustTestLibrary')
        dir_frameworks = os.path.join(dir_ext, 'sdk/Frameworks/Static')

        # Remove static AdjustTestLibrary.framework.
        print('Removing existing static AdjustTestLibrary.framework ...')
        recreate_dir(dir_frameworks)

        # Rebuild static AdjustTestLibrary.framework.
        print('Rebuilding static AdjustTestLibrary.framework in {0} mode ...'.format(build_mode))
        os.chdir(dir_test_lib)
        xcode_rebuild('AdjustTestLibraryStatic', build_mode.capitalize())

        # Copy static AdjustTestLibrary.framework to it's destination.
        copy_dir_content(os.path.join(dir_frameworks, 'AdjustTestLibrary.framework'),
                         os.path.join(dir_src_extension, 'AdjustTestLibrary.framework'))
        copy_dir_content(os.path.join(dir_frameworks, 'AdjustTestLibrary.framework'),
                         os.path.join(dir_plugin, 'AdjustTestLibrary.framework'))

        # Build iOS test extension .a library.
        print(
            'Building Adobe AIR SDK test library iOS extension .a library and outputting it to {0} ...'.format(
                dir_plugin))
        os.chdir(dir_src_extension)
        xcode_rebuild_custom_destination('AdjustTestExtension', build_mode.capitalize(), dir_plugin)

    def adobe_air_amxmlc_example(self):
        execute_command(
            'amxmlc', '-external-library-path+=lib/Adjust-{0}.ane'.format(self.version), '-output=Main.swf', '--',
            'Main.as')

    @staticmethod
    def adobe_air_does_keystore_file_exist(dir_path):
        return len(glob.glob('{0}/*.pfx'.format(dir_path))) > 0

    @staticmethod
    def adobe_air_make_sample_cert():
        execute_command(
            'adt', '-certificate', '-validityPeriod', '25', '-cn', 'SelfSigned', '2048-RSA', 'sampleCert.pfx', 'pass')

    @staticmethod
    def adobe_air_package_apk_file():
        print('Packaging APK file, please wait ...')
        command = """adt -package -target apk-debug -arch armv8 -storetype pkcs12 -keystore sampleCert.pfx Main.apk 
        Main-app.xml Main.swf -extdir lib """
        print('Executing: [{0}] ...'.format(command))
        os.system('echo pass|{0}'.format(command))
        print('Packaging APK file done.')

    def build_and_run_app_example_android(self):
        dir_app = os.path.join(self.project_root, 'example')

        # Remove Adjust SDK ANE from example app.
        print('Removing SDK ANE file from example app ...')
        remove_files_with_pattern('Adjust-*.*.*.ane', os.path.join(dir_app, 'lib/'))

        # Copy newly generated Adjust SDK ANE to example app.
        print('Copying SDK ANE file to example app ...')
        create_dir_if_not_present(os.path.join(dir_app, 'lib/'))
        copy_file(os.path.join(self.project_root, f'Adjust-{self.version}.ane'),
                  os.path.join(dir_app, 'lib', f'Adjust-{self.version}.ane'))

        # Run 'amxmlc'.
        print('Running \'amxmlc\' ...')
        os.chdir(dir_app)
        self.adobe_air_amxmlc_example()

        # Do keystore file logic.
        if not self.adobe_air_does_keystore_file_exist(dir_app):
            print('Keystore file does not exist, creating one with password [pass] ...')
            self.adobe_air_make_sample_cert()
            print('Keystore file created.')
        else:
            print('Keystore file exists.')

        # Uninstall example app.
        print('Uninstalling air.com.adjust.examples package from test device ...')
        adb_uninstall('air.com.adjust.examples')

        # Package example app APK file.
        print('Packaging APK file. Password will be entered automatically ...')
        self.adobe_air_package_apk_file()

        # Install example app.
        print('Installing air.com.adjust.examples package to test device ...')
        adb_install_apk('Main.apk')

        # Start example app.
        print('Example app installed. Starting the example app on the device ...')
        adb_shell_monkey('air.com.adjust.examples')

    @only_mac_os
    def build_extension_sdk_ios(self, build_mode='release'):
        dir_ext = os.path.join(self.project_root, 'ext/ios')
        dir_sdk = os.path.join(dir_ext, 'sdk')
        dir_src_extension = os.path.join(dir_ext, 'src/AdjustExtension')

        # Remove static AdjustSdk.framework.
        print('Removing existing static AdjustSdk.framework ...')
        recreate_dir(os.path.join(dir_sdk, 'Frameworks/Static'))

        # Rebuild static AdjustSdk.framework.
        print('Rebuilding static AdjustSdk.framework in {0} mode ...'.format(build_mode))
        os.chdir(dir_sdk)
        xcode_rebuild('AdjustStatic', build_mode.capitalize())

        # Copy static AdjustSdk.framework to it's destination.
        copy_dir_content(os.path.join(dir_sdk, 'Frameworks/Static/AdjustSdk.framework'),
                         os.path.join(dir_src_extension, 'include/Adjust/AdjustSdk.framework'))
        copy_dir_content(os.path.join(dir_sdk, 'Frameworks/Static/AdjustSdk.framework'),
                         os.path.join(dir_ext, 'AdjustSdk.framework'))

        # Build iOS extension .a library.
        print('Building Adobe AIR iOS SDK extension .a library and outputing it to {0} ...'.format(dir_ext))
        os.chdir(dir_src_extension)
        xcode_rebuild_custom_destination('AdjustExtension', build_mode.capitalize(), dir_ext)

    @only_mac_os
    def build_and_run_app_example_ios(self):
        dir_app = os.path.join(self.project_root, 'example')
        file_app_xml = os.path.join(dir_app, 'Main-app.xml')

        path_prov_profile = os.environ.get('DEV_ADOBE_PROVISIONING_PROFILE_PATH')
        path_keystore_file = os.environ.get('KEYSTORE_FILE_PATH')

        # Remove Adjust SDK ANE from example app.
        print('Removing SDK ANE file from example app ...')
        remove_files_with_pattern('Adjust-*.*.*.ane', os.path.join(dir_app, 'lib/'))

        # Copy newly generated Adjust SDK ANE to example app.
        print('Copying SDK ANE file to example app ...')
        create_dir_if_not_present(os.path.join(dir_app, 'lib'))
        copy_file(os.path.join(self.project_root, f'Adjust-{self.version}.ane'),
                  os.path.join(dir_app, 'lib', f'Adjust-{self.version}.ane'))

        # Run 'amxmlc'.
        print('Running \'amxmlc\' ...')
        os.chdir(dir_app)
        self.adobe_air_amxmlc_example()

        # Do keystore file logic.
        if not self.adobe_air_does_keystore_file_exist(dir_app):
            print('Keystore file does not exist, creating one with password [pass] ...')
            self.adobe_air_make_sample_cert()
            print('Keystore file created.')
        else:
            print('Keystore file exists.')

        # Package example app IPA file.
        print('Packaging IPA file ...')
        self.adobe_air_package_ipa_file(path_prov_profile, path_keystore_file, file_app_xml)

    @staticmethod
    def adobe_air_package_ipa_file(prov_profile_path, keystore_file_path, example_app_xml_file):
        print('Packaging IPA file, please wait ...')
        command = """adt -package -target ipa-debug -provisioning-profile {0} -storetype pkcs12 -keystore {1} 
        Main.ipa {2} Main.swf -extdir lib""".format(
            prov_profile_path, keystore_file_path, example_app_xml_file)
        print('Executing: [{0}]'.format(command))
        os.system('echo|{0}'.format(command))
        print('Packaging IPA file done')

    def build_extension_sdk_android(self, build_mode='release'):
        dir_ext = os.path.join(self.project_root, 'ext/android')
        dir_bld_extension = os.path.join(dir_ext, 'src/AdjustExtension')
        dir_src_extension = os.path.join(dir_ext, 'src/AdjustExtension/extension/src/main/java/com/adjust/sdk')
        dir_src_sdk = os.path.join(dir_ext, 'sdk/Adjust/sdk-core/src/main/java/com/adjust/sdk')
        dir_src_jar = os.path.join(dir_ext, 'src/AdjustExtension/extension/build/libs/', build_mode)

        # Update Android extension source files from SDK extension directory.
        print('Update all Android SDK source files in the extension source directory ...')
        excluded_files = [
            os.path.join(dir_src_extension, 'AdjustActivity.java'),
            os.path.join(dir_src_extension, 'AdjustExtension.java'),
            os.path.join(dir_src_extension, 'AdjustFunction.java'),
            os.path.join(dir_src_extension, 'AdjustContext.java')]
        os.chdir(self.project_root)
        remove_files_with_pattern('*', dir_src_extension, excluded_files)
        copy_dir_content(dir_src_sdk, dir_src_extension)

        # Build Android extension JAR.
        print('Building adjust-android.jar of the Android extension ...')
        os.chdir(dir_bld_extension)
        if build_mode == 'release':
            execute_command('./gradlew', 'clean', 'makeReleaseJar')
        else:
            execute_command('./gradlew', 'clean', 'makeDebugJar')

        # Copy generated Android extension JAR to it's destination directory.
        print('Copying generated adjust-android.jar from {0} to {1} ...'.format(dir_src_jar, dir_ext))
        copy_file('{0}/adjust-android.jar'.format(dir_src_jar), '{0}/adjust-android.jar'.format(dir_ext))

    @staticmethod
    def adobe_air_amxmlc_test(version):
        execute_command('amxmlc', '-external-library-path+=lib/Adjust-{0}.ane'.format(version),
                        '-external-library-path+=lib/AdjustTest-{0}.ane'.format(version), '-output=Main.swf', '--',
                        'Main.as')

    def build_and_run_app_test_android(self):
        dir_app = os.path.join(self.project_root, 'test/app')

        # Remove Adjust SDK and test library ANE from test app.
        print('Removing SDK and test library ANE files from test app ...')
        remove_files_with_pattern('Adjust-*.*.*.ane', os.path.join(dir_app, 'lib/'))
        remove_files_with_pattern('AdjustTest-*.*.*.ane', os.path.join(dir_app, 'lib/'))

        # Copy Adjust SDK and test library ANE files to test app.
        print('Copying SDK and test library ANE files to test app ...')
        create_dir_if_not_present(os.path.join(dir_app, 'lib'))
        copy_file(os.path.join(self.project_root, f'Adjust-{self.version}.ane'),
                  os.path.join(dir_app, 'lib', f'Adjust-{self.version}.ane'))
        copy_file(os.path.join(self.project_root, f'AdjustTest-{self.version}.ane'),
                  os.path.join(dir_app, 'lib', f'AdjustTest-{self.version}.ane'))

        # Run 'amxmlc'.
        print('Running \'amxmlc\' ...')
        os.chdir(dir_app)
        self.adobe_air_amxmlc_test(self.version)

        # Do keystore file logic.
        if not self.adobe_air_does_keystore_file_exist(dir_app):
            print('Keystore file does not exist, creating one with password [pass] ...')
            self.adobe_air_make_sample_cert()
            print('Keystore file created.')
        else:
            print('Keystore file exists.')

        # Uninstall test app.
        print('Uninstalling air.com.adjust.examples package from test device ...')
        adb_uninstall('air.com.adjust.examples')

        # Package test app APK file.
        print('Packaging APK file. Password will be entered automatically ...')
        self.adobe_air_package_apk_file()

        # Install test app.
        print('Installing air.com.adjust.examples package to test device ...')
        adb_install_apk('Main.apk')

        # Start test app.
        print('Test app installed. Starting the test app on the device ...')
        adb_shell_monkey('air.com.adjust.examples')

    @only_mac_os
    def build_and_run_app_test_ios(self):
        dir_app = os.path.join(self.project_root, 'test/app')
        file_app_xml = os.path.join(dir_app, 'Main-app.xml')

        path_prov_profile = os.environ.get('DEV_ADOBE_PROVISIONING_PROFILE_PATH')
        path_keystore_file = os.environ.get('KEYSTORE_FILE_PATH')

        # Remove Adjust SDK and test library ANE from test app.
        print('Removing SDK and test library ANE files from test app ...')
        remove_files_with_pattern('Adjust-*.*.*.ane', os.path.join(dir_app, 'lib/'))
        remove_files_with_pattern('AdjustTest-*.*.*.ane', os.path.join(dir_app, 'lib/'))

        # Copy Adjust SDK and test library ANE files to test app.
        print('Copying SDK and test library ANE files to test app ...')
        create_dir_if_not_present('{0}/lib'.format(dir_app))
        copy_file(os.path.join(self.project_root, f'Adjust-{self.version}.ane'),
                  os.path.join(dir_app, 'lib', f'Adjust-{self.version}.ane'))
        copy_file(os.path.join(self.project_root, f'AdjustTest-{self.version}.ane'),
                  os.path.join(dir_app, 'lib', f'AdjustTest-{self.version}.ane'))

        # Run 'amxmlc'.
        print('Running \'amxmlc\' ...')
        os.chdir(dir_app)
        self.adobe_air_amxmlc_test(self.version)

        # Do keystore file logic.
        if not self.adobe_air_does_keystore_file_exist(dir_app):
            print('Keystore file does not exist, creating one with password [pass] ...')
            self.adobe_air_make_sample_cert()
            print('Keystore file created.')
        else:
            print('Keystore file exists.')

        # Package example app IPA file.
        print('Packaging IPA file ...')
        self.adobe_air_package_ipa_file(path_prov_profile, path_keystore_file, file_app_xml)

    @staticmethod
    def __reacreate_ane_dirs(dir_build):

        # Remove 'catalog.xml' file.
        remove_file_if_exists(os.path.join(dir_build, 'default/catalog.xml'))

        # Recreate build directories.
        recreate_dir(os.path.join(dir_build, 'Android'))
        recreate_dir(os.path.join(dir_build, 'Android64'))
        recreate_dir(os.path.join(dir_build, 'iOS'))
        recreate_dir(os.path.join(dir_build, 'Android-x86'))
        recreate_dir(os.path.join(dir_build, 'iOS-x86'))

    def build_ane_sdk(self):
        dir_build = os.path.join(self.project_root, 'build')
        dir_src = os.path.join(self.project_root, 'src')
        dir_ext_android = os.path.join(self.project_root, 'ext/android')
        dir_ext_ios = os.path.join(self.project_root, 'ext/ios')

        # Check for presence of submodule directories.
        print('Checking for presence of submodules directories ...')
        self.check_submodule_dir('iOS', os.path.join(dir_ext_ios, 'sdk'))
        self.check_submodule_dir('Android', os.path.join(dir_ext_android, 'sdk'))

        # Go to root directory.
        print('Moving to root directory ...')
        os.chdir(self.project_root)

        # Recreate 'build' directory and it's 'default' sub-directory.
        print('Recreating \'build\' and \'build/default\' directories ...')
        recreate_dir(dir_build)
        recreate_dir('{0}/default'.format(dir_build))

        # Run 'compc' command.
        print('Running compc ...')
        self.adobe_air_compc_sdk(self.project_root, dir_build)

        self.__reacreate_ane_dirs(dir_build)

        # Copy generated files into build directories.
        copy_file(os.path.join(dir_ext_android, 'adjust-android.jar'),
                  os.path.join(dir_build, 'Android/adjust-android.jar'))
        copy_file(os.path.join(dir_ext_android, 'adjust-android.jar'),
                  os.path.join(dir_build, 'Android64/adjust-android.jar'))
        copy_file(os.path.join(dir_ext_ios, 'libAdjustExtension.a'),
                  os.path.join(dir_build, 'iOS/libAdjustExtension.a'))
        copy_dir_content(os.path.join(dir_ext_ios, 'AdjustSdk.framework'),
                         os.path.join(dir_build, 'AdjustSdk.framework'))
        copy_file(os.path.join(dir_ext_android, 'adjust-android.jar'),
                  os.path.join(dir_build, 'Android-x86/adjust-android.jar'))
        copy_file(os.path.join(dir_ext_ios, 'libAdjustExtension.a'),
                  os.path.join(dir_build, 'iOS-x86/libAdjustExtension.a'))
        copy_dir_content(os.path.join(dir_ext_ios, 'AdjustSdk.framework'),
                         os.path.join(dir_build, 'iOS-x86/AdjustSdk.framework'))

        # Generate .swc file.
        print('Making SWC file ...')
        self.adobe_air_compc_swc_sdk(self.project_root, dir_build)

        # Generate SDK ANE file.
        print('Running ADT and finalizing the ANE file generation ...')
        self.adobe_air_unzip(os.path.join(dir_build, 'Android'), os.path.join(dir_build, 'Adjust.swc'))
        self.adobe_air_unzip(os.path.join(dir_build, 'Android64'), os.path.join(dir_build, 'Adjust.swc'))
        self.adobe_air_unzip(os.path.join(dir_build, 'iOS'), os.path.join(dir_build, 'Adjust.swc'))
        self.adobe_air_unzip(os.path.join(dir_build, 'Android-x86'), os.path.join(dir_build, 'Adjust.swc'))
        self.adobe_air_unzip(os.path.join(dir_build, 'iOS-x86'), os.path.join(dir_build, 'Adjust.swc'))
        copy_file(os.path.join(dir_src, 'platformoptions_ios.xml'),
                  os.path.join(dir_build, 'iOS/platformoptions_ios.xml'))
        copy_file(os.path.join(dir_src, 'platformoptions_ios.xml'),
                  os.path.join(dir_build, 'iOS-x86/platformoptions_ios.xml'))
        copy_file(os.path.join(dir_src, 'extension.xml'), os.path.join(dir_build, 'extension.xml'))
        os.chdir(dir_build)
        self.adobe_air_adt_sdk(self.version)

    def build_ane_test(self):
        dir_plugin = os.path.join(self.project_root, 'test/plugin')
        dir_plugin_android = os.path.join(dir_plugin, 'android')
        dir_plugin_ios = os.path.join(dir_plugin, 'ios')
        dir_plugin_src = os.path.join(dir_plugin, 'src')
        dir_plugin_build = os.path.join(dir_plugin, 'build')

        # Go to root directory.
        print('Moving to root directory ...')
        os.chdir(dir_plugin)

        # Recreate 'build' directory and it's 'default' sub-directory.
        print('Recreating \'build\' and \'build/default\' directories ...')
        recreate_dir(dir_plugin_build)
        recreate_dir('{0}/default'.format(dir_plugin_build))

        # Run 'compc' command.
        print('Running compc ...')
        self.adobe_air_compc_test(dir_plugin, dir_plugin_build)

        self.__reacreate_ane_dirs(dir_plugin_build)

        # Copy generated files into build directories.
        copy_file(os.path.join(dir_plugin_android, 'adjust-android-test.jar'),
                  os.path.join(dir_plugin_build, 'Android/adjust-android-test.jar'))
        copy_file(os.path.join(dir_plugin_android, 'src/AdjustTestExtension/extension/libs/gson-2.8.6.jar'),
                  os.path.join(dir_plugin_build, 'Android/gson-2.8.6.jar'))
        copy_file(os.path.join(dir_plugin_android, 'src/AdjustTestExtension/extension/libs/Java-WebSocket-1.4.0.jar'),
                  os.path.join(dir_plugin_build, 'Android/Java-WebSocket-1.4.0.jar'))
        copy_file(os.path.join(dir_plugin_android, 'src/AdjustTestExtension/extension/libs/slf4j-api-1.7.30.jar'),
                  os.path.join(dir_plugin_build, 'Android/slf4j-api-1.7.30.jar'))
        copy_file(os.path.join(dir_plugin_android, 'adjust-android-test.jar'),
                  os.path.join(dir_plugin_build, 'Android64/adjust-android-test.jar'))
        copy_file(os.path.join(dir_plugin_android, 'src/AdjustTestExtension/extension/libs/gson-2.8.6.jar'),
                  os.path.join(dir_plugin_build, 'Android64/gson-2.8.6.jar'))
        copy_file(os.path.join(dir_plugin_android, 'src/AdjustTestExtension/extension/libs/Java-WebSocket-1.4.0.jar'),
                  os.path.join(dir_plugin_build, 'Android64/Java-WebSocket-1.4.0.jar'))
        copy_file(os.path.join(dir_plugin_android, 'src/AdjustTestExtension/extension/libs/slf4j-api-1.7.30.jar'),
                  os.path.join(dir_plugin_build, 'Android64/slf4j-api-1.7.30.jar'))
        copy_file(os.path.join(dir_plugin_ios, 'libAdjustTestExtension.a'),
                  os.path.join(dir_plugin_build, 'iOS/libAdjustTestExtension.a'))
        copy_dir_content(os.path.join(dir_plugin_ios, 'AdjustTestLibrary.framework'),
                         os.path.join(dir_plugin_build, 'iOS/AdjustTestLibrary.framework'))
        copy_file(os.path.join(dir_plugin_android, 'adjust-android-test.jar'),
                  os.path.join(dir_plugin_build, 'Android-x86/adjust-android-test.jar'))
        copy_file(os.path.join(dir_plugin_android, 'src/AdjustTestExtension/extension/libs/gson-2.8.6.jar'),
                  os.path.join(dir_plugin_build, 'Android-x86/gson-2.8.6.jar'))
        copy_file(os.path.join(dir_plugin_android, 'src/AdjustTestExtension/extension/libs/Java-WebSocket-1.4.0.jar'),
                  os.path.join(dir_plugin_build, 'Android-x86/Java-WebSocket-1.4.0.jar'))
        copy_file(os.path.join(dir_plugin_android, 'src/AdjustTestExtension/extension/libs/slf4j-api-1.7.30.jar'),
                  os.path.join(dir_plugin_build, 'Android-x86/slf4j-api-1.7.30.jar'))
        copy_file(os.path.join(dir_plugin_ios, 'libAdjustTestExtension.a'),
                  os.path.join(dir_plugin_build, 'iOS-x86/libAdjustTestExtension.a'))
        copy_dir_content(os.path.join(dir_plugin_ios, 'AdjustTestLibrary.framework'),
                         os.path.join(dir_plugin_build, 'iOS-x86/AdjustTestLibrary.framework'))

        # Generate .swc file.
        print('Making SWC file ...')
        self.adobe_air_compc_swc_test(dir_plugin, dir_plugin_build)

        # Generate SDK test ANE file.
        print('Running ADT and finalizing the ANE file generation ...')
        self.adobe_air_unzip(os.path.join(dir_plugin_build, 'Android'),
                             os.path.join(dir_plugin_build, 'AdjustTest.swc'))
        self.adobe_air_unzip(os.path.join(dir_plugin_build, 'Android64'),
                             os.path.join(dir_plugin_build, 'AdjustTest.swc'))
        self.adobe_air_unzip(os.path.join(dir_plugin_build, 'iOS'), os.path.join(dir_plugin_build, 'AdjustTest.swc'))
        self.adobe_air_unzip(os.path.join(dir_plugin_build, 'Android-x86'),
                             os.path.join(dir_plugin_build, 'AdjustTest.swc'))
        self.adobe_air_unzip(os.path.join(dir_plugin_build, 'iOS-x86'),
                             os.path.join(dir_plugin_build, 'AdjustTest.swc'))
        copy_file(os.path.join(dir_plugin_src, 'platformoptions_android_test.xml'),
                  os.path.join(dir_plugin_build, 'Android/platformoptions_android_test.xml'))
        copy_file(os.path.join(dir_plugin_src, 'platformoptions_android_test.xml'),
                  os.path.join(dir_plugin_build, 'Android64/platformoptions_android_test.xml'))
        copy_file(os.path.join(dir_plugin_src, 'platformoptions_ios_test.xml'),
                  os.path.join(dir_plugin_build, 'iOS/platformoptions_ios_test.xml'))
        copy_file(os.path.join(dir_plugin_src, 'platformoptions_android_test.xml'),
                  os.path.join(dir_plugin_build, 'Android-x86/platformoptions_android_test.xml'))
        copy_file(os.path.join(dir_plugin_src, 'platformoptions_ios_test.xml'),
                  os.path.join(dir_plugin_build, 'iOS-x86/platformoptions_ios_test.xml'))
        copy_file(os.path.join(dir_plugin_src, 'extension.xml'), os.path.join(dir_plugin_build, 'extension.xml'))
        os.chdir(dir_plugin_build)
        self.adobe_air_adt_test(self.project_root, dir_plugin_build, self.version)

    @staticmethod
    def check_submodule_dir(build_platform, submodule_dir):
        if not os.path.isdir(submodule_dir) or not os.listdir(submodule_dir):
            print(
                '[Error] [{0}] submodule folder empty. Did you forget to run \'git submodule update --init '
                '--recursive\'?'.format(
                    build_platform))
            exit()

    @staticmethod
    def adobe_air_compc_sdk(root_dir, build_dir):
        path_air_sdk = os.environ.get('AIR_SDK_PATH')
        file_swc = os.path.join(path_air_sdk, 'frameworks/libs/air/airglobal.swc')
        compc = os.path.join(path_air_sdk, 'bin/compc')
        dir_src = os.path.join(root_dir, 'default/src')
        dir_output = os.path.join(build_dir, 'default')

        execute_command(compc, '-source-path', dir_src, '-external-library-path',
                        file_swc, '-include-classes', 'com.adjust.sdk.Adjust', 'com.adjust.sdk.LogLevel',
                        'com.adjust.sdk.Environment',
                        'com.adjust.sdk.UrlStrategy', 'com.adjust.sdk.AdjustConfig', 'com.adjust.sdk.AdjustAttribution',
                        'com.adjust.sdk.AdjustEventSuccess',
                        'com.adjust.sdk.AdjustEventFailure', 'com.adjust.sdk.AdjustEvent',
                        'com.adjust.sdk.AdjustSessionSuccess',
                        'com.adjust.sdk.AdjustSessionFailure', 'com.adjust.sdk.AdjustTestOptions', '-directory=true',
                        '-output', dir_output)

    @staticmethod
    def adobe_air_compc_swc_sdk(root_dir, build_dir):
        air_sdk_path = os.environ.get('AIR_SDK_PATH')
        compc = os.path.join(air_sdk_path, 'bin/compc')
        src_dir = os.path.join(root_dir, 'src')
        external_lib_path = os.path.join(air_sdk_path, 'frameworks/libs/air/airglobal.swc')

        execute_command(compc, '-source-path', src_dir, '-external-library-path',
                        external_lib_path, '-include-classes', 'com.adjust.sdk.Adjust', 'com.adjust.sdk.LogLevel',
                        'com.adjust.sdk.Environment',
                        'com.adjust.sdk.UrlStrategy', 'com.adjust.sdk.AdjustConfig',
                        'com.adjust.sdk.AdjustAttribution',
                        'com.adjust.sdk.AdjustEventSuccess',
                        'com.adjust.sdk.AdjustEventFailure', 'com.adjust.sdk.AdjustEvent',
                        'com.adjust.sdk.AdjustSessionSuccess',
                        'com.adjust.sdk.AdjustSessionFailure', 'com.adjust.sdk.AdjustTestOptions', '-output',
                        '{0}/Adjust.swc'.format(build_dir))

    @staticmethod
    def adobe_air_unzip(dir_path, adjust_swc_path):
        execute_command('unzip', '-d', dir_path, '-qq', '-o', adjust_swc_path, '-x', 'catalog.xml')

    @staticmethod
    def adobe_air_adt_sdk(version):
        air_sdk_path = os.environ.get('AIR_SDK_PATH')
        adt = os.path.join(air_sdk_path, 'bin/adt')

        execute_command(
            adt, '-package', '-target', 'ane', '../Adjust-{0}.ane'.format(version), 'extension.xml', '-swc',
            'Adjust.swc',
            '-platform', 'Android-ARM', '-C', 'Android', '.',
            '-platform', 'Android-ARM64', '-C', 'Android64', '.',
            '-platform', 'Android-x86', '-C', 'Android-x86', '.',
            '-platform', 'iPhone-ARM', '-C', 'iOS', '.', '-platformoptions', 'iOS/platformoptions_ios.xml',
            '-platform', 'iPhone-x86', '-C', 'iOS-x86', '.',
            '-platform', 'default', '-C', 'default', '.')

    @staticmethod
    def adobe_air_compc_test(root_dir, build_dir):
        air_sdk_path = os.environ.get('AIR_SDK_PATH')
        compc = os.path.join(air_sdk_path, 'bin/compc')
        default_src_dir = os.path.join(root_dir, 'default/src')
        external_lib_path = os.path.join(air_sdk_path, 'frameworks/libs/air/airglobal.swc')
        output_dir = os.path.join(build_dir, 'default')

        execute_command(compc, '-source-path', default_src_dir, '-external-library-path',
                        external_lib_path, '-include-classes', 'com.adjust.test.AdjustTest', '-directory=true',
                        '-output', output_dir)

    @staticmethod
    def adobe_air_compc_swc_test(root_dir, build_dir):
        air_sdk_path = os.environ.get('AIR_SDK_PATH')
        compc = os.path.join(air_sdk_path, 'bin/compc')
        src_dir = os.path.join(root_dir, 'src')
        external_lib_path = os.path.join(air_sdk_path, 'frameworks/libs/air/airglobal.swc')

        execute_command(compc, '-source-path', src_dir, '-external-library-path',
                        external_lib_path, '-include-classes', 'com.adjust.test.AdjustTest', '-output',
                        '{0}/AdjustTest.swc'.format(build_dir))

    @staticmethod
    def adobe_air_adt_test(root_dir, build_dir, version):
        air_sdk_path = os.environ.get('AIR_SDK_PATH')
        adt = os.path.join(air_sdk_path, 'bin/adt')

        execute_command(
            adt, '-package', '-target', 'ane', '{0}/AdjustTest-{1}.ane'.format(root_dir, version), 'extension.xml',
            '-swc', 'AdjustTest.swc',
            '-platform', 'Android-ARM', '-C', 'Android', '.', '-platformoptions',
            '{0}/Android/platformoptions_android_test.xml'.format(build_dir),
            '-platform', 'Android-ARM64', '-C', 'Android64', '.', '-platformoptions',
            '{0}/Android/platformoptions_android_test.xml'.format(build_dir),
            '-platform', 'Android-x86', '-C', 'Android-x86', '.',
            '-platform', 'iPhone-ARM', '-C', 'iOS', '.', '-platformoptions',
            '{0}/iOS/platformoptions_ios_test.xml'.format(build_dir),
            '-platform', 'iPhone-x86', '-C', 'iOS-x86', '.',
            '-platform', 'default', '-C', 'default', '.')
