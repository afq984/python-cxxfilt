cxxfilt |ci|
============

.. |ci| image:: https://github.com/afq984/python-cxxfilt/actions/workflows/test.yml/badge.svg
    :target: https://github.com/afq984/python-cxxfilt/actions/workflows/test.yml

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

To demangle an internal symbol, use `external_only=False`::

    >>> cxxfilt.demangle('N3foo12BarExceptionE')
    'N3foo12BarExceptionE'
    >>> cxxfilt.demangle('N3foo12BarExceptionE', external_only=False)
    'foo::BarException'

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

Make custom `Demangler` objects to use specific C/C++ libraries::

    >>> from ctypes.util import find_library
    >>>
    >>> d = cxxfilt.Demangler(find_library('c'), find_library('stdc++'))
    >>> d
    <Demangler libc='libc.so.6' libcxx='libstdc++.so.6'>
    >>>
    >>> d = cxxfilt.Demangler(find_library('c'), find_library('c++'))
    >>> d
    <Demangler libc='libc.so.6' libcxx='libc++.so.1'>
    >>> d.demangle('_ZNSt22condition_variable_anyD2Ev')
    'std::condition_variable_any::~condition_variable_any()'

Supported environments
----------------------

Python 3.6 or greater.

Tested on Linux and macOS (see github actions). Should work on unix systems with libc and libc++/libstdc++.

Will not work on Windows (PR welcome though).

For Python 2.7 please use cxxfilt version < 0.3.

Changelog
---------

0.3.0
~~~~~

*   Added ``Demangler`` class.

*   ``import cxxfilt`` no longer fails when there are no C/C++ libraries available.
    To check whether the default demangler is valid,
    use the expression: ``not isinstance(cxxfilt.default_demangler, cxxfilt.DeferedErrorDemangler)``.


Testing
-------

run in shell::

    pytest
