from adobe.utils import *
import os

from decorators import only_mac_os

dir_root = get_root_dir()
version = get_version_string()


def build_and_run_app_example_android():
    dir_app = os.path.join(dir_root, 'example')

    # Remove Adjust SDK ANE from example app.
    debug_green('Removing SDK ANE file from example app ...')
    remove_files_with_pattern('Adjust-*.*.*.ane', os.path.join(dir_app, 'lib/'))

    # Copy newly generated Adjust SDK ANE to example app.
    debug_green('Copying SDK ANE file to example app ...')
    create_dir_if_not_present(os.path.join(dir_app, 'lib/'))
    copy_file(os.path.join(dir_root, f'Adjust-{version}.ane'), os.path.join(dir_app, 'lib', f'Adjust-{version}.ane'))

    # Run 'amxmlc'.
    debug_green('Running \'amxmlc\' ...')
    change_dir(dir_app)
    adobe_air_amxmlc_example(version)

    # Do keystore file logic.
    if not adobe_air_does_keystore_file_exist(dir_app):
        debug_green('Keystore file does not exist, creating one with password [pass] ...')
        adobe_air_make_sample_cert()
        debug_green('Keystore file created.')
    else:
        debug_green('Keystore file exists.')

    # Uninstall example app.
    debug_green('Uninstalling air.com.adjust.examples package from test device ...')
    adb_uninstall('air.com.adjust.examples')

    # Package example app APK file.
    debug_green('Packaging APK file. Password will be entered automatically ...')
    adobe_air_package_apk_file()

    # Install example app.
    debug_green('Installing air.com.adjust.examples package to test device ...')
    adb_install_apk('Main.apk')

    # Start example app.
    debug_green('Example app installed. Starting the example app on the device ...')
    adb_shell_monkey('air.com.adjust.examples')


def build_and_run_app_test_android():
    dir_app = os.path.join(dir_root, 'test/app')

    # Remove Adjust SDK and test library ANE from test app.
    debug_green('Removing SDK and test library ANE files from test app ...')
    remove_files_with_pattern('Adjust-*.*.*.ane', os.path.join(dir_app, 'lib/'))
    remove_files_with_pattern('AdjustTest-*.*.*.ane', os.path.join(dir_app, 'lib/'))

    # Copy Adjust SDK and test library ANE files to test app.
    debug_green('Copying SDK and test library ANE files to test app ...')
    create_dir_if_not_present(os.path.join(dir_app, 'lib'))
    copy_file(os.path.join(dir_root, f'Adjust-{version}.ane'), os.path.join(dir_app, 'lib', f'Adjust-{version}.ane'))
    copy_file(os.path.join(dir_root, f'AdjustTest-{version}.ane'),
              os.path.join(dir_app, 'lib', f'AdjustTest-{version}.ane'))

    # Run 'amxmlc'.
    debug_green('Running \'amxmlc\' ...')
    change_dir(dir_app)
    adobe_air_amxmlc_test(version)

    # Do keystore file logic.
    if not adobe_air_does_keystore_file_exist(dir_app):
        debug_green('Keystore file does not exist, creating one with password [pass] ...')
        adobe_air_make_sample_cert()
        debug_green('Keystore file created.')
    else:
        debug_green('Keystore file exists.')

    # Uninstall test app.
    debug_green('Uninstalling air.com.adjust.examples package from test device ...')
    adb_uninstall('air.com.adjust.examples')

    # Package test app APK file.
    debug_green('Packaging APK file. Password will be entered automatically ...')
    adobe_air_package_apk_file()

    # Install test app.
    debug_green('Installing air.com.adjust.examples package to test device ...')
    adb_install_apk('Main.apk')

    # Start test app.
    debug_green('Test app installed. Starting the test app on the device ...')
    adb_shell_monkey('air.com.adjust.examples')


@only_mac_os
def build_and_run_app_example_ios():
    dir_app = os.path.join(dir_root, 'example')
    file_app_xml = os.path.join(dir_app, 'Main-app.xml')

    path_prov_profile = get_env_variable('DEV_ADOBE_PROVISIONING_PROFILE_PATH')
    path_keystore_file = get_env_variable('KEYSTORE_FILE_PATH')

    # Remove Adjust SDK ANE from example app.
    debug_green('Removing SDK ANE file from example app ...')
    remove_files_with_pattern('Adjust-*.*.*.ane', os.path.join(dir_app, 'lib/'))

    # Copy newly generated Adjust SDK ANE to example app.
    debug_green('Copying SDK ANE file to example app ...')
    create_dir_if_not_present(os.path.join(dir_app, 'lib'))
    copy_file(os.path.join(dir_root, f'Adjust-{version}.ane'), os.path.join(dir_app, 'lib', f'Adjust-{version}.ane'))

    # Run 'amxmlc'.
    debug_green('Running \'amxmlc\' ...')
    change_dir(dir_app)
    adobe_air_amxmlc_example(version)

    # Do keystore file logic.
    if not adobe_air_does_keystore_file_exist(dir_app):
        debug_green('Keystore file does not exist, creating one with password [pass] ...')
        adobe_air_make_sample_cert()
        debug_green('Keystore file created.')
    else:
        debug_green('Keystore file exists.')

    # Package example app IPA file.
    debug_green('Packaging IPA file ...')
    adobe_air_package_ipa_file(path_prov_profile, path_keystore_file, file_app_xml)


@only_mac_os
def build_and_run_app_test_ios():
    dir_app = os.path.join(dir_root, 'test/app')
    file_app_xml = os.path.join(dir_app, 'Main-app.xml')

    path_prov_profile = get_env_variable('DEV_ADOBE_PROVISIONING_PROFILE_PATH')
    path_keystore_file = get_env_variable('KEYSTORE_FILE_PATH')

    # Remove Adjust SDK and test library ANE from test app.
    debug_green('Removing SDK and test library ANE files from test app ...')
    remove_files_with_pattern('Adjust-*.*.*.ane', os.path.join(dir_app, 'lib/'))
    remove_files_with_pattern('AdjustTest-*.*.*.ane', os.path.join(dir_app, 'lib/'))

    # Copy Adjust SDK and test library ANE files to test app.
    debug_green('Copying SDK and test library ANE files to test app ...')
    create_dir_if_not_present('{0}/lib'.format(dir_app))
    copy_file(os.path.join(dir_root, f'Adjust-{version}.ane'), os.path.join(dir_app, 'lib', f'Adjust-{version}.ane'))
    copy_file(os.path.join(dir_root, f'AdjustTest-{version}.ane'),
              os.path.join(dir_app, 'lib', f'AdjustTest-{version}.ane'))

    # Run 'amxmlc'.
    debug_green('Running \'amxmlc\' ...')
    change_dir(dir_app)
    adobe_air_amxmlc_test(version)

    # Do keystore file logic.
    if not adobe_air_does_keystore_file_exist(dir_app):
        debug_green('Keystore file does not exist, creating one with password [pass] ...')
        adobe_air_make_sample_cert()
        debug_green('Keystore file created.')
    else:
        debug_green('Keystore file exists.')

    # Package example app IPA file.
    debug_green('Packaging IPA file ...')
    adobe_air_package_ipa_file(path_prov_profile, path_keystore_file, file_app_xml)
