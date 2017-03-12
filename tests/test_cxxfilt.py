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
