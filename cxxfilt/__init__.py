import ctypes
import ctypes.util

from cxxfilt.version import __version__  # noqa


class Error(Exception):
    pass


class InternalError(Error):
    pass


class InvalidName(Error):
    '''Exception raised when:
    mangled_name is not a valid name under the C++ ABI mangling rules.'''

    def __init__(self, mangled_name):
        super(InvalidName, self).__init__()
        self.mangled_name = mangled_name

    def __str__(self):
        return repr(self.mangled_name)


class CharP(ctypes.c_char_p):
    pass


def find_any_library(*choices):
    for choice in choices:
        lib = ctypes.util.find_library(choice)
        if lib is not None:
            return lib
    raise Error('Cannot find any of libraries: {}'.format(choices))


libc = ctypes.CDLL(find_any_library('c'))
libc.free.argtypes = [ctypes.c_void_p]

libcxx = ctypes.CDLL(find_any_library('c++', 'stdc++'))
libcxx.__cxa_demangle.restype = CharP


def demangleb(mangled_name):
    # Wikipedia: All mangled symbols begin with _Z
    if not mangled_name.startswith(b'_Z'):
        return mangled_name

    mangled_name_p = ctypes.c_char_p(mangled_name)
    status = ctypes.c_int()
    retval = libcxx.__cxa_demangle(
        mangled_name_p,
        None,
        None,
        ctypes.pointer(status))

    try:
        demangled = retval.value
    finally:
        libc.free(retval)

    if status.value == 0:
        return demangled
    elif status.value == -1:
        raise InternalError('A memory allocation failiure occurred')
    elif status.value == -2:
        raise InvalidName(mangled_name)
    elif status.value == -3:
        raise InternalError('One of the arguments is invalid')
    else:
        raise InternalError('Unkwon status code: {}'.format(status.value))


def demangle(mangled_name):
    return demangleb(mangled_name.encode()).decode()
