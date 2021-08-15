import abc
import ctypes
import ctypes.util

from typing import Sequence, Union

from cxxfilt.version import __version__  # noqa


class Error(Exception):
    pass


class LibraryNotFound(Error):
    pass


class InternalError(Error):
    pass


class InvalidName(Error):
    '''Exception raised when:
    mangled_name is not a valid name under the C++ ABI mangling rules.'''

    def __init__(self, mangled_name: Union[str, bytes]) -> None:
        super(InvalidName, self).__init__()
        self.mangled_name = mangled_name

    def __str__(self) -> str:
        return repr(self.mangled_name)


class CharP(ctypes.c_char_p):
    pass


def find_any_library(*choices: str) -> str:
    for choice in choices:
        lib = ctypes.util.find_library(choice)
        if lib is not None:
            return lib
    raise LibraryNotFound('Cannot find any of libraries: {}'.format(choices))


class BaseDemangler(abc.ABC):
    @abc.abstractmethod
    def demangleb(self, mangled_name: bytes, external_only: bool = True) -> bytes:
        raise NotImplementedError

    def demangle(self, mangled_name: str, external_only: bool = True) -> str:
        return self.demangleb(
            mangled_name.encode(), external_only=external_only
        ).decode()


class Demangler(BaseDemangler):
    def __init__(self, libc_name: str, libcxx_name: str) -> None:
        assert isinstance(libc_name, str), libc_name
        assert isinstance(libcxx_name, str), libcxx_name

        self._libc_name = libc_name
        libc = ctypes.CDLL(libc_name)
        self._free = libc.free
        self._free.argtypes = [ctypes.c_void_p]

        self._libcxx_name = libcxx_name
        libcxx = ctypes.CDLL(libcxx_name)
        # use getattr to workaround with python's own name mangling
        self._cxa_demangle = getattr(libcxx, '__cxa_demangle')
        self._cxa_demangle.restype = CharP

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} libc={self._libc_name!r} libcxx={self._libcxx_name!r}>'

    def demangleb(self, mangled_name: bytes, external_only: bool = True) -> bytes:
        # Wikipedia: All *external* mangled symbols begin with _Z
        if external_only and not mangled_name.startswith(b'_Z'):
            return mangled_name

        mangled_name_p = ctypes.c_char_p(mangled_name)
        status = ctypes.c_int()
        retval = self._cxa_demangle(mangled_name_p, None, None, ctypes.pointer(status))

        try:
            demangled = retval.value
        finally:
            self._free(retval)

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


class DeferedErrorDemangler(BaseDemangler):
    def __init__(self, error: Exception) -> None:
        self._error = error

    def demangleb(self, mangled_name: bytes, external_only: bool = True) -> bytes:
        raise self._error


def _get_default_demangler() -> BaseDemangler:
    try:
        libc = find_any_library('c')
        libcxx = find_any_library('stdc++', 'c++')
    except LibraryNotFound as error:
        return DeferedErrorDemangler(error=error)
    return Demangler(libc, libcxx)


default_demangler: BaseDemangler = _get_default_demangler()


def demangle(mangled_name: str, external_only: bool = True) -> str:
    return default_demangler.demangle(
        mangled_name=mangled_name,
        external_only=external_only,
    )


def demangleb(mangled_name: bytes, external_only: bool = True) -> bytes:
    return default_demangler.demangleb(
        mangled_name=mangled_name,
        external_only=external_only,
    )
