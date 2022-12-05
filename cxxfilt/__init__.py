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


class DWORD(ctypes.c_uint):
    pass


def find_any_library(*choices: str) -> str:
    for choice in choices:
        lib = ctypes.util.find_library(choice)
        if lib is not None:
            return lib


class BaseDemangler(abc.ABC):
    @abc.abstractmethod
    def demangleb(self, mangled_name: bytes, external_only: bool = True) -> bytes:
        raise NotImplementedError

    def demangle(self, mangled_name: str, external_only: bool = True) -> str:
        return self.demangleb(
            mangled_name.encode(), external_only=external_only
        ).decode()

    @abc.abstractmethod
    def is_demangling_through_cxa(self):
        pass


class Demangler(BaseDemangler):
    def __init__(self, libc_name: str, libcxx_name: str, dbghelp_name: str) -> None:
        assert isinstance(libc_name, str), libc_name

        self._libc_name = libc_name
        self._libcxx_name = libcxx_name
        self._dbghelp_name = dbghelp_name

        libc = ctypes.CDLL(libc_name)
        libcxx = ctypes.CDLL(libcxx_name) if libcxx_name else None
        libdbghelp = ctypes.CDLL(dbghelp_name) if dbghelp_name else None

        self._free = libc.free
        self._free.argtypes = [ctypes.c_void_p]

        # @note: @es3n1n: to avoid undefined attrs we would explicitly init all funcs
        # here
        self._cxa_demangle = None
        self._UnDecorateSymbolName = None

        if libcxx_name:
            # use getattr to workaround with python's own name mangling
            self._cxa_demangle = getattr(libcxx, '__cxa_demangle')
            self._cxa_demangle.restype = CharP

        if dbghelp_name:
            self._UnDecorateSymbolName = getattr(libdbghelp, 'UnDecorateSymbolName')
            self._UnDecorateSymbolName.restype = DWORD

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} libc={self._libc_name!r} libcxx={self._libcxx_name!r}>'

    def _demangle_via_cxa_demangle(self, mangled_name: bytes, external_only: bool = True) -> bytes:
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

    # @xref: https://learn.microsoft.com/en-us/windows/win32/api/dbghelp/nf-dbghelp-undecoratesymbolname
    # @todo: https://learn.microsoft.com/en-us/windows/win32/api/dbghelp/nf-dbghelp-undecoratesymbolname#parameters
    def _demangle_via_dbghelp(self, mangled_name: bytes, external_only: bool = True) -> bytes:
        mangled_name_p: ctypes.c_char_p = ctypes.c_char_p(mangled_name)

        DEMANGLED_NAME_P_SIZE: int = 255  # todo: dynamic result size
        demangled_name_p = ctypes.create_string_buffer(DEMANGLED_NAME_P_SIZE)  # todo: prob should be freed
        ctypes.memset(demangled_name_p, 0, DEMANGLED_NAME_P_SIZE)

        UNDNAME_NO_MS_KEYWORDS: int = 0x0002
        UNDNAME_NO_ACCESS_SPECIFIERS: int = 0x0080
        flags: int = UNDNAME_NO_ACCESS_SPECIFIERS | UNDNAME_NO_MS_KEYWORDS

        result_value: DWORD = self._UnDecorateSymbolName(mangled_name_p, demangled_name_p, DEMANGLED_NAME_P_SIZE, flags)
        if not result_value.value:
            raise InternalError('Something went wrong, result = {}, params = [{}, {}, {}, 0]'.format(
                str(result_value.value), hex(demangled_name_p.value), str(DEMANGLED_NAME_P_SIZE), str(flags)
            ))

        result: bytes = demangled_name_p.value[:result_value.value+1]

        if result == mangled_name:
            raise InvalidName(mangled_name)

        return result

    def demangleb(self, mangled_name: bytes, external_only: bool = True) -> bytes:
        # Wikipedia: All *external* mangled symbols begin with _Z
        if external_only and not mangled_name.startswith(b'_Z'):
            return mangled_name

        # @note: @es3n1n: if cxa demangle function is available we should definitely use it
        if self._cxa_demangle:
            return self._demangle_via_cxa_demangle(mangled_name, external_only)

        if self._UnDecorateSymbolName:
            return self._demangle_via_dbghelp(mangled_name, external_only)

        raise InternalError('No demanglers available. Something is off.')

    def is_demangling_through_cxa(self):
        return self._cxa_demangle


class DeferedErrorDemangler(BaseDemangler):
    def __init__(self, error: Exception) -> None:
        self._error = error

    def demangleb(self, mangled_name: bytes, external_only: bool = True) -> bytes:
        raise self._error

    def is_demangling_through_cxa(self):
        return True


def _get_default_demangler() -> BaseDemangler:
    try:
        libc = find_any_library('c', 'msvcrt')
        libcxx = find_any_library('stdc++', 'c++')
        dbghelp = find_any_library('dbghelp')

        if not libc:
            raise LibraryNotFound('Cannot find C library')

        if not libcxx and not dbghelp:
            raise LibraryNotFound('Cannot find libcxx/dbghelp')
    except LibraryNotFound as error:
        return DeferedErrorDemangler(error=error)

    return Demangler(libc, libcxx, dbghelp)


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
