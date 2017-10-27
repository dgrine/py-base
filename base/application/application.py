################################################################################
# base.application.application
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
from base.application.settings import Settings
from base.application.mixins import arg, ArgumentsMixin
from base.utilities.misc import current_timestamp
from multiprocessing import cpu_count
import datetime
import dateutil.relativedelta

log = get_logger()

class Application(ArgumentsMixin(prog = 'app')):
    """
    Base class for all applications. This class serves as a blueprint for
    concrete applications. It provides only the most basic functionality:
    - handling of command line arguments
    - handling of application settings
    """

    @classmethod
    def arg(cls, *args, **kwargs):
        """
        Convenience class method forwarding call to 'arg' function.
        """
        return arg(*args, **kwargs)

    def __init__(self, settings = None, settings_defaults = None):
        """
        Initializes the application basic functionality.

        :param settings:
            Either a Settings object or the configuration file.
        :param settings_defaults:
            A dictionary of key-value pairs to be used when reading the
            given configuration file.
        """
        # Settings
        log.noise("Configuring application settings...")
        settings_defaults = settings_defaults if not settings_defaults is None else {}
        if settings is None:
            self.settings = Settings()

        elif type(settings) in (str, unicode, list):
            self.settings = Settings(
                config_file = settings,
                defaults = settings_defaults
               )
        elif Settings == type(settings):
            self.settings = settings if not settings is None else Settings(
            defaults = settings_defaults
           )

        assert hasattr(self, 'settings'), "'settings' attribute not set"
        super(Application, self).__init__()

    def _print_unified_settings(self):
        """
        Debug function that prints the unified settings of the application.
        """
        # Log the unified settings
        _log_msg = ""
        for section in self._settings:
            _log_msg += "[%s]\n" % section
            for option in self._settings[ section ]:
                value = self._settings[ section ][ option ]
                _log_msg += "%s=%s\n" % (option, value)
            _log_msg += "\n"
        log.dump("Application configuration:\n%s", _log_msg)

    def post_init(self):
        """
        Triggers the callbacks decorated with the 'post_init' decorator.
        """
        post_init_functions = [
            getattr(self, fnc_name) for fnc_name in dir(self) \
            if hasattr(getattr(self, fnc_name), '__post_init_function__') \
            and \
            True == getattr(self, fnc_name).__post_init_function__
            ]
        log.noise("Performing application post-initialization...")
        for init_func in post_init_functions:
            log.noise("-> post-init function: '%s'", init_func.__name__)
            init_func()
        log.noise("Finished application post-initialization.")

    def run(self):
        """
        This method must be implemented by concrete classes.
        """
        raise NotImplementedError(
            "Class '%s' missing 'run' method" % self.__class__.__name__
           )

class PipelineApplication(Application):
    """
    Pipeline application that runs a set of components.
    """

    process_count = arg(
        '-j',
        type = int,
        default = cpu_count()
       )

    class Context(object):
        @classmethod
        def create(cls, app):
            context = cls()
            context.timestamp = current_timestamp()
            context.process_count = app.process_count
            return context

    def run(self):
        assert hasattr(self, 'pipeline'), "No 'pipeline' list attribute set"

        # Set up the context
        context = self.Context.create(self)

        # Run the pipeline
        log.debug("Starting pipeline...")
        for component in self.pipeline:
            ts_start = None
            try:
                if component.can_run(context):
                    log.info("Running component '%s'...", component.name)
                    ts_start = datetime.datetime.now()
                    component.run(context)
                else:
                    log.warning("Skipping component '%s'...", component.name)

            except Exception as error:
                log.exception(error)
                log.error("Component '%s' failed. Stopping execution.", component.name)
                exit(1)
            
            finally:
                if ts_start:
                    ts_diff = dateutil.relativedelta.relativedelta(
                        datetime.datetime.now(),
                        ts_start
                       )
                    log.info(
                        "Elapsed time: %s hours, %s minutes and %s seconds",
                        ts_diff.hours,
                        ts_diff.minutes,
                        ts_diff.seconds
                       )

        log.info("Finished pipeline. Done.")
        
