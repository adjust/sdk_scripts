import configparser

config = configparser.ConfigParser()
config.read_file(open('config.ini'))

a = config.get('Default', 'a')
b = config.get('Default', 'b')
s = config.get('Default', 's')

print(a, type(a))
print(b, type(b))
print(s, type(s))


for i in config['Default'].items():
    print(i)