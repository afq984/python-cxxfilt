from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

# reads __version__
__version__: str
with open(path.join(here, 'cxxfilt', 'version.py'), encoding='utf-8') as f:
    exec(f.read())

setup(
    name='cxxfilt',

    version=__version__,

    description='Python interface to c++filt / abi::__cxa_demangle',
    long_description=long_description,

    url='https://github.com/afq984/python-cxxfilt',

    author='afq984',
    author_email='afg984@gmail.com',

    license='BSD',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 3 - Alpha',

        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',

        'License :: OSI Approved :: BSD License',

        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],

    keywords='c++ c++filt name mangling',

    packages=find_packages(exclude=['tests']),

    extras_require={
        'test': ['pytest>=3.0.0'],
    },
)
