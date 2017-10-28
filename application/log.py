################################################################################
# base.application.log
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
from base.py.modules import get_caller_module
import logging

# Add some additional logging levels
NOISE = logging.DEBUG - 1
DUMP  = logging.DEBUG - 2
_LEVEL_NAMES = {
    logging.getLevelName(logging.DEBUG)    : logging.DEBUG,
    logging.getLevelName(logging.INFO)     : logging.INFO,
    logging.getLevelName(logging.WARNING)  : logging.WARNING,
    logging.getLevelName(logging.ERROR)    : logging.ERROR, 
    logging.getLevelName(logging.CRITICAL) : logging.CRITICAL,
    'NOISE' : NOISE, 
    'DUMP'  : DUMP, 
}
logging.addLevelName(NOISE, 'NOISE')
logging.addLevelName(DUMP,  'DUMP' )

class _ApplicationLogger(logging.getLoggerClass()):
    """
    This is the logger presented to the application. It adds
    support for additional log levels.
    """

    def noise(self, *args, **kwargs):
        return self.log(NOISE, *args, **kwargs)

    def dump(self, *args, **kwargs):
        return self.log(DUMP, *args, **kwargs)

# This is the logger class to use when a new logger is created
logging.setLoggerClass(_ApplicationLogger)

# The default logger name
# This logger has support for the additional logging levels and
# can be used by all modules with a simple get_logger() call.
DEFAULT_LOGGER_NAME = '__root__'

def _get_default_format(handler_type):
    if 'StreamHandler' == handler_type:
        return '%(levelname)s: %(message)s'
    else:
        return '%(levelname)s - %(asctime)s - [ %(pathname)s:%(lineno)s ]: %(message)s'

def _get_default_logger_descriptions():
    stream_logger_description = {
        'handler_type': 'StreamHandler',
        'format': '%(message)s'
    }
    return [stream_logger_description]

def initialize_logging(logger_descriptions = None, name = None):
    """
    Initializes the logging system for the logger with the given
    name.
    """
    name = name if None != name else DEFAULT_LOGGER_NAME

    # Configure the logger
    logger = logging.getLogger(name)
    logger.setLevel(DUMP) # Should always be set to the lowest level

    # Remove all handlers
    logger.handlers = []

    # Some sanity checks
    if list == type(logger_descriptions):
        pass
    elif dict == type(logger_descriptions):
        logger_descriptions = [ logger_descriptions ]
    elif None == logger_descriptions:
        logger_descriptions = _get_default_logger_descriptions()
    else:
        assert False, "Unsupported type '%s'" % type(logger_descriptions)
     
    # Set up the loggers
    for logger_description in logger_descriptions:
        assert dict == type(logger_description), "Expected dict type"
        assert 'handler_type' in logger_description
        assert hasattr(logging, logger_description[ 'handler_type' ]), \
            "Unknown logging handler '%s'" % logger_description[ 'handler_type' ]
        _level = \
            logger_description[ 'level' ].upper() \
                if 'level' in logger_description \
                else \
            'DUMP'
        _handler_kwargs = \
            logger_description[ 'handler_kwargs' ] \
                if 'handler_kwargs' in logger_description \
                else \
            {}
        _format = \
            logger_description[ 'format' ] \
                if 'format' in logger_description \
                else \
            _get_default_format(logger_description[ 'handler_type' ])
        _date_format = \
            logger_description[ 'date_format' ] \
                if 'date_format' in logger_description \
                else \
            '%Y-%m-%d %H:%M:%s'

        # Set up the handler
        handler = getattr(logging, logger_description[ 'handler_type' ])(**_handler_kwargs)
        handler.setLevel(_LEVEL_NAMES[ _level ])

        # Set up the handler's formatter
        formatter = logging.Formatter(_format)
        handler.setFormatter(formatter)

        # Add the handler to the logger
        logger.addHandler(handler)

def get_logger(name = None):
    """
    Returns a named logger. If no name is specified, a default logger
    is returned instead.
    """
    name = name if None != name else DEFAULT_LOGGER_NAME
    return logging.getLogger(name)
