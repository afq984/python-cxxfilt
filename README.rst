cxxfilt |travis|
================

.. |travis| image:: https://travis-ci.org/afg984/python-cxxfilt.svg?branch=master
    :target: https://travis-ci.org/afg984/python-cxxfilt

Demangling C++ symbols in Python / interface to abi::__cxa_demangle

Usage
-----

Install::

    pip install cxxfilt

Use ``demangle`` to demangle a C++ mangled symbol name::

    >>> import cxxfilt
    >>> cxxfilt.demangle('_ZNSt22condition_variable_anyD2Ev')
    'std::condition_variable_any::~condition_variable_any()'

Non-mangled name will be kept intact::

    >>> cxxfilt.demangle('main')
    'main'

Invalid mangled names will trigger an ``InvalidName`` exception::

    >>> cxxfilt.demangle('_ZQQ')
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "/path/to/python-cxxfilt/cxxfilt/__init__.py", line 77, in demangle
        return demangleb(mangled_name.encode()).decode()
      File "/path/to/python-cxxfilt/cxxfilt/__init__.py", line 69, in demangleb
        raise InvalidName(mangled_name)
    cxxfilt.InvalidName: b'_ZQQ'

Use ``demangleb`` to demangle name in ``bytes``::

    >>> cxxfilt.demangleb(b'_ZNSt22condition_variable_anyD2Ev')
    b'std::condition_variable_any::~condition_variable_any()'


Supported environments
----------------------

Python 2.7 / 3.3+

Tested on Arch Linux and FreeBSD. Should work on unix systems with libc and libc++/libstdc++

Will not work on Windows.

Testing
-------

run in shell::

    pytest
