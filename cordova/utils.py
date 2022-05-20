##
##  Various util python methods which can be utilized and shared among different scripts
## TODO: clean up this file and reuse it among all scripts inside of the sdk_scripts repo
##
import os, shutil, glob, time, sys, platform, subprocess
from distutils.dir_util import copy_tree

def set_log_tag(t):
    global TAG
    TAG = t

def set_log_tag(t):
    global TAG
    TAG = t

# ------------------------------------------------------------------
# Colours for terminal (does not work in Windows).

CEND = '\033[0m'

CBOLD     = '\33[1m'
CITALIC   = '\33[3m'
CURL      = '\33[4m'
CBLINK    = '\33[5m'
CBLINK2   = '\33[6m'
CSELECTED = '\33[7m'

CBLACK  = '\33[30m'
CRED    = '\33[31m'
CGREEN  = '\33[32m'
CYELLOW = '\33[33m'
CBLUE   = '\33[34m'
CVIOLET = '\33[35m'
CBEIGE  = '\33[36m'
CWHITE  = '\33[37m'

CBLACKBG  = '\33[40m'
CREDBG    = '\33[41m'
CGREENBG  = '\33[42m'
CYELLOWBG = '\33[43m'
CBLUEBG   = '\33[44m'
CVIOLETBG = '\33[45m'
CBEIGEBG  = '\33[46m'
CWHITEBG  = '\33[47m'

CGREY    = '\33[90m'
CRED2    = '\33[91m'
CGREEN2  = '\33[92m'
CYELLOW2 = '\33[93m'
CBLUE2   = '\33[94m'
CVIOLET2 = '\33[95m'
CBEIGE2  = '\33[96m'
CWHITE2  = '\33[97m'

CGREYBG    = '\33[100m'
CREDBG2    = '\33[101m'
CGREENBG2  = '\33[102m'
CYELLOWBG2 = '\33[103m'
CBLUEBG2   = '\33[104m'
CVIOLETBG2 = '\33[105m'
CBEIGEBG2  = '\33[106m'
CWHITEBG2  = '\33[107m'

# ------------------------------------------------------------------
# Log output methods.

def debug(msg):
    if not is_windows():
        print(('{0}* [{1}][INFO]:{2} {3}').format(CBOLD, TAG, CEND, msg))
    else:
        print(('* [{0}][INFO]: {1}').format(TAG, msg))

def debug_green(msg):
    if not is_windows():
        print(('{0}* [{1}][INFO]:{2} {3}{4}{5}').format(CBOLD, TAG, CEND, CGREEN, msg, CEND))
    else:
        print(('* [{0}][INFO]: {1}').format(TAG, msg))

def debug_blue(msg):
    if not is_windows():
        print(('{0}* [{1}][INFO]:{2} {3}{4}{5}').format(CBOLD, TAG, CEND, CBLUE, msg, CEND))
    else:
        print(('* [{0}][INFO]: {1}').format(TAG, msg))

def error(msg, do_exit=False):
    if not is_windows():
        print(('{0}* [{1}][ERROR]:{2} {3}{4}{5}').format(CBOLD, TAG, CEND, CRED, msg, CEND))
    else:
        print(('* [{0}][ERROR]: {1}').format(TAG, msg))

    if do_exit:
        exit()

############################################################
### file system util methods

def copy_file(sourceFile, destFile):
    debug('copying: {0} -> {1}'.format(sourceFile, destFile))
    shutil.copyfile(sourceFile, destFile)

def copy_files(fileNamePattern, sourceDir, destDir):
    for file in glob.glob(sourceDir + '/' + fileNamePattern):
        debug('copying: {0} -> {1}'.format(file, destDir))
        shutil.copy(file, destDir)

def copy_dir_content(sourceDir, destDir):
    copy_tree(sourceDir, destDir)

def remove_files(fileNamePattern, sourceDir, log=True):
    for file in glob.glob(sourceDir + '/' + fileNamePattern):
        if log:
            debug('deleting: ' + file)
        os.remove(file)

def rename_file(fileNamePattern, newFileName, sourceDir):
    for file in glob.glob(sourceDir + '/' + fileNamePattern):
        debug('rename: {0} -> {1}'.format(file, newFileName))
        os.rename(file, sourceDir + '/' + newFileName)

def clear_dir(dir):
    shutil.rmtree(dir)
    os.mkdir(dir)

def remove_dir_if_exists(dir):
    if os.path.exists(dir):
        shutil.rmtree(dir)

def recreate_dir(dir):
    if os.path.exists(dir):
        shutil.rmtree(dir)
    os.mkdir(dir)

# Get VERSION number string.
def get_version_string():
    dir_root = get_root_dir()
    version  = open(dir_root + '/VERSION').read()
    version  = version[:-1] # remove end character
    return version

# Get scripts directory path.
def get_scripts_dir():
    return os.path.dirname(os.path.realpath(__file__))

# Get SDK root directory path.
def get_root_dir():
    dir_scripts = get_scripts_dir()
    dir_platform = path_navigate_down(dir_scripts)
    dir_ext = path_navigate_down(dir_platform)
    return path_navigate_down(dir_ext)

# Get partent directory of the given path.
def path_navigate_down(dir_path):
    return os.path.dirname(os.path.normpath(dir_path));

# Remove files with certain pattern from given directory.
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

# Change to directory.
def change_dir(dir):
    os.chdir(dir)
    debug('Changed directory to {0}.'.format(dir))

############################################################
### util

# Execute given command.
def execute_command(cmd_params, log=True):
    if log:
        debug_blue('Executing: [{0}]'.format(' '.join([str(cmd) for cmd in cmd_params])))
    subprocess.call(cmd_params)

# ------------------------------------------------------------------
# Random stuff.

# Check if platform is Windows.
def is_windows():
    return platform.system().lower() == 'windows';

# Get system enviornment variable value.
def get_env_variable(var_name):
    return os.environ.get(var_name);

############################################################
### cordova specific

def _remove_platforms():
    debug_green('Removing platforms ...')
    cordova_remove_platform('android')
    cordova_remove_platform('ios')

def clean_test_app(root_dir):
    example_dir             = '{0}/example'.format(root_dir)
    sdk_name                = 'com.adjust.sdk'
    adjust_sdk_plugin_dir   = '{0}/plugins/com.adjust.sdk'.format(example_dir)

    debug_green('Removing cordova plugins ...')
    os.chdir(example_dir)
    subprocess.call(['cordova', 'plugin', 'rm', sdk_name])
    subprocess.call(['cordova', 'plugin', 'rm', 'cordova-plugin-console'])
    subprocess.call(['cordova', 'plugin', 'rm', 'cordova-plugin-customurlscheme'])
    subprocess.call(['cordova', 'plugin', 'rm', 'cordova-plugin-dialogs'])
    subprocess.call(['cordova', 'plugin', 'rm', 'cordova-plugin-whitelist'])
    subprocess.call(['cordova', 'plugin', 'rm', 'cordova-plugin-device'])
    subprocess.call(['cordova', 'plugin', 'rm', 'cordova-universal-links-plugin'])

    remove_dir_if_exists(adjust_sdk_plugin_dir)
    _remove_platforms()

def clean_example_app(root_dir):
    test_dir                    = '{0}/test/app'.format(root_dir)
    sdk_name                    = 'com.adjust.sdk'
    test_plugin_name            = 'com.adjust.test'
    adjust_sdk_plugin_dir       = '{0}/plugins/com.adjust.sdk'.format(test_dir)
    adjust_sdk_test_plugin_dir  = '{0}/plugins/com.adjust.test'.format(test_dir)

    debug_green('Removing cordova plugins ...')
    os.chdir(test_dir)
    subprocess.call(['cordova', 'plugin', 'rm', sdk_name])
    subprocess.call(['cordova', 'plugin', 'rm', test_plugin_name])

    remove_dir_if_exists(adjust_sdk_plugin_dir)
    remove_dir_if_exists(adjust_sdk_test_plugin_dir)
    _remove_platforms()

def cordova_add_plugin(plugin_name, options=None):
    cmd_params = ['cordova', 'plugin', 'add', plugin_name]
    if not options == None:
        for opt in options:
            cmd_params.append(opt)
    execute_command(cmd_params)

def cordova_remove_plugin(plugin_name):
    execute_command(['cordova', 'plugin', 'remove', plugin_name])

def cordova_build(platform, options=None):
    cmd_params = ['cordova', 'build', platform]
    if not options == None:
        for opt in options:
            cmd_params.append(opt)
    execute_command(cmd_params)

def cordova_run(platform):
    execute_command(['cordova', 'run', platform])

def cordova_add_platform(platform):
    execute_command(['cordova', 'platform', 'add', platform])

def cordova_remove_platform(platform):
    execute_command(['cordova', 'platform', 'remove', platform])

### xcode
def xcode_build(target, configuration='Release'):
    execute_command(['xcodebuild', '-target', target, '-configuration', configuration, 'clean', 'build', '-UseModernBuildSystem=NO'])

### adb
def adb_uninstall(package):
    execute_command(['adb', 'uninstall', package])

def adb_install_apk(path):
    execute_command(['adb', 'install', '-r', path])

def adb_shell(app_package):
    execute_command(['adb', 'shell', 'monkey', '-p', app_package, '1'])