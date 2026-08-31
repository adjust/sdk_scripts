import os, shutil, subprocess, sys

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
    subprocess.Popen(cmd, cwd=cwd, stdout=open(log_path, 'w'), stderr=subprocess.STDOUT, start_new_session=True)

# this file lives in <root>/ext/scripts/<platform>/, so <root> is three levels up
def root_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

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
