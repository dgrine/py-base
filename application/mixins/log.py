################################################################################
# base.application.mixins.log
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
from base.application.log import initialize_logging, get_logger
from base.application.mixin import ApplicationMixin
import os

log = get_logger()

class LoggingMixin( ApplicationMixin ):
    """
    Application mixin that adds file logging.
    """

    def __init__( self ):
        """
        Initializes the mixin.
        """
        super( LoggingMixin, self ).__init__()

        self._configure_logging()

    def _get_logger_descriptions( self, log_level, log_file_all, log_file_err ):
        return [
            {
                'handler_type': 'FileHandler',
                'level': log_level,
                'handler_kwargs':
                {
                    'filename': log_file_all,
                }
            },
            {
                'handler_type': 'FileHandler',
                'level': 'warning',
                'handler_kwargs':
                {
                    'filename': log_file_err,
                }
            }
        ]

    def _configure_logging( self ):
        """
        Configures the file logging by reading the corresponding logging section
        in the settings. Logging will be done to two files:
        - logging.filename_all: contains the full log.
        - logging.filename_err: contains only error logging.
        """
        # Read configuration
        if not 'logging' in self.settings:
            raise RuntimeError( "No 'logging' configuration" )
        if not 'path' in self.settings.logging:
            raise RuntimeError( "No 'path' setting in 'logging' configuration" )
        log_path = self.settings.logging.path
        log_file_all = os.path.join( log_path, self.settings( default = 'all.log' ).logging.filename_all )
        log_file_err = os.path.join( log_path, self.settings( default = 'err.log' ).logging.filename_error )
        log_level = self.settings( default = 'DUMP' ).logging.level
        
        # List of logger descriptions
        logger_descriptions = self._get_logger_descriptions(
            log_level,
            log_file_all,
            log_file_err
            )
    
        # Initialize the logging
        log.debug( "Setting up file logging to '%s'...", log_path )
        initialize_logging( logger_descriptions, name = '__root__' )
        log.debug( "File logging active." )
