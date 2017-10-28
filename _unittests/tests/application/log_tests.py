################################################################################
# base._unittests.tests.application.log_tests
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
from testing import TestCase, LogCapture
from base.application.log import initialize_logging, get_logger
import os

class Test_Logging(TestCase):
    def setUp(self):
        for file in [ \
            os.path.join(self.data_path, filename) \
            for filename in os.listdir(self.data_path) \
            if filename.endswith('.log') \
            ]:
            os.remove(file)

    def test_console_logger_all_levels(self):
        logger_description = {
            'handler_type': 'StreamHandler',
        }
        with LogCapture() as captured_log:
            initialize_logging(logger_description)
            log = get_logger()

            lines = [
                ('CRITICAL', 'Critical message'),
                ('ERROR',    'Error message'),
                ('WARNING',  'Warning message'),
                ('INFO',     'Information message'),
                ('DEBUG',    'Debug message'),
                ('NOISE',    'Noise message'),
                ('DUMP',     'Dump mesage'),
                ]
            for level, line in lines:
                getattr(log, level.lower())(line)

        ref = [ ('__root__',) + item for item in lines ]
        captured_log.check(*ref)

    def test_file_logger_all_levels(self):
        logfile = os.path.join(self.data_path, 'test.log')
        logger_description = \
        {
            'handler_type': 'FileHandler',
            'handler_kwargs':
            {
                'filename': logfile,
            },
            'format': '+%(levelname)s: %(message)s'
        }
        initialize_logging(logger_description, 'my_filelog')
        log = get_logger('my_filelog')

        lines = [
            ('CRITICAL', 'Critical message'),
            ('ERROR',    'Error message'),
            ('WARNING',  'Warning message'),
            ('INFO',     'Information message'),
            ('DEBUG',    'Debug message'),
            ('NOISE',    'Noise message'),
            ('DUMP',     'Dump mesage'),
            ]
        for level, line in lines:
            getattr(log, level.lower())(line)

        with open(logfile, 'r') as f:
            actual_lines = f.readlines()
        ref_lines = [ "+%s: %s\n" % item for item in lines ]

        self.assertEqual(ref_lines, actual_lines)

    def test_named_loggers(self):
        ref_log_a = None
        with LogCapture() as captured_log_a:
            initialize_logging(name = 'logger_a')
            log = get_logger(name = 'logger_a')
            lines = [
                ('INFO',     'Information message for logger_a'),
                ]
            for level, line in lines:
                getattr(log, level.lower())(line)
            ref_log_a = [ (log.name,) + item for item in lines ]

        ref_log_b = None
        with LogCapture() as captured_log_b:
            initialize_logging(name = 'logger_b')
            log = get_logger(name = 'logger_b')
            lines = [
                ('INFO',     'Information message for logger_b'),
                ]
            for level, line in lines:
                getattr(log, level.lower())(line)
            ref_log_b = [ (log.name,) + item for item in lines ]

        captured_log_a.check(*ref_log_a)
        captured_log_b.check(*ref_log_b)
