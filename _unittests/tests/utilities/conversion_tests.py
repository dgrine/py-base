################################################################################
# base._unittests.tests.utilities.conversion
#
# Copyright 2017. Djamel Grine.
#
# Redistribution and use in source and binary forms, with or without 
# modification, are permitted provided that the following conditions are met:
# 
# 1. Redistributions of source code must retain the above copyright notice, 
#    this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice, 
#    this list of conditions and the following disclaimer in the documentation 
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" 
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE 
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE 
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE 
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR 
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF 
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS 
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN 
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) 
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE 
# POSSIBILITY OF SUCH DAMAGE.
################################################################################
from base.utilities.conversion import guess_convert
from testing import TestCase, LogCapture
from datetime import datetime

def is_ok(lhs, rhs):
    return (lhs == rhs) and (type(lhs) == type(rhs))

class Test_Conversion(TestCase):
    def test_int(self):
        self.assertEqual(True, is_ok(2, guess_convert("2")))
        self.assertEqual(False, is_ok(2.0, guess_convert("2")))

    def test_float(self):
        self.assertEqual(True, is_ok(2.1, guess_convert("2.1")))
        self.assertEqual(False, is_ok(2, guess_convert("2.1")))

    def test_date(self):
        string = "2016-10-26"
        self.assertEqual(True, is_ok(datetime.strptime(string, "%Y-%m-%d"), guess_convert(string)))
        string = "89899-10989-01200"
        self.assertEqual(True, is_ok(string, guess_convert(string)))

    def test_boolean(self):
        self.assertEqual(True, is_ok(True, guess_convert("True")))
        self.assertEqual(True, is_ok(True, guess_convert("true")))
        self.assertEqual(True, is_ok(True, guess_convert("TRUE")))
        self.assertEqual(True, is_ok(True, guess_convert("tRuE")))
        self.assertEqual(True, is_ok(False, guess_convert("False")))
        self.assertEqual(True, is_ok(False, guess_convert("false")))
        self.assertEqual(True, is_ok(False, guess_convert("FALSE")))
        self.assertEqual(True, is_ok(False, guess_convert("fAlSe")))

    def test_string(self):
        string = "Sample string"
        self.assertEqual(True, is_ok(string, guess_convert(string)))
