import glob, os, shutil, subprocess, sys

TAG = 'SDK'

BOLD, RED, GREEN, BLUE, END = '\033[1m', '\033[31m', '\033[32m', '\033[34m', '\033[0m'

def set_log_tag(tag):
    global TAG
    TAG = tag

def _log(msg, color):
    print(f'{BOLD}* [{TAG}]{END} {color}{msg}{END}')

def info(msg):
    _log(msg, GREEN)

def error(msg):
    _log(msg, RED)

def run(cmd, allow_failure=False):
    _log(' '.join(cmd), BLUE)
    if allow_failure:
        subprocess.call(cmd)
    else:
        subprocess.check_call(cmd)

def output(cmd):
    return subprocess.check_output(cmd, text=True).strip()

def run_background(cmd, cwd, log_path):
    _log(f'{" ".join(cmd)} (background, log: {log_path})', BLUE)
    # fully detach from the terminal; with an inherited stdin, interactive tools like Metro keep
    # reading keystrokes from the tab and leave it unusable after the script exits
    subprocess.Popen(cmd, cwd=cwd, stdin=subprocess.DEVNULL, stdout=open(log_path, 'w'), stderr=subprocess.STDOUT, start_new_session=True)

# this file lives in <root>/ext/scripts/, so <root> is two levels up
def root_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

def require_dir(path):
    if not os.path.isdir(path) or not os.listdir(path):
        error(f'{path} is missing or empty. Run: git submodule update --init --recursive')
        sys.exit(1)

def change_dir(path):
    os.chdir(path)
    _log(f'cd {path}', BLUE)

def copy_file(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy(src, dst)
    _log(f'{src} -> {dst}', BLUE)

def copy_dir(src, dst, *skip):
    shutil.copytree(src, dst, dirs_exist_ok=True, ignore=shutil.ignore_patterns('.DS_Store', *skip))
    _log(f'{src} -> {dst}', BLUE)

def remove_dir(path):
    shutil.rmtree(path, ignore_errors=True)

def recreate_dir(path):
    shutil.rmtree(path, ignore_errors=True)
    os.makedirs(path)

# ------------------------------------------------------------------
# Adobe AIR

def debug(msg):
    _log(msg, '')

def debug_green(msg):
    info(msg)

def debug_blue(msg):
    _log(msg, BLUE)

def get_version_string():
    return open(root_dir() + '/VERSION').read()[:-1]

def get_scripts_dir():
    return os.path.dirname(os.path.realpath(__file__))

def get_root_dir():
    return root_dir()

def get_env_variable(var_name):
    return os.environ.get(var_name)

def check_submodule_dir(platform, submodule_dir):
    if not os.path.isdir(submodule_dir) or not os.listdir(submodule_dir):
        error('[{0}] submodule folder empty. Did you forget to run \'git submodule update --init --recursive\'?'.format(platform))
        exit()

def create_dir_if_not_present(dir):
    os.makedirs(dir, exist_ok=True)

def remove_file_if_exists(path):
    if os.path.exists(path):
        os.remove(path)
        debug('Deleted file {0}.'.format(path))
    else:
        error('Can not delete file {0}. File does not exist.'.format(path))

def remove_files_with_pattern(pattern, directory, excluded_files=[]):
    for item in glob.glob(directory + '/' + pattern):
        if item in excluded_files:
            debug('Skipping deletion of {0}.'.format(item))
            continue
        if os.path.isfile(item):
            os.remove(item)
        else:
            shutil.rmtree(item)
        debug('Deleted {0}.'.format(item))

def clean_dir(item_pattern, directory, excluded_files=[]):
    remove_files_with_pattern(item_pattern, directory, excluded_files)

def copy_dir_content(dir_source, dir_destination):
    shutil.copytree(dir_source, dir_destination, dirs_exist_ok=True)

def execute_command(cmd_params, log=True):
    if log:
        debug_blue('Executing: [{0}]'.format(' '.join([str(cmd) for cmd in cmd_params])))
    subprocess.call(cmd_params)

def xcode_rebuild(target, configuration):
    execute_command(['xcodebuild', '-target', target, '-configuration', configuration, 'clean', 'build', '-UseModernBuildSystem=NO'])

def xcode_rebuild_custom_destination(target, configuration, destination):
    execute_command(['xcodebuild', '-target', target, '-configuration', configuration, 'clean', 'build', 'CONFIGURATION_BUILD_DIR={0}'.format(destination), '-UseModernBuildSystem=NO'])

def adb_uninstall(package):
    execute_command(['adb', 'uninstall', package])

def adb_install_apk(path):
    execute_command(['adb', 'install', '-r', path])

def adb_shell_monkey(package):
    execute_command(['adb', 'shell', 'monkey', '-p', package, '1'])

def adobe_air_compc_sdk(root_dir, build_dir):
    path_air_sdk    = get_env_variable('AIR_SDK_PATH');
    file_swc        = '{0}/frameworks/libs/air/airglobal.swc'.format(path_air_sdk)
    compc           = '{0}/bin/compc'.format(path_air_sdk)
    dir_src         = '{0}/default/src'.format(root_dir)
    dir_output      = '{0}/default'.format(build_dir)

    execute_command([compc, '-source-path', dir_src, '-external-library-path',
        file_swc, '-include-classes', 'com.adjust.sdk.Adjust', 'com.adjust.sdk.AdjustLogLevel', 'com.adjust.sdk.AdjustEnvironment',
        'com.adjust.sdk.AdjustConfig', 'com.adjust.sdk.AdjustAttribution', 'com.adjust.sdk.AdjustEventSuccess',
        'com.adjust.sdk.AdjustEventFailure', 'com.adjust.sdk.AdjustEvent', 'com.adjust.sdk.AdjustSessionSuccess',
        'com.adjust.sdk.AdjustAdRevenue', 'com.adjust.sdk.AdjustAppStorePurchase', 'com.adjust.sdk.AdjustAppStoreSubscription',
        'com.adjust.sdk.AdjustDeeplink', 'com.adjust.sdk.AdjustPlayStorePurchase', 'com.adjust.sdk.AdjustPlayStoreSubscription',
        'com.adjust.sdk.AdjustPurchaseVerificationResult', 'com.adjust.sdk.AdjustThirdPartySharing',
        'com.adjust.sdk.AdjustSessionFailure', 'com.adjust.sdk.AdjustTestOptions', '-directory=true', '-output', dir_output])

def adobe_air_compc_test(root_dir, build_dir):
    air_sdk_path      = get_env_variable('AIR_SDK_PATH');
    compc             = '{0}/bin/compc'.format(air_sdk_path)
    default_src_dir   = '{0}/default/src'.format(root_dir)
    external_lib_path = '{0}/frameworks/libs/air/airglobal.swc'.format(air_sdk_path)
    output_dir        = '{0}/default'.format(build_dir)

    execute_command([compc, '-source-path', default_src_dir, '-external-library-path',
        external_lib_path, '-include-classes', 'com.adjust.test.AdjustTest', '-directory=true', '-output', output_dir])

def adobe_air_compc_swc_sdk(root_dir, build_dir):
    air_sdk_path      = get_env_variable('AIR_SDK_PATH');
    compc             = '{0}/bin/compc'.format(air_sdk_path)
    src_dir           = '{0}/src'.format(root_dir)
    external_lib_path = '{0}/frameworks/libs/air/airglobal.swc'.format(air_sdk_path)

    execute_command([compc, '-source-path', src_dir, '-external-library-path',
        external_lib_path, '-include-classes', 'com.adjust.sdk.Adjust', 'com.adjust.sdk.AdjustLogLevel', 'com.adjust.sdk.AdjustEnvironment',
        'com.adjust.sdk.AdjustConfig', 'com.adjust.sdk.AdjustAttribution', 'com.adjust.sdk.AdjustEventSuccess',
        'com.adjust.sdk.AdjustEventFailure', 'com.adjust.sdk.AdjustEvent', 'com.adjust.sdk.AdjustSessionSuccess',
        'com.adjust.sdk.AdjustAdRevenue', 'com.adjust.sdk.AdjustAppStorePurchase', 'com.adjust.sdk.AdjustAppStoreSubscription',
        'com.adjust.sdk.AdjustDeeplink', 'com.adjust.sdk.AdjustPlayStorePurchase', 'com.adjust.sdk.AdjustPlayStoreSubscription',
        'com.adjust.sdk.AdjustPurchaseVerificationResult', 'com.adjust.sdk.AdjustThirdPartySharing',
        'com.adjust.sdk.AdjustSessionFailure', 'com.adjust.sdk.AdjustTestOptions', '-output', '{0}/Adjust.swc'.format(build_dir)])

def adobe_air_compc_swc_test(root_dir, build_dir):
    air_sdk_path      = get_env_variable('AIR_SDK_PATH');
    compc             = '{0}/bin/compc'.format(air_sdk_path)
    src_dir           = '{0}/src'.format(root_dir)
    external_lib_path = '{0}/frameworks/libs/air/airglobal.swc'.format(air_sdk_path)

    execute_command([compc, '-source-path', src_dir, '-external-library-path',
        external_lib_path, '-include-classes', 'com.adjust.test.AdjustTest', '-output', '{0}/AdjustTest.swc'.format(build_dir)])

def adobe_air_adt_sdk(version):
    air_sdk_path  = get_env_variable('AIR_SDK_PATH');
    adt           = '{0}/bin/adt'.format(air_sdk_path)

    execute_command([adt, '-package', '-target', 'ane', '../Adjust-{0}.ane'.format(version), 'extension.xml', '-swc', 'Adjust.swc',
        '-platform', 'Android-ARM', '-C', 'Android', '.', '-platformoptions', 'Android/platformoptions_android.xml',
        '-platform', 'Android-ARM64', '-C', 'Android64', '.', '-platformoptions', 'Android/platformoptions_android.xml',
        '-platform', 'Android-x86', '-C', 'Android-x86', '.', '-platformoptions', 'Android/platformoptions_android.xml',
        '-platform', 'iPhone-ARM', '-C', 'iOS', '.', '-platformoptions', 'iOS/platformoptions_ios.xml',
        '-platform', 'iPhone-x86', '-C', 'iOS-x86', '.',
        '-platform', 'default', '-C', 'default', '.'])

def adobe_air_adt_test(root_dir, build_dir, version):
    air_sdk_path  = get_env_variable('AIR_SDK_PATH');
    adt           = '{0}/bin/adt'.format(air_sdk_path)

    execute_command([adt, '-package', '-target', 'ane', '{0}/AdjustTest-{1}.ane'.format(root_dir, version), 'extension.xml', '-swc', 'AdjustTest.swc',
        '-platform', 'Android-ARM', '-C', 'Android', '.', '-platformoptions', '{0}/Android/platformoptions_android_test.xml'.format(build_dir),
        '-platform', 'Android-ARM64', '-C', 'Android64', '.', '-platformoptions', '{0}/Android/platformoptions_android_test.xml'.format(build_dir),
        '-platform', 'Android-x86', '-C', 'Android-x86', '.',
        '-platform', 'iPhone-ARM', '-C', 'iOS', '.', '-platformoptions', '{0}/iOS/platformoptions_ios_test.xml'.format(build_dir),
        '-platform', 'iPhone-x86', '-C', 'iOS-x86', '.',
        '-platform', 'default', '-C', 'default', '.'])

def adobe_air_unzip(dir_path, adjust_swc_path):
    execute_command(['unzip', '-d', dir_path, '-qq', '-o', adjust_swc_path, '-x', 'catalog.xml'])

def adobe_air_amxmlc_example(version):
    execute_command(['amxmlc', '-external-library-path+=lib/Adjust-{0}.ane'.format(version), '-output=Main.swf', '--', 'Main.as'])

def adobe_air_amxmlc_test(version):
    execute_command(['amxmlc', '-external-library-path+=lib/Adjust-{0}.ane'.format(version),
        '-external-library-path+=lib/AdjustTest-{0}.ane'.format(version), '-output=Main.swf', '--', 'Main.as'])

def adobe_air_make_sample_cert():
    execute_command(['adt', '-certificate', '-validityPeriod', '25', '-cn', 'SelfSigned', '2048-RSA', 'sampleCert.pfx', 'pass'])

def adobe_air_package_apk_file():
    debug_blue('Packaging APK file, please wait ...')
    command = 'adt -package -target apk-debug -storetype pkcs12 -keystore sampleCert.pfx Main.apk Main-app.xml Main.swf -extdir lib'
    debug_blue('Executing: [{0}] ...'.format(command))
    os.system('echo pass|{0}'.format(command))
    debug_blue('Packaging APK file done.')

def adobe_air_package_ipa_file(prov_profile_path, keystore_file_path, example_app_xml_file):
    debug_blue('Packaging IPA file, please wait ...')
    command = """adt -package -target ipa-debug -provisioning-profile {0} -storetype pkcs12 -keystore {1} Main.ipa {2} Main.swf -extdir lib""".format(prov_profile_path, keystore_file_path, example_app_xml_file)
    debug_blue('Executing: [{0}]'.format(command))
    os.system('echo|{0}'.format(command))
    debug_blue('Packaging IPA file done')

def adobe_air_does_keystore_file_exist(dir_path):
    return len(glob.glob('{0}/*.pfx'.format(dir_path))) > 0
