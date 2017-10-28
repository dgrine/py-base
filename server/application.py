################################################################################
# base.server.application
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
from base.application.log import get_logger
from base.application.application import Application
from base.application.settings import Settings, to_bool, to_int
from base.utilities import Texttable
from base.server.mixins.backends import FlaskMixin
from base.py.modules import get_caller_module

log = get_logger()

class ServerApplication(Application, FlaskMixin):
    def __init__(self, name = None, settings = None, settings_defaults = None):
        """
        Initializes the server application.

        :param name:
            Name to be given to the Flask server.
        :param settings:
            Either a Settings object or the configuration file.
        :param settings_defaults:
            A dictionary of key-value pairs to be used when reading the
            given configuration file.
        """
        self._name = name if name is not None else get_caller_module().__name__

        # Continue initializing the application
        super(ServerApplication, self).__init__(settings, settings_defaults)

    @property
    def rules(self):
        return self.server.url_map.iter_rules()

    def run(self):
        """
        Runs the server and blocks until it's done.
        """

        assert hasattr(self, 'server'), \
            "ServerApplication does not have a server"

        # Display endpoints
        _excluded_methods = set(['OPTIONS', 'HEAD'])
        rows = [
            [rule.rule, ", ".join(rule.methods - _excluded_methods), rule.endpoint]
            for rule in self.rules
           ]
        rows.sort(key = lambda x: x[0])
        rows.insert(0, ['URL', 'METHOD', 'ENDPOINT'])
        table = Texttable(max_width = 120)
        table.add_rows(rows)
        log.debug("%d endpoints in server:\n%s",len(rows), table.draw())

        # Run the server
        log.info("Running server...")
        self.server.run(
            host  = self.settings.server.host,
            port  = self.settings(convert = to_int).server.port,
            debug = False # self.settings(convert = to_bool).server.debug
           )

