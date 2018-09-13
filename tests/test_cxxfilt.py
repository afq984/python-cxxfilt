from __future__ import unicode_literals
import unittest
import cxxfilt


class TestCase(unittest.TestCase):

    def test_not_mangled_name(self):
        self.assertEqual(cxxfilt.demangle('main'), 'main')

    def test_not_mangled_nameb(self):
        self.assertEqual(cxxfilt.demangleb(b'main'), b'main')

    def test_reject_invalid_name(self):
        with self.assertRaises(cxxfilt.InvalidName):
            cxxfilt.demangle('_ZQQ')

    def test_reject_invalid_nameb(self):
        with self.assertRaises(cxxfilt.InvalidName):
            cxxfilt.demangleb(b'_ZQQ')

    def test_demangle(self):
        self.assertIn(
            cxxfilt.demangle('_ZNSt22condition_variable_anyD2Ev'),
            {
                'std::condition_variable_any::~condition_variable_any()',
                'std::condition_variable_any::~condition_variable_any(void)',
            }
        )

    def test_demangleb(self):
        self.assertIn(
            cxxfilt.demangleb(b'_ZNSt22condition_variable_anyD2Ev'),
            {
                b'std::condition_variable_any::~condition_variable_any()',
                b'std::condition_variable_any::~condition_variable_any(void)',
            }
        )

    def test_issue_1(self):
        # https://github.com/afg984/python-cxxfilt/issues/1
        self.assertEqual(
            cxxfilt.demangle('N3foo12BarExceptionE', external_only=False),
            'foo::BarException'
        )
        self.assertEqual(
            cxxfilt.demangleb(b'N3foo12BarExceptionE', external_only=False),
            b'foo::BarException'
        )

        self.assertEqual(
            cxxfilt.demangle('Z4mainEUlvE_', external_only=False),
            'main::{lambda()#1}'
        )
        self.assertEqual(
            cxxfilt.demangleb(b'Z4mainEUlvE_', external_only=False),
            b'main::{lambda()#1}'
        )

        self.assertEqual(
            cxxfilt.demangle('a', external_only=False),
            'signed char'
        )
        self.assertEqual(
            cxxfilt.demangleb(b'a', external_only=False),
            b'signed char'
        )

    def test_gcc_cp_mangle(self):
        # examples from gcc: gcc/cp/mangle.c
        self.assertEqual(
            cxxfilt.demangle('St13bad_exception', external_only=False),
            'std::bad_exception'
        )
        self.assertEqual(
            cxxfilt.demangle('_ZN4_VTVISt13bad_exceptionE12__vtable_mapE'),
            '_VTV<std::bad_exception>::__vtable_map'
        )
