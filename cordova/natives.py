from utils import *

dir_root = get_root_dir()

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
# build native test options for given platform and build mode
# 'release' mode used by default if none specified
# note: right now, only Android supports test options concept
# ------------------------------------------------------------------
def build_native_test_options(platform, build_mode='debug'):
    if platform == 'android':
        build_native_test_options_android(build_mode)

# ------------------------------------------------------------------
# build native Android test library
# ------------------------------------------------------------------
def build_native_test_library_android(build_mode='debug'):
    dir_ext     = '{0}/ext/android'.format(dir_root)
    dir_sdk     = '{0}/ext/android/sdk'.format(dir_root)
    dir_build   = '{0}/Adjust'.format(dir_sdk)
    dir_jar_src  = '{0}/test-library/build/libs'.format(dir_build)
    dir_jar_dst = '{0}/test/plugin/src/android'.format(dir_root)

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
    debug_green('Moving native Android test library JAR from {0} to {1} dir ...'.format(dir_jar_src, dir_jar_dst))
    clear_dir(dir_jar_dst)
    if build_mode == 'release':
        copy_files('test-library-release.jar', dir_jar_src, dir_jar_dst)
        rename_file('test-library-release.jar', 'adjust-test-library.jar', dir_jar_dst)
    else:
        copy_files('test-library-debug.jar', dir_jar_src, dir_jar_dst)
        rename_file('test-library-debug.jar', 'adjust-test-library.jar', dir_jar_dst)

# ------------------------------------------------------------------
# build native Android test options
# ------------------------------------------------------------------
def build_native_test_options_android(build_mode='debug'):
    dir_ext     = '{0}/ext/android'.format(dir_root)
    dir_sdk     = '{0}/ext/android/sdk'.format(dir_root)
    dir_build   = '{0}/Adjust'.format(dir_sdk)
    dir_jar_src  = '{0}/test-options/build/intermediates/aar_main_jar/{1}'.format(dir_build, build_mode)
    dir_jar_dst = '{0}/test/plugin/src/android'.format(dir_root)

    os.chdir(dir_build)

    # ------------------------------------------------------------------
    # build the JAR
    # ------------------------------------------------------------------
    if build_mode == 'release':
        debug_green('Building native Android test options in release mode ...')
        execute_command(['./gradlew', 'clean', ':test-options:assembleRelease'])
    else:
        debug_green('Building native Android test options in debug mode ...')
        execute_command(['./gradlew', 'clean', ':test-options:assembleDebug'])

    # ------------------------------------------------------------------
    # move the built JAR to destination folder
    # ------------------------------------------------------------------
    debug_green('Moving native Android test options JAR from {0} to {1} dir ...'.format(dir_jar_src, dir_jar_dst))
    # skipping cleaning of folder for now since it will wipe out adjust-test-library.jar
    # TODO: find nicer way to do this
    # clear_dir(dir_jar_dst)
    if build_mode == 'release':
        copy_files('classes.jar', dir_jar_src, dir_jar_dst)
        rename_file('classes.jar', 'adjust-test-options.jar', dir_jar_dst)
    else:
        copy_files('classes.jar', dir_jar_src, dir_jar_dst)
        rename_file('classes.jar', 'adjust-test-options.jar', dir_jar_dst)

# ------------------------------------------------------------------
# build native iOS test library
# ------------------------------------------------------------------
def build_native_test_library_ios():
    dir_ext                 = '{0}/ext/ios'.format(dir_root)
    dir_sdk                 = '{0}/ext/ios/sdk'.format(dir_root)
    dir_test_lib_project    = '{0}/AdjustTests/AdjustTestLibrary'.format(dir_ext)
    dir_test_lib_dst        = '{0}/test/plugin/src/ios'.format(dir_root)
    dir_frameworks          = '{0}/Frameworks/Static/'.format(dir_ext)

    # ------------------------------------------------------------------
    # remove old test library framework
    # ------------------------------------------------------------------
    debug_green('Removing old framework ...')
    remove_dir_if_exists('{0}/AdjustTestLibrary.framework'.format(dir_test_lib_dst))

    # ------------------------------------------------------------------
    # build new test library framework
    # ------------------------------------------------------------------
    debug_green('Building new test library framework ...')
    change_dir(dir_test_lib_project)
    xcode_build('AdjustTestLibraryStatic', configuration='Debug')

    # ------------------------------------------------------------------
    # copy built test library framework to designated location
    # ------------------------------------------------------------------
    debug_green('Copying built framework to designated location ...')
    copy_dir_contents('{0}/AdjustTestLibrary.framework'.format(dir_frameworks), '{0}/AdjustTestLibrary.framework'.format(dir_test_lib_dst))
    remove_dir_if_exists('{0}/AdjustTestLibrary.framework/Versions'.format(dir_test_lib_dst))