from utils import *

dir_root = get_root_dir()

# ------------------------------------------------------------------
# Common interface.

# Build SDK extension for given platform and build mode ('release' by default).
def build_extension_sdk(platform, build_mode='release'):
    if platform == 'android':
        build_extension_sdk_android(build_mode)
    elif platform == 'ios':
        build_extension_sdk_ios(build_mode)

# Build test extension for given platform and build mode ('release' by default).
def build_extension_test(platform, build_mode='release'):
    if platform == 'android':
        build_extension_test_android(build_mode)
    elif platform == 'ios':
        build_extension_test_ios(build_mode)

# ------------------------------------------------------------------
# Android interface.

# Build Adobe AIR SDK Android extension JAR in debug mode.
def build_extension_sdk_android_debug():
    build_extension_sdk_android('debug')

# Build Adobe AIR SDK Android extension JAR in release mode.
def build_extension_sdk_android_release():
    build_extension_sdk_android('release')

# Build Adobe AIR SDK Android extension JAR.
def build_extension_sdk_android(build_mode='release'):
    dir_ext             = '{0}/ext/android'.format(dir_root)
    dir_bld_extension   = '{0}/src/AdjustExtension'.format(dir_ext)
    dir_src_extension   = '{0}/src/AdjustExtension/extension/src/main/java/com/adjust/sdk'.format(dir_ext)
    dir_src_sdk         = '{0}/sdk/Adjust/sdk-core/src/main/java/com/adjust/sdk'.format(dir_ext)
    dir_src_aar         = '{0}/src/AdjustExtension/extension/build/outputs/aar'.format(dir_ext)
    # dir_src_jar         = '{0}/extension/build/intermediates/aar_main_jar/{1}/sync{2}LibJars'.format(dir_bld_extension, build_mode, build_mode.capitalize())

    # Update Android extension souce files from SDK extension directory.
    debug_green('Update all Android SDK source files in the extension source directory ...')
    excluded_files = [
        '{0}/AdjustActivity.java'.format(dir_src_extension), 
        '{0}/AdjustExtension.java'.format(dir_src_extension), 
        '{0}/AdjustFunction.java'.format(dir_src_extension), 
        '{0}/AdjustContext.java'.format(dir_src_extension)]
    change_dir(dir_root)
    clean_dir('*', dir_src_extension, excluded_files)
    copy_dir_content(dir_src_sdk, dir_src_extension)

    # Build Android extension JAR.
    debug_green('Building adjust-android.jar of the Android extension ...')
    change_dir(dir_bld_extension)
    if build_mode == 'release':
        execute_command(['./gradlew', 'clean', 'assembleRelease'])
    else:
        execute_command(['./gradlew', 'clean', 'assembleDebug'])

    # Copy generated Android extension AAR to it's destination directory.
    debug_green('Copying generated extension AAR from {0} to {1} ...'.format(dir_src_aar, dir_ext))
    copy_file('{0}/extension-{1}.aar'.format(dir_src_aar, build_mode), '{0}/adjust-android.aar'.format(dir_ext))

# Build Adobe AIR SDK test library Android extension JAR in debug mode.
def build_extension_test_android_debug():
    build_extension_test_android('debug')

# Build Adobe AIR SDK test library Android extension JAR in release mode.
def build_extension_test_android_release():
    build_extension_test_android('release')

# Build Adobe AIR SDK test library Android extension JAR.
def build_extension_test_android(build_mode='release'):
    dir_plugin              = '{0}/test/plugin/android'.format(dir_root)
    dir_bld_extension       = '{0}/src/AdjustTestExtension'.format(dir_plugin)
    dir_src_extension       = '{0}/extension/src/main/java/com/adjust/test'.format(dir_bld_extension)
    dir_src_test            = '{0}/ext/android/sdk/Adjust/tests/test-library/src/main/java/com/adjust/test'.format(dir_root)
    dir_src_jar             = '{0}/extension/build/intermediates/aar_main_jar/{1}/sync{2}LibJars'.format(dir_bld_extension, build_mode, build_mode.capitalize())
    # dir_src_jar             = '{0}/extension/build/intermediates/aar_main_jar/{1}/syncDebugLibJars'.format(dir_bld_extension, build_mode)
    dir_src_test_options    = '{0}/ext/android/sdk/Adjust/tests/test-options/build/intermediates/aar_main_jar/{1}'.format(dir_root, build_mode)

    # Update Android test extension souce files from SDK extension directory.
    debug_green('Update all Android SDK test library source files in the extension source directory ...')
    excluded_files = [
        '{0}/AdjustTestExtension.java'.format(dir_src_extension), 
        '{0}/AdjustTestFunction.java'.format(dir_src_extension), 
        '{0}/AdjustTestContext.java'.format(dir_src_extension), 
        '{0}/CommandListener.java'.format(dir_src_extension)]
    change_dir(dir_root)
    clean_dir('*', dir_src_extension, excluded_files)
    copy_dir_content(dir_src_test, dir_src_extension)

    # Build test options and copy the resulting JAR to its destination directory.
    change_dir('{0}/ext/android/sdk/Adjust'.format(dir_root))
    if build_mode == 'release':
        debug_green('Building native Android test options in release mode ...')
        execute_command(['./gradlew', 'clean', ':tests:test-options:assembleRelease'])
    else:
        debug_green('Building native Android test options in debug mode ...')
        execute_command(['./gradlew', 'clean', ':tests:test-options:assembleDebug'])

    debug_green('Copy native Android test options JAR from {0} to {1} dir ...'.format(dir_src_test_options, dir_bld_extension))
    if build_mode == 'release':
        copy_file('{0}/classes.jar'.format(dir_src_test_options), '{0}/extension/libs/adjust-android-test-options.jar'.format(dir_bld_extension))
    else:
        copy_file('{0}/classes.jar'.format(dir_src_test_options), '{0}/extension/libs/adjust-android-test-options.jar'.format(dir_bld_extension))

    # Build Android test extension JAR.
    debug_green('Building adjust-android-test.jar of the Android test extension ...')
    change_dir(dir_bld_extension)
    if build_mode == 'release':
        execute_command(['./gradlew', 'clean', 'makeReleaseJar'])
    else:
        execute_command(['./gradlew', 'clean', 'makeDebugJar'])

    # Copy generated Android fat test and test options JARs to their destination directory.
    debug_green('Copying generated adjust-android-test.jar from {0} to {1} ...'.format(dir_src_jar, dir_plugin))
    copy_file('{0}/classes.jar'.format(dir_src_jar), '{0}/adjust-android-test.jar'.format(dir_plugin))
    copy_file('{0}/extension/libs/adjust-android-test-options.jar'.format(dir_bld_extension), '{0}/adjust-android-test-options.jar'.format(dir_plugin))

# ------------------------------------------------------------------
# iOS interface.

# Build Adobe AIR SDK iOS extension .a library in debug mode.
def build_extension_sdk_ios_debug():
    build_extension_sdk_ios('debug')

# Build Adobe AIR iOS SDK extension .a library in release mode.
def build_extension_sdk_ios_release():
    build_extension_sdk_ios('release')

# Build Adobe AIR iOS SDK extension .a library.
def build_extension_sdk_ios(build_mode='release'):
    dir_ext             = '{0}/ext/ios'.format(dir_root)
    dir_sdk             = '{0}/sdk'.format(dir_ext)
    dir_src_extension   = '{0}/src/AdjustExtension'.format(dir_ext)

    # Remove static AdjustSdk.framework.
    debug_green('Removing existing static AdjustSdk.framework ...')
    recreate_dir('{0}/Frameworks/Static'.format(dir_sdk))

    # Rebuild static AdjustSdk.framework.
    debug_green('Rebuilding static AdjustSdk.framework in {0} mode ...'.format(build_mode))
    change_dir(dir_sdk)
    # xcode_rebuild('AdjustStatic', build_mode.capitalize())
    execute_command(['./scripts/build_frameworks.sh', '-fs', '-ios'])

    # Copy static AdjustSdk.framework to it's destination.
    copy_dir_content('{0}/sdk_distribution/frameworks-static/AdjustSdk-iOS-Static/AdjustSdk.framework'.format(dir_sdk), '{0}/include/Adjust/AdjustSdk.framework'.format(dir_src_extension))
    copy_dir_content('{0}/sdk_distribution/frameworks-static/AdjustSdk-iOS-Static/AdjustSdk.framework'.format(dir_sdk), '{0}/AdjustSdk.framework'.format(dir_ext))

    # Build iOS extension .a library.
    debug_green('Building Adobe AIR iOS SDK extension .a library and outputing it to {0} ...'.format(dir_ext))
    change_dir(dir_src_extension)
    xcode_rebuild_custom_destination('AdjustExtension', build_mode.capitalize(), dir_ext)

# Build Adobe AIR SDK test library iOS extension .a library in debug mode.
def build_extension_test_ios_debug():
    build_extension_test_ios('debug')

# Build Adobe AIR SDK test library iOS extension .a library in release mode.
def build_extension_test_ios_release():
    build_extension_test_ios('release')

# Build Adobe AIR SDK test library iOS extension .a library.
def build_extension_test_ios(build_mode='release'):
    dir_plugin          = '{0}/test/plugin/ios'.format(dir_root)
    dir_ext             = '{0}/ext/ios'.format(dir_root)
    dir_src_extension   = '{0}/test/plugin/ios/src/AdjustTestExtension'.format(dir_root)
    dir_test_lib        = '{0}/sdk/AdjustTests/AdjustTestLibrary'.format(dir_ext)
    # dir_frameworks      = '{0}/sdk/Frameworks/Static'.format(dir_ext)
    dir_frameworks      = '{0}/sdk/sdk_distribution/test-static-framework'.format(dir_ext)

    # Remove static AdjustTestLibrary.framework.
    debug_green('Removing existing static AdjustTestLibrary.framework ...')
    recreate_dir(dir_frameworks)

    # Rebuild static AdjustTestLibrary.framework.
    debug_green('Rebuilding static AdjustTestLibrary.framework in {0} mode ...'.format(build_mode))
    change_dir(dir_test_lib)
    xcode_rebuild('AdjustTestLibraryStatic', build_mode.capitalize())

    # Copy static AdjustTestLibrary.framework to it's destination.
    copy_dir_content('{0}/AdjustTestLibrary.framework'.format(dir_frameworks), '{0}/AdjustTestLibrary.framework'.format(dir_src_extension))
    copy_dir_content('{0}/AdjustTestLibrary.framework'.format(dir_frameworks), '{0}/AdjustTestLibrary.framework'.format(dir_plugin))

    # Build iOS test extension .a library.
    debug_green('Building Adobe AIR SDK test library iOS extension .a library and outputing it to {0} ...'.format(dir_plugin))
    change_dir(dir_src_extension)
    xcode_rebuild_custom_destination('AdjustTestExtension', build_mode.capitalize(), dir_plugin)
