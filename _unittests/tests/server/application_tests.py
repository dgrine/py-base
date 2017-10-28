################################################################################
# base._unittests.tests.server.application_tests
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
from testing import TestCase
from base.server.application import ServerApplication
from base.application.mixins import LoggingMixin
from base.application.settings import Settings
from base.application.log import get_logger
import os

class Test_WebServer(TestCase):
    def setUp(self):
        self._remove_log_files()

    def tearDown(self):
        self.test_client = None
        self._remove_log_files()

    def _remove_log_files(self):
        for log_file in [os.path.join(self.data_path, f) for f in os.listdir(self.data_path) if f.endswith('.log')]:
            os.remove(log_file)

    def test_webserver_crud(self):
        class _WebApp(ServerApplication): pass
        app = _WebApp()

        @app.server.route('/test_get', methods = ['GET'])
        def test_get():
            return "CRUD-GET"

        @app.server.route('/test_post', methods = ['POST'])
        def test_post():
            return "CRUD-POST"

        # Create the test client
        self.test_client = app.server.test_client()

        # GET
        response = self.test_client.get('/test_get')
        self.assertEqual(('200 OK', "CRUD-GET"), (response.status, response.data)) 

        # POST
        response = self.test_client.post('/test_post')
        self.assertEqual(('200 OK', "CRUD-POST"), (response.status, response.data))

    def test_webserver_logging_mixin(self):
        class _WebApp(ServerApplication, LoggingMixin):
            def __init__(this):
                _settings = Settings()
                _settings.logging.path = self.data_path
                
                super(_WebApp, this).__init__(
                    settings = _settings
                   )
        app = _WebApp()
        log = get_logger()

        @app.server.route('/test_get', methods = ['GET'])
        def test_get():
            log.info("test_get")
            return 'CRUD-GET'

        # Create the test client
        self.test_client = app.server.test_client()
        
        _log_file = os.path.join(app.settings.logging.path, app.settings.logging.filename_all)

        # GET
        response = self.test_client.get('/test_get')
        with open(_log_file, 'r') as f:
            content = f.readlines()
        self.assertTrue(9 == len(content), content)
        
