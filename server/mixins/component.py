################################################################################
# base.server.mixins.component
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
from base.application.mixins import arg
from base.application.settings import to_list
from base.application.mixin import ApplicationMixin
from base.server.compmgt import ComponentManager

log = get_logger()

class ConfigurationError(Exception): pass

class ComponentMixin(ApplicationMixin):
    """
    Server application mixin that adds componentization.
    """

    includes = arg(
        '--include',
        nargs = '+',
        help = 'components to include'
       )
    excludes = arg(
        '--exclude',
        nargs = '+',
        help = 'components to exclude'
       )

    def __init__(self):
        super(ComponentMixin, self).__init__()
        self._configure_component_mixin()

    def _configure_component_mixin(self):
        self._component_manager = ComponentManager(self.settings.components.path)

        if self.includes:
            self.settings.components.includes = ':'.join(self.includes)
        if self.excludes:
            self.settings.components.excludes = ':'.join(self.excludes)
            
        # Sanity checks on the settings
        log.debug("Checking for inconsistencies in the component settings...")
        log.noise("-> Checking component selection...")
        if 'includes' in self.settings.components and 'excludes' in self.settings.components:
            raise ConfigurationError("Invalid setting: 'includes' and 'excludes' options are mutually exclusive settings. Pick one.")

    @ApplicationMixin.post_init
    def load_components(self):
        log.debug("Preparing to load server components...")

        includes = self.settings(convert = to_list).components.includes if 'includes' in self.settings.components else None
        excludes = self.settings(convert = to_list).components.excludes if 'excludes' in self.settings.components else None

        # Load the server components
        self._component_manager.load(self, includes, excludes)
