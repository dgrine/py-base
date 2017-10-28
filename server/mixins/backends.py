################################################################################
# base.server.mixins.log
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
from base.application.mixin import ApplicationMixin
from base.application.mixins import ArgumentsMixin, arg
from base.application.settings import to_bool, to_int
from base.utilities.misc import generate_key
import flask
import werkzeug
import os
from werkzeug.contrib.profiler import ProfilerMiddleware

log = get_logger()

class FlaskMixin( ApplicationMixin ):
    """
    Server application mixin that provides a Flask WSGI back-end.
    """

    host = arg(
        '--host',
        type = str,
        help = 'host on which to run the web server'
        )
    port = arg(
        '--port',
        type = int,
        help = 'port on which to run the web server',
        )
    debug = arg(
        '--debug',
        action = 'store_true',
        help = 'enables interactive debugging (WARNING: security risk!)'
        )

    def __init__( self ):
        super( FlaskMixin, self ).__init__()

        log.noise(
            "Server is using Flask version %s and Werkzeug version %s",
            flask.__version__,
            werkzeug.__version__
            )
        self.server = flask.Flask( self._name )
        self._configure_flask_mixin()       

    def _configure_flask_mixin( self ):
        # Fill in the default configuration
            # Basic server information
        self.settings.server.host = self.settings.server.host if 'host' in self.settings.server else 'localhost'
        self.settings.server.port = self.settings.server.port if 'port' in self.settings.server else '5000'
        self.settings.server.debug = self.settings.server.debug if 'debug' in self.settings.server else 'true'
        
            # Other Flask configurations
        self.settings.server.allowed_extensions = self.settings.server.allowed_extensions if 'allowed_extensions' in self.settings.server else [ 'png', 'jpg', 'jpeg', 'gif' ]
        self.settings.server.csrf_enabled = self.settings.server.csrf_enabled if 'csrf_enabled' in self.settings.server else True
        self.settings.server.max_content_length = self.settings.server.max_content_length if 'max_content_length' in self.settings.server else '20971520'
        self.settings.server.secret_key = self.settings.server.secret_key if 'secret_key' in self.settings.server else generate_key()
        self.settings.server.static_path = os.path.join( self.server.root_path, self.settings.server.static_path if 'static_path' in self.settings.server else 'static' )
        self.settings.server.templates_path = os.path.join( self.server.root_path, self.settings.server.templates_path if 'templates_path' in self.settings.server else 'templates' )
        self.settings.server.upload_path = os.path.join( self.server.root_path, self.settings.server.upload_path if 'upload_path' in self.settings.server else 'static/upload' )

            # Custom server settings
        self.settings.server.profile = self.settings.server.profile if 'profile' in self.settings.server else 'false'

        # Command line overwrites
        if self.host: self.settings.server.host = self.host
        if self.port: self.settings.server.port = self.port
        if self.debug: self.settings.server.debug = self.debug

        # Emit warnings
        if self.settings( convert = to_bool ).server.debug:
            log.warning(
                "\n\n" + \
                "=" * 80 + \
                "\n= SECURITY RISK: running in debug mode." + \
                " Do NOT run this server in production.  =\n" + \
                "=" * 80 + \
                "\n"
                )

        # Configure Flask application
        class _internal_configuration( object ):
            ALLOWED_EXTENSIONS = set( self.settings.server.allowed_extensions )
            CSRF_ENABLED = self.settings( convert = to_bool ).server.csrf_enabled
            MAX_CONTENT_LENGTH = self.settings( convert = to_int ).server.max_content_length
            PROFILE = self.settings( convert = to_bool ).server.profile
            SECRET_KEY = self.settings.server.secret_key
            STATIC_FOLDER = self.settings.server.static_path
            TEMPLATES_FOLDER = self.settings.server.templates_path
            UPLOAD_FOLDER = self.settings.server.upload_path
        self.server.config.from_object( _internal_configuration() )
        if self.settings( convert = to_bool ).server.profile:
            self.server.wsgi_app = ProfilerMiddleware(
            self.server.wsgi_app,
            restrictions = [ 30 ]
            )
