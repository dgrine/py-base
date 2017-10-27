################################################################################
# base.server.blueprint
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
from base.py.modules import get_caller_module
from flask import Blueprint

log = get_logger()

class ServerBlueprint(Blueprint):
    @property
    def views(self):
        raise NotImplementedError()

    def __init__(
        self,
        app,
        name,
        module_name = None,
        template_folder = 'templates',
        static_folder = 'static',
        *args,
        **kwargs
       ):      
        super(ServerBlueprint, self).__init__(
            name,
            module_name if module_name else get_caller_module().__name__,
            template_folder = template_folder,
            static_folder = static_folder,
            *args,
            **kwargs
           )

    def finalize(self, app):
        """
        Hook method that gets called after all the views for this blueprint
        have been registered.
        """
        pass
