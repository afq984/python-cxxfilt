from __future__ import annotations

import abc
import ctypes
import ctypes.util
from typing import Union

from cxxfilt.version import __version__  # noqa

__all__ = [
    "Error",
    "LibraryNotFoundError",
    "InternalError",
    "InvalidNameError",
    "Demangler",
    "demangle",
    "demangleb",
]


class Error(Exception):
    """Base class for all cxxfilt exceptions."""

    pass


# can be subclassed from FileNotFoundError?
# see https://stackoverflow.com/a/36077407
class LibraryNotFoundError(Error):
    """Raised when a required library is not found"""

    def __init__(self, choices: list[str]) -> None:
        super().__init__()
        self.choices = choices

    def __repr__(self) -> str:
        return f"Couldn't find any of the libraries: {self.choices}"

    __str__ = __repr__


class InternalError(Error):
    """Raised when libcxx.__cxa_demangle fails."""

    ERROR_STRINGS = {
        -1: "A memory allocation failure occurred",
        -3: "One of the arguments is invalid",
    }

    def __init__(self, ret_code: int) -> None:
        super().__init__()
        self.ret_code = ret_code

    def __repr__(self):
        try:
            return self.ERROR_STRINGS[self.ret_code]
        except:
            return f"Unknown status code: {self.ret_code}"

    __str__ = __repr__


class InvalidNameError(Error):
    """Raised when a mangled name is an invalid
    name under the GNU C++ ABI mangling rules."""

    def __init__(self, mangled_name: Union[str, bytes]) -> None:
        super().__init__()
        self.mangled_name = mangled_name

    def __repr__(self) -> str:
        return f"{self.mangled_name} is an invalid name"

    __str__ = __repr__


def find_any_library(*choices: str) -> str:
    for choice in choices:
        lib = ctypes.util.find_library(choice)
        if lib is not None:
            return lib
    raise LibraryNotFoundError(choices)


class BaseDemangler(abc.ABC):
    @abc.abstractmethod
    def demangleb(self, mangled_name: bytes, external_only: bool = True) -> bytes:
        """Demangles a mangled name. This function is similar to `demangle`
        except it operates with `bytes` objects rather than strings.

        Example:
            Demangle a mangled name:
                >>> import cxxfilt
                >>> cxxfilt.demangleb(b'_ZNSt22condition_variable_anyD2Ev')
                b'std::condition_variable_any::~condition_variable_any()'

            Non-mangled name will be kept intact:
                >>> cxxfilt.demangleb(b'main')
                b'main'

            To demangle an internal symbol, use `external_only=False`:
                >>> cxxfilt.demangleb(b'N3foo12BarExceptionE')
                b'N3foo12BarExceptionE'
                >>> cxxfilt.demangleb(b'N3foo12BarExceptionE', external_only=False)
                b'foo::BarException'

        Args:
            mangled_name (bytes): The name to be demangled.
            external_only (bool, optional): Demangles internal symbols if False.
                Defaults to True.

        Returns:
            bytes: The demangled name or the original name if it is unmangled.

        Raises:
            InternalError: When the libcxx library call fails internally.
            InvalidNameError: When `mangled_name` is an invalid name.
            LibraryNotFoundError: When the libc or libcxx library aren't found.
        """

        raise NotImplementedError

    def demangle(self, mangled_name: str, external_only: bool = True) -> str:
        """Demangles a mangled name. This function is similar to `demangleb`
        except it operates with strings rather than `bytes` objects.

        Example:
            Demangle a mangled name:
                >>> import cxxfilt
                >>> cxxfilt.demangle('_ZNSt22condition_variable_anyD2Ev')
                'std::condition_variable_any::~condition_variable_any()'

            Non-mangled name will be kept intact:
                >>> cxxfilt.demangle('main')
                'main'

            To demangle an internal symbol, use `external_only=False`:
                >>> cxxfilt.demangle('N3foo12BarExceptionE')
                'N3foo12BarExceptionE'
                >>> cxxfilt.demangle('N3foo12BarExceptionE', external_only=False)
                'foo::BarException'

        Args:
            mangled_name (str): The name to be demangled.
            external_only (bool, optional): Demangles internal symbols if False.
                Defaults to True.

        Returns:
            str: The demangled name or the original name if it is unmangled.

        Raises:
            InternalError: When the libcxx library call fails internally.
            InvalidNameError: When `mangled_name` is an invalid name.
            LibraryNotFoundError: When the libc or libcxx library aren't found.
        """
        
        return self.demangleb(mangled_name.encode(), external_only).decode()


class Demangler(BaseDemangler):
    """A demangler which uses specific libc and libcxx libraries under the hood.

    Example:
        >>> from ctypes.util import find_library
        >>> d = cxxfilt.Demangler(find_library('c'), find_library('stdc++'))
        >>> d
        <Demangler libc='libc.so.6' libcxx='libstdc++.so.6'>
        >>> d = cxxfilt.Demangler(find_library('c'), find_library('c++'))
        >>> d
        <Demangler libc='libc.so.6' libcxx='libc++.so.1'>
    """

    def __init__(self, libc_name: str, libcxx_name: str) -> None:
        """Creates a custom Demangler.

        Args:
            libc_name (str): The name/path to the libc library to be used.
            libcxx_name (str): The name/path to the libcxx library to be used.

        Raises:
            AssertionError: If `libc_name` or `libcxx_name` is not a `str`
        """

        assert isinstance(libc_name, str), libc_name
        assert isinstance(libcxx_name, str), libcxx_name

        self._libc_name = libc_name
        libc = ctypes.CDLL(libc_name)
        self._free = libc["free"]
        self._free.argtypes = [ctypes.c_void_p]

        self._libcxx_name = libcxx_name
        libcxx = ctypes.CDLL(libcxx_name)
        self._cxa_demangle = libcxx["__cxa_demangle"]
        self._cxa_demangle.restype = ctypes.c_char_p

    def __repr__(self) -> str:
        cls = self.__class__.__name__
        libc = self._libc_name
        libcxx = self._libcxx_name
        return f"<{cls} libc={libc!r} libcxx={libcxx!r}>"

    def demangleb(self, mangled_name: bytes, external_only: bool = True) -> bytes:
        # Wikipedia: All *external* mangled symbols begin with _Z
        if external_only and not mangled_name.startswith(b"_Z"):
            return mangled_name

        mangled_name_p = ctypes.c_char_p(mangled_name)
        status = ctypes.c_int()
        retval: ctypes.c_char_p = self._cxa_demangle(
            mangled_name_p, None, None, ctypes.pointer(status)
        )

        try:
            demangled = retval.value
        finally:
            self._free(retval)

        ret = status.value
        if ret == 0:
            return demangled
        elif ret == -2:
            raise InvalidNameError(mangled_name)
        else:
            raise InternalError(ret)


class DeferedErrorDemangler(BaseDemangler):
    def __init__(self, error: Exception) -> None:
        self._error = error

    def demangleb(self, *_) -> bytes:
        raise self._error


def _get_default_demangler() -> BaseDemangler:
    try:
        libc = find_any_library("c")
        libcxx = find_any_library("stdc++", "c++")
    except LibraryNotFoundError as error:
        return DeferedErrorDemangler(error=error)
    return Demangler(libc, libcxx)


default_demangler: BaseDemangler = _get_default_demangler()


def demangle(mangled_name: str, external_only: bool = True) -> str:
    """Demangles a mangled name. This function is similar to `demangleb`
    except it operates with strings rather than `bytes` objects.

    Example:
        Demangle a mangled name:
            >>> import cxxfilt
            >>> cxxfilt.demangle('_ZNSt22condition_variable_anyD2Ev')
            'std::condition_variable_any::~condition_variable_any()'

        Non-mangled name will be kept intact:
            >>> cxxfilt.demangle('main')
            'main'

        To demangle an internal symbol, use `external_only=False`:
            >>> cxxfilt.demangle('N3foo12BarExceptionE')
            'N3foo12BarExceptionE'
            >>> cxxfilt.demangle('N3foo12BarExceptionE', external_only=False)
            'foo::BarException'

    Args:
        mangled_name (str): The name to be demangled.
        external_only (bool, optional): Demangles internal symbols if False.
            Defaults to True.

    Returns:
        str: The demangled name or the original name if it is unmangled.

    Raises:
        InternalError: When the libcxx library call fails internally.
        InvalidNameError: When `mangled_name` is an invalid name.
        LibraryNotFoundError: When the libc or libcxx library aren't found.
    """

    return default_demangler.demangle(mangled_name, external_only)


def demangleb(mangled_name: bytes, external_only: bool = True) -> bytes:
    """Demangles a mangled name. This function is similar to `demangle`
    except it operates with `bytes` objects rather than strings.

    Example:
        Demangle a mangled name:
            >>> import cxxfilt
            >>> cxxfilt.demangleb(b'_ZNSt22condition_variable_anyD2Ev')
            b'std::condition_variable_any::~condition_variable_any()'

        Non-mangled name will be kept intact:
            >>> cxxfilt.demangleb(b'main')
            b'main'

        To demangle an internal symbol, use `external_only=False`:
            >>> cxxfilt.demangleb(b'N3foo12BarExceptionE')
            b'N3foo12BarExceptionE'
            >>> cxxfilt.demangleb(b'N3foo12BarExceptionE', external_only=False)
            b'foo::BarException'

    Args:
        mangled_name (bytes): The name to be demangled.
        external_only (bool, optional): Demangles internal symbols if False.
            Defaults to True.

    Returns:
        bytes: The demangled name or the original name if it is unmangled.

    Raises:
        InternalError: When the libcxx library call fails internally.
        InvalidNameError: When `mangled_name` is an invalid name.
        LibraryNotFoundError: When the libc or libcxx library aren't found.
    """

    return default_demangler.demangleb(mangled_name, external_only)
