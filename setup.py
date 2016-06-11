from distutils.core import setup
try:
    with open('VERSION.txt', 'r') as v:
        version = v.read().strip()
except FileNotFoundError:
    version = '0.0.0-dev'

setup(
  name = 'pyserver',
  packages = ['pyserver'], # this must be the same as the name above
  description = 'TCP/UDP Aysnchronous Server/Client Library',
  author = 'Woong Gyu La',
  author_email = 'juhgiyo@gmail.com',
  version=version,
  url = 'https://github.com/juhgiyo/pyserver', # use the URL to the github repo
    keywords = ['tcp', 'udp', 'server', 'library'], # arbitrary keywords
  license='MIT',
  classifiers = [],
)