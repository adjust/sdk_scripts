import glob
import os
import shutil
import subprocess
from distutils.dir_util import copy_tree
from pathlib import Path

from decorators import only_mac_os


def execute_command(*args: str) -> int:
    return subprocess.call(args)


def create_dir_if_not_present(path):
    if not os.path.exists(path):
        os.makedirs(path)


def adb_uninstall(package):
    execute_command('adb', 'uninstall', package)


def adb_install_apk(path):
    execute_command('adb', 'install', '-r', path)


def adb_shell_monkey(package):
    execute_command('adb', 'shell', 'monkey', '-p', package, '1')


@only_mac_os
def xcode_rebuild_custom_destination(target, configuration, destination):
    execute_command('xcodebuild', '-target', target, '-configuration', configuration, 'clean', 'build',
                    'CONFIGURATION_BUILD_DIR={0}'.format(destination), '-UseModernBuildSystem=NO')


def xcode_rebuild(target, configuration):
    execute_command('xcodebuild', '-target', target, '-configuration', configuration, 'clean', 'build',
                    '-UseModernBuildSystem=NO')


def clear_dir(path, exclude_files=()):
    if len(exclude_files) == 0:
        if os.path.exists(path):
            shutil.rmtree(path)
        os.makedirs(path, exist_ok=True)
    else:
        for item in os.scandir(path):
            item: os.DirEntry
            if item.name in exclude_files:
                continue
            else:
                os.remove(item.path)


def copy_files(fileNamePattern, sourceDir, destDir):
    for file in glob.glob(os.path.join(sourceDir, fileNamePattern)):
        shutil.copy(file, destDir)


def rename_file(file_name_pattern, new_file_name, source_dir):
    for file in glob.glob(os.path.join(source_dir + '/' + file_name_pattern)):
        os.rename(file, os.path.join(source_dir, new_file_name))


def copy_dir_content(source_dir, dest_dir):
    copy_tree(source_dir, dest_dir)


def convert_to_abspath(path: str):
    if path.startswith('~'):
        return os.path.join(str(Path.home()), path[2:] if path[1] == '/' else path[1])
    return os.path.abspath(path)


def remove_dir_if_exists(path):
    if os.path.exists(path):
        shutil.rmtree(path)


def remove_files_with_pattern(pattern, directory, excluded_files=()):
    for item in glob.glob(directory + '/' + pattern):
        if item in excluded_files:
            print('[DEBUG] Skipping deletion of {0}.'.format(item))
            continue
        if os.path.isfile(item):
            os.remove(item)
        else:
            shutil.rmtree(item)
        print('[DEBUG] Deleted {0}.'.format(item))


def recreate_dir(path):
    if os.path.exists(path):
        shutil.rmtree(path)
    os.mkdir(path)


def copy_file(sourceFile, destFile):
    shutil.copyfile(sourceFile, destFile)


def remove_file_if_exists(path):
    if os.path.exists(path):
        os.remove(path)
        print('[DEBUG] Deleted file {0}.'.format(path))
    else:
        print('[ERROR] Can not delete file {0}. File does not exist.'.format(path))


def copy_content_to_temp_dir(dir_root):
    dir_temp = os.path.join(dir_root, 'temp')
    dir_ios = os.path.join(dir_root, 'ios')
    dir_android = os.path.join(dir_root, 'android')

    recreate_dir(dir_temp)
    copy_dir_content(dir_android, os.path.join(dir_temp, 'android'))
    copy_dir_content(dir_ios, os.path.join(dir_temp, 'ios'))
    copy_file(os.path.join(dir_root, 'package.json'), os.path.join(dir_temp, 'package.json'))
    copy_file(os.path.join(dir_root, 'react-native-adjust.podspec'),
              os.path.join(dir_temp, 'react-native-adjust.podspec'))
    copy_file(os.path.join(dir_root, 'index.js'), os.path.join(dir_temp, 'index.js'))
