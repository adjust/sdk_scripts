from adobe.utils import *

dir_root = get_root_dir()
version = get_version_string()


# FIXME split these functions by platform

# Build Adobe AIR SDK ANE.
def build_ane_sdk():
    dir_build = os.path.join(dir_root, 'build')
    dir_src = os.path.join(dir_root, 'src')
    dir_ext_android = os.path.join(dir_root, 'ext/android')
    dir_ext_ios = os.path.join(dir_root, 'ext/ios')

    # Check for presence of submodule directories.
    debug_green('Checking for presence of submodules directories ...')
    check_submodule_dir('iOS', os.path.join(dir_ext_ios, '/sdk'))
    check_submodule_dir('Android', os.path.join(dir_ext_android, '/sdk'))

    # Go to root directory.
    debug_green('Moving to root directory ...')
    change_dir(dir_root)

    # Recreate 'build' directory and it's 'default' sub-directory.
    debug_green('Recreating \'build\' and \'build/default\' directories ...')
    recreate_dir(dir_build)
    recreate_dir('{0}/default'.format(dir_build))

    # Run 'compc' command.
    debug_green('Running compc ...')
    adobe_air_compc_sdk(dir_root, dir_build)

    # Remove 'catalog.xml' file.
    remove_file_if_exists(os.path.join(dir_build, 'default/catalog.xml'))

    # Recreate build directories.
    recreate_dir(os.path.join(dir_build, 'Android'))
    recreate_dir(os.path.join(dir_build, 'Android64'))
    recreate_dir(os.path.join(dir_build, 'iOS'))
    recreate_dir(os.path.join(dir_build, 'Android-x86'))
    recreate_dir(os.path.join(dir_build, 'iOS-x86'))

    # Copy generated files into build directories.
    copy_file(os.path.join(dir_ext_android, 'adjust-android.jar'),
              os.path.join(dir_build, 'Android/adjust-android.jar'))
    copy_file(os.path.join(dir_ext_android, 'adjust-android.jar'),
              os.path.join(dir_build, 'Android64/adjust-android.jar'))
    copy_file(os.path.join(dir_ext_ios, 'libAdjustExtension.a'), os.path.join(dir_build, 'iOS/libAdjustExtension.a'))
    copy_dir_content(os.path.join(dir_ext_ios, 'AdjustSdk.framework'), os.path.join(dir_build, 'AdjustSdk.framework'))
    copy_file(os.path.join(dir_ext_android, 'adjust-android.jar'),
              os.path.join(dir_build, 'Android-x86/adjust-android.jar'))
    copy_file(os.path.join(dir_ext_ios, 'libAdjustExtension.a'),
              os.path.join(dir_build, 'iOS-x86/libAdjustExtension.a'))
    copy_dir_content(os.path.join(dir_ext_ios, 'AdjustSdk.framework'),
                     os.path.join(dir_build, 'iOS-x86/AdjustSdk.framework'))

    # Generate .swc file.
    debug_green('Making SWC file ...')
    adobe_air_compc_swc_sdk(dir_root, dir_build)

    # Generate SDK ANE file.
    debug_green('Running ADT and finalizing the ANE file generation ...')
    adobe_air_unzip(os.path.join(dir_build, 'Android'), os.path.join(dir_build, 'Adjust.swc'))
    adobe_air_unzip(os.path.join(dir_build, 'Android64'), os.path.join(dir_build, 'Adjust.swc'))
    adobe_air_unzip(os.path.join(dir_build, 'iOS'), os.path.join(dir_build, 'Adjust.swc'))
    adobe_air_unzip(os.path.join(dir_build, 'Android-x86'), os.path.join(dir_build, 'Adjust.swc'))
    adobe_air_unzip(os.path.join(dir_build, 'iOS-x86'), os.path.join(dir_build, 'Adjust.swc'))
    copy_file(os.path.join(dir_src, 'platformoptions_ios.xml'), os.path.join(dir_build, 'iOS/platformoptions_ios.xml'))
    copy_file(os.path.join(dir_src, 'platformoptions_ios.xml'),
              os.path.join(dir_build, 'iOS-x86/platformoptions_ios.xml'))
    copy_file(os.path.join(dir_src, 'extension.xml'), os.path.join(dir_build, 'extension.xml'))
    change_dir(dir_build)
    adobe_air_adt_sdk(version)


# Build Adobe AIR SDK test library ANE.
def build_ane_test():
    dir_plugin = os.path.join(dir_root, 'test/plugin')
    dir_plugin_android = os.path.join(dir_plugin, 'android')
    dir_plugin_ios = os.path.join(dir_plugin, 'ios')
    dir_plugin_src = os.path.join(dir_plugin, 'src')
    dir_plugin_build = os.path.join(dir_plugin, 'build')

    # Go to root directory.
    debug_green('Moving to root directory ...')
    change_dir(dir_plugin)

    # Recreate 'build' directory and it's 'default' sub-directory.
    debug_green('Recreating \'build\' and \'build/default\' directories ...')
    recreate_dir(dir_plugin_build)
    recreate_dir('{0}/default'.format(dir_plugin_build))

    # Run 'compc' command.
    debug_green('Running compc ...')
    adobe_air_compc_test(dir_plugin, dir_plugin_build)

    # Remove 'catalog.xml' file.
    remove_file_if_exists(os.path.join(dir_plugin_build, 'default/catalog.xml'))

    # Recreate build directories.
    recreate_dir(os.path.join(dir_plugin_build, 'Android'))
    recreate_dir(os.path.join(dir_plugin_build, 'Android64'))
    recreate_dir(os.path.join(dir_plugin_build, 'iOS'))
    recreate_dir(os.path.join(dir_plugin_build, 'Android-x86'))
    recreate_dir(os.path.join(dir_plugin_build, 'iOS-x86'))

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
    debug_green('Making SWC file ...')
    adobe_air_compc_swc_test(dir_plugin, dir_plugin_build)

    # Generate SDK test ANE file.
    debug_green('Running ADT and finalizing the ANE file generation ...')
    adobe_air_unzip(os.path.join(dir_plugin_build, 'Android'), os.path.join(dir_plugin_build, 'AdjustTest.swc'))
    adobe_air_unzip(os.path.join(dir_plugin_build, 'Android64'), os.path.join(dir_plugin_build, 'AdjustTest.swc'))
    adobe_air_unzip(os.path.join(dir_plugin_build, 'iOS'), os.path.join(dir_plugin_build, 'AdjustTest.swc'))
    adobe_air_unzip(os.path.join(dir_plugin_build, 'Android-x86'), os.path.join(dir_plugin_build, 'AdjustTest.swc'))
    adobe_air_unzip(os.path.join(dir_plugin_build, 'iOS-x86'), os.path.join(dir_plugin_build, 'AdjustTest.swc'))
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
    change_dir(dir_plugin_build)
    adobe_air_adt_test(dir_root, dir_plugin_build, version)
