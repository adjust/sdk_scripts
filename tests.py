import os


def test_react_native_build():
    build_platforms = ['android', 'ios']
    targets = ['sdk', 'test-library', 'test-options', 'plugin-oaid']
    modes = ['debug', 'release']

    for build_platform in build_platforms:
        for target in targets:
            for mode in modes:
                command = f'python3 main.py react-native build-native --target-type={target} --build-platform={build_platform} --mode={mode}'
                print(f'{command}')
                os.system(command)


def test_adobe_build_ane():
    targets = ['sdk', 'test']
    for target in targets:
        command = f'python3 main.py adobe build-ane --app-type={target}'
        print(command)
        os.system(command)
        input()


def test_adobe_build_extension():
    build_platforms = ['android', 'ios']
    targets = ['sdk', 'test']
    modes = ['debug', 'release']

    for build_platform in build_platforms:
        for target in targets:
            for mode in modes:
                command = f'python3 main.py adobe build-extension --app-type={target} --build-platform={build_platform} --mode={mode}'
                print(f'{command}')
                os.system(command)
                input(f'{build_platform}-{target}-{mode} ended! Press [Enter]')


#test_react_native_build()
# test_adobe_build_extension()
# print('-' * 20)
#
#test_adobe_build_ane()

