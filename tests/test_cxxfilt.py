from __future__ import unicode_literals

import pytest

import cxxfilt


def test_not_mangled_name():
    assert cxxfilt.demangle('main') == 'main'


def test_not_mangled_nameb():
    assert cxxfilt.demangleb(b'main') == b'main'


def test_reject_invalid_name():
    with pytest.raises(cxxfilt.InvalidName):
        cxxfilt.demangle('_ZQQ')


def test_reject_invalid_nameb():
    with pytest.raises(cxxfilt.InvalidName):
        cxxfilt.demangleb(b'_ZQQ')


def test_demangle():
    if not cxxfilt.default_demangler.is_demangling_through_cxa():
        assert cxxfilt.demangle('??1_Sentry_base@?$basic_ostream@DU?$char_traits@D@std@@@std@@QAE@XZ', False) in {
            'std::basic_ostream<char,struct std::char_traits<char> >::_Sentry_base::~_Sentry_base(void)'
        }
        return

    assert cxxfilt.demangle('_ZNSt22condition_variable_anyD2Ev') in {
        'std::condition_variable_any::~condition_variable_any()',
        'std::condition_variable_any::~condition_variable_any(void)',
    }


def test_demangleb():
    if not cxxfilt.default_demangler.is_demangling_through_cxa():
        assert cxxfilt.demangleb(b'??1_Sentry_base@?$basic_ostream@DU?$char_traits@D@std@@@std@@QAE@XZ', False) in {
            b'std::basic_ostream<char,struct std::char_traits<char> >::_Sentry_base::~_Sentry_base(void)'
        }
        return

    assert cxxfilt.demangleb(b'_ZNSt22condition_variable_anyD2Ev') in {
        b'std::condition_variable_any::~condition_variable_any()',
        b'std::condition_variable_any::~condition_variable_any(void)',
    }


@pytest.mark.parametrize(
    ['input', 'external_only', 'valid_outputs'],
    [
        # https://github.com/afg984/python-cxxfilt/issues/1
        ('N3foo12BarExceptionE', False, ['foo::BarException']),
        ('Z4mainEUlvE_', False, ['main::{lambda()#1}', "main::'lambda'()"]),
        ('a', False, ['signed char']),
        # examples from gcc: gcc/cp/mangle.c
        ('St13bad_exception', False, ['std::bad_exception']),
        (
            '_ZN4_VTVISt13bad_exceptionE12__vtable_mapE',
            True,
            ['_VTV<std::bad_exception>::__vtable_map'],
        ),
    ],
)
def test_demangle_parametrize(input, external_only, valid_outputs):
    if not cxxfilt.default_demangler.is_demangling_through_cxa():
        return  # fixme: write tests for dbghelp demangler
    assert cxxfilt.demangle(input, external_only=external_only) in valid_outputs


def test_default_demangler():
    assert isinstance(cxxfilt.default_demangler, cxxfilt.Demangler)

    repr(cxxfilt.default_demangler)


def test_ErrorDemangler():
    demangler = cxxfilt.DeferedErrorDemangler(cxxfilt.LibraryNotFound())

    with pytest.raises(cxxfilt.LibraryNotFound):
        demangler.demangle('aa')

    with pytest.raises(cxxfilt.LibraryNotFound):
        demangler.demangle('aa', external_only=False)

    with pytest.raises(cxxfilt.LibraryNotFound):
        demangler.demangleb(b'aa')

    with pytest.raises(cxxfilt.LibraryNotFound):
        demangler.demangleb(b'aa', external_only=False)
