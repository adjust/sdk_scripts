from adobe.utils import *
import os

from decorators import only_mac_os

dir_root = get_root_dir()


# ------------------------------------------------------------------
# Common interface.

# Build SDK extension for given platform and build mode ('release' by default).
def build_extension_sdk(build_platform, build_mode='release'):
    if build_platform == 'android':
        build_extension_sdk_android(build_mode)
    elif build_platform == 'ios':
        build_extension_sdk_ios(build_mode)


# Build test extension for given platform and build mode ('release' by default).
def build_extension_test(build_platform, build_mode='release'):
    if build_platform == 'android':
        build_extension_test_android(build_mode)
    elif build_platform == 'ios':
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
    dir_ext = os.path.join(dir_root, 'ext/android')
    dir_bld_extension = os.path.join(dir_ext, 'src/AdjustExtension')
    dir_src_extension = os.path.join(dir_ext, 'src/AdjustExtension/extension/src/main/java/com/adjust/sdk')
    dir_src_sdk = os.path.join(dir_ext, 'sdk/Adjust/sdk-core/src/main/java/com/adjust/sdk')
    dir_src_jar = os.path.join(dir_ext, 'src/AdjustExtension/extension/build/libs/', build_mode)

    # Update Android extension souce files from SDK extension directory.
    debug_green('Update all Android SDK source files in the extension source directory ...')
    excluded_files = [
        os.path.join(dir_src_extension, 'AdjustActivity.java'),
        os.path.join(dir_src_extension, 'AdjustExtension.java'),
        os.path.join(dir_src_extension, 'AdjustFunction.java'),
        os.path.join(dir_src_extension, 'AdjustContext.java')]
    change_dir(dir_root)
    clean_dir('*', dir_src_extension, excluded_files)
    copy_dir_content(dir_src_sdk, dir_src_extension)

    # Build Android extension JAR.
    debug_green('Building adjust-android.jar of the Android extension ...')
    change_dir(dir_bld_extension)
    if build_mode == 'release':
        execute_command(['./gradlew', 'clean', 'makeReleaseJar'])
    else:
        execute_command(['./gradlew', 'clean', 'makeDebugJar'])

    # Copy generated Android extension JAR to it's destination directory.
    debug_green('Copying generated adjust-android.jar from {0} to {1} ...'.format(dir_src_jar, dir_ext))
    copy_file('{0}/adjust-android.jar'.format(dir_src_jar), '{0}/adjust-android.jar'.format(dir_ext))


# Build Adobe AIR SDK test library Android extension JAR in debug mode.
def build_extension_test_android_debug():
    build_extension_test_android('debug')


# Build Adobe AIR SDK test library Android extension JAR in release mode.
def build_extension_test_android_release():
    build_extension_test_android('release')


# Build Adobe AIR SDK test library Android extension JAR.
def build_extension_test_android(build_mode='release'):
    dir_plugin = os.path.join(dir_root, 'test/plugin/android')
    dir_bld_extension = os.path.join(dir_plugin, 'src/AdjustTestExtension')
    dir_src_extension = os.path.join(dir_bld_extension, 'extension/src/main/java/com/adjust/test')
    dir_src_test = os.path.join(dir_root, 'ext/android/sdk/Adjust/test-library/src/main/java/com/adjust/test')
    dir_src_jar = os.path.join(dir_bld_extension, 'extension/build/libs/', build_mode)

    # Update Android test extension souce files from SDK extension directory.
    debug_green('Update all Android SDK test library source files in the extension source directory ...')
    excluded_files = [
        os.path.join(dir_src_extension, 'AdjustTestExtension.java'),
        os.path.join(dir_src_extension, 'AdjustTestFunction.java'),
        os.path.join(dir_src_extension, 'AdjustTestContext.java'),
        os.path.join(dir_src_extension, 'CommandListener.java')]
    change_dir(dir_root)
    clean_dir('*', dir_src_extension, excluded_files)
    copy_dir_content(dir_src_test, dir_src_extension)

    # Build Android test extension JAR.
    debug_green('Building adjust-android-test.jar of the Android test extension ...')
    change_dir(dir_bld_extension)
    if build_mode == 'release':
        execute_command(['./gradlew', 'clean', 'makeReleaseJar'])
    else:
        execute_command(['./gradlew', 'clean', 'makeDebugJar'])

    # Copy generated Android test extension JAR to it's destination directory.
    debug_green('Copying generated adjust-android-test.jar from {0} to {1} ...'.format(dir_src_jar, dir_plugin))
    copy_file('{0}/adjust-android-test.jar'.format(dir_src_jar), '{0}/adjust-android-test.jar'.format(dir_plugin))


# ------------------------------------------------------------------
# iOS interface.

# Build Adobe AIR SDK iOS extension .a library in debug mode.
@only_mac_os
def build_extension_sdk_ios_debug():
    build_extension_sdk_ios('debug')


# Build Adobe AIR iOS SDK extension .a library in release mode.
@only_mac_os
def build_extension_sdk_ios_release():
    build_extension_sdk_ios('release')


# Build Adobe AIR iOS SDK extension .a library.
@only_mac_os
def build_extension_sdk_ios(build_mode='release'):
    dir_ext = os.path.join(dir_root, 'ext/ios')
    dir_sdk = os.path.join(dir_ext, 'sdk')
    dir_src_extension = os.path.join(dir_ext, 'src/AdjustExtension')

    # Remove static AdjustSdk.framework.
    debug_green('Removing existing static AdjustSdk.framework ...')
    recreate_dir(os.path.join(dir_sdk, 'Frameworks/Static'))

    # Rebuild static AdjustSdk.framework.
    debug_green('Rebuilding static AdjustSdk.framework in {0} mode ...'.format(build_mode))
    change_dir(dir_sdk)
    xcode_rebuild('AdjustStatic', build_mode.capitalize())

    # Copy static AdjustSdk.framework to it's destination.
    copy_dir_content(os.path.join(dir_sdk, 'Frameworks/Static/AdjustSdk.framework'),
                     os.path.join(dir_src_extension, 'include/Adjust/AdjustSdk.framework'))
    copy_dir_content(os.path.join(dir_sdk, 'Frameworks/Static/AdjustSdk.framework'),
                     os.path.join(dir_ext, 'AdjustSdk.framework'))

    # Build iOS extension .a library.
    debug_green('Building Adobe AIR iOS SDK extension .a library and outputing it to {0} ...'.format(dir_ext))
    change_dir(dir_src_extension)
    xcode_rebuild_custom_destination('AdjustExtension', build_mode.capitalize(), dir_ext)


# Build Adobe AIR SDK test library iOS extension .a library in debug mode.
@only_mac_os
def build_extension_test_ios_debug():
    build_extension_test_ios('debug')


# Build Adobe AIR SDK test library iOS extension .a library in release mode.
@only_mac_os
def build_extension_test_ios_release():
    build_extension_test_ios('release')


# Build Adobe AIR SDK test library iOS extension .a library.
@only_mac_os
def build_extension_test_ios(build_mode='release'):
    dir_plugin = os.path.join(dir_root, 'test/plugin/ios')
    dir_ext = os.path.join(dir_root, 'ext/ios')
    dir_src_extension = os.path.join(dir_root, 'test/plugin/ios/src/AdjustTestExtension')
    dir_test_lib = os.path.join(dir_ext, 'sdk/AdjustTests/AdjustTestLibrary')
    dir_frameworks = os.path.join(dir_ext, 'sdk/Frameworks/Static')

    # Remove static AdjustTestLibrary.framework.
    debug_green('Removing existing static AdjustTestLibrary.framework ...')
    recreate_dir(dir_frameworks)

    # Rebuild static AdjustTestLibrary.framework.
    debug_green('Rebuilding static AdjustTestLibrary.framework in {0} mode ...'.format(build_mode))
    change_dir(dir_test_lib)
    xcode_rebuild('AdjustTestLibraryStatic', build_mode.capitalize())

    # Copy static AdjustTestLibrary.framework to it's destination.
    copy_dir_content(os.path.join(dir_frameworks, 'AdjustTestLibrary.framework'),
                     os.path.join(dir_src_extension, 'AdjustTestLibrary.framework'))
    copy_dir_content(os.path.join(dir_frameworks, 'AdjustTestLibrary.framework'),
                     os.path.join(dir_plugin, 'AdjustTestLibrary.framework'))

    # Build iOS test extension .a library.
    debug_green(
        'Building Adobe AIR SDK test library iOS extension .a library and outputing it to {0} ...'.format(dir_plugin))
    change_dir(dir_src_extension)
    xcode_rebuild_custom_destination('AdjustTestExtension', build_mode.capitalize(), dir_plugin)
