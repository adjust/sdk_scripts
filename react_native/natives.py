from utils import *

dir_root = get_root_dir()

# ------------------------------------------------------------------
# build native SDK for given platform and build mode 
# 'release' mode used by default if none specified
# ------------------------------------------------------------------
def build_native_sdk(platform, build_mode='release'):
    if platform == 'android':
        build_native_sdk_android(build_mode)
    elif platform == 'ios':
        build_native_sdk_ios()

# ------------------------------------------------------------------
# build native test library for given platform and build mode
# 'release' mode used by default if none specified
# ------------------------------------------------------------------
def build_native_test_library(platform, build_mode='debug'):
    if platform == 'android':
        build_native_test_library_android(build_mode)
    elif platform == 'ios':
        build_native_test_library_ios()

# ------------------------------------------------------------------
# build native OAID plugin for given platform [android only!]
# 'release' mode used by default if none specified
# ------------------------------------------------------------------
def build_native_plugin_oaid(platform, build_mode='release'):
    if platform == 'android':
        build_native_plugin_oaid_android(build_mode)

# ------------------------------------------------------------------
# build native Android SDK
# ------------------------------------------------------------------
def build_native_sdk_android(build_mode='release'):
    dir_ext     = '{0}/ext/android'.format(dir_root)
    dir_sdk     = '{0}/ext/android/sdk'.format(dir_root)
    dir_build   = '{0}/Adjust'.format(dir_sdk)
    dir_jar_out = '{0}/android/libs'.format(dir_root)
    dir_jar_in  = '{0}/sdk-core/build/libs'.format(dir_build)

    os.chdir(dir_build)

    # ------------------------------------------------------------------
    # build the JAR
    # ------------------------------------------------------------------
    if build_mode == 'release':
        debug_green('Building native Android SDK in release mode ...')
        execute_command(['./gradlew', 'clean', 'adjustCoreJarRelease'])
    else:
        debug_green('Building native Android SDK in debug mode ...')
        execute_command(['./gradlew', 'clean', 'adjustCoreJarRelease'])

    # ------------------------------------------------------------------
    # move the built JAR to destination folder
    # ------------------------------------------------------------------
    debug_green('Moving native Android SDK JAR from {0} to {1} dir ...'.format(dir_jar_in, dir_jar_out))
    clear_dir(dir_jar_out)
    if build_mode == 'release':
        copy_files('adjust-sdk-release.jar', dir_jar_in, dir_jar_out)
        rename_file('adjust-sdk-release.jar', 'adjust-android.jar', dir_jar_out)
    else:
        copy_files('adjust-sdk-debug.jar', dir_jar_in, dir_jar_out)
        rename_file('adjust-sdk-debug.jar', 'adjust-android.jar', dir_jar_out)

# ------------------------------------------------------------------
# build native Android test library
# ------------------------------------------------------------------
def build_native_test_library_android(build_mode='debug'):
    dir_ext     = '{0}/ext/android'.format(dir_root)
    dir_sdk     = '{0}/ext/android/sdk'.format(dir_root)
    dir_build   = '{0}/Adjust'.format(dir_sdk)
    dir_jar_in  = '{0}/test-library/build/libs'.format(dir_build)
    dir_jar_out = '{0}/test/lib/android/libs'.format(dir_root)

    os.chdir(dir_build)

    # ------------------------------------------------------------------
    # build the JAR
    # ------------------------------------------------------------------
    if build_mode == 'release':
        debug_green('Building native Android test library in release mode ...')
        execute_command(['./gradlew', 'clean', ':test-library:adjustTestLibraryJarRelease'])
    else:
        debug_green('Building native Android test library in debug mode ...')
        execute_command(['./gradlew', 'clean', ':test-library:adjustTestLibraryJarDebug'])

    # ------------------------------------------------------------------
    # move the built JAR to destination folder
    # ------------------------------------------------------------------
    debug_green('Moving native Android SDK JAR from {0} to {1} dir ...'.format(dir_jar_in, dir_jar_out))
    clear_dir(dir_jar_out)
    if build_mode == 'release':
        copy_files('test-library-release.jar', dir_jar_in, dir_jar_out)
        rename_file('test-library-release.jar', 'adjust-test.jar', dir_jar_out)
    else:
        copy_files('test-library-debug.jar', dir_jar_in, dir_jar_out)
        rename_file('test-library-debug.jar', 'adjust-test.jar', dir_jar_out)

# ------------------------------------------------------------------
# build native Android OAID plugin
# ------------------------------------------------------------------
def build_native_plugin_oaid_android(build_mode='release'):
    dir_ext     = '{0}/ext/android'.format(dir_root)
    dir_sdk     = '{0}/ext/android/sdk'.format(dir_root)
    dir_build   = '{0}/Adjust'.format(dir_sdk)
    dir_jar_out = '{0}/plugins/oaid/android/libs'.format(dir_root)
    dir_jar_in  = '{0}/sdk-plugin-oaid/build/libs'.format(dir_build)

    os.chdir(dir_build)

    # ------------------------------------------------------------------
    # build the JAR
    # ------------------------------------------------------------------
    if build_mode == 'release':
        debug_green('Building native Android OAID plugin in release mode ...')
        execute_command(['./gradlew', 'clean', 'sdk-plugin-oaid:adjustOaidAndroidJar'])
    else:
        debug_green('Building native Android OAID plugin in debug mode ...')
        execute_command(['./gradlew', 'clean', 'sdk-plugin-oaid:adjustOaidAndroidJar'])

    # ------------------------------------------------------------------
    # move the built JAR to destination folder
    # ------------------------------------------------------------------
    debug_green('Moving native Android OAID plugin JAR from {0} to {1} dir ...'.format(dir_jar_in, dir_jar_out))
    clear_dir(dir_jar_out)
    if build_mode == 'release':
        copy_files('sdk-plugin-oaid.jar', dir_jar_in, dir_jar_out)
        rename_file('sdk-plugin-oaid.jar', 'adjust-android-oaid.jar', dir_jar_out)
    else:
        copy_files('sdk-plugin-oaid.jar', dir_jar_in, dir_jar_out)
        rename_file('sdk-plugin-oaid.jar', 'adjust-android-oaid.jar', dir_jar_out)

# ------------------------------------------------------------------
# build native iOS SDK
# ------------------------------------------------------------------
def build_native_sdk_ios():
    dir_ext     = '{0}/ext/ios'.format(dir_root)
    dir_sdk     = '{0}/ext/ios/sdk'.format(dir_root)
    dir_src     = '{0}/Adjust'.format(dir_sdk)
    dir_src_out = '{0}/ios/Adjust'.format(dir_root)

    debug_green('Copying iOS SDK source files from {0} to {1} ...'.format(dir_src, dir_src_out))
    copy_dir_content(dir_src, dir_src_out)

# ------------------------------------------------------------------
# build native iOS test library
# ------------------------------------------------------------------
def build_native_test_library_ios():
    dir_ext     = '{0}/ext/ios'.format(dir_root)
    dir_sdk     = '{0}/ext/ios/sdk'.format(dir_root)
    dir_src     = '{0}/AdjustTests/AdjustTestLibrary/AdjustTestLibrary/'.format(dir_sdk)
    dir_src_out = '{0}/test/lib/ios/AdjustTestLibrary/'.format(dir_root)

    debug_green('Copying iOS test library source files from {0} to {1} ...'.format(dir_src, dir_src_out))
    copy_dir_content(dir_src, dir_src_out)