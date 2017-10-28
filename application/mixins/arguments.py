################################################################################
# base.application.arguments
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
import sys
import argparse
import os

class _ArgumentsMixinMeta(type):
    def __call__(cls, *args, **kwargs):
        if ArgumentsMixin == cls:
            class ArgumentsMixinWithParserArgs(cls):
                _parser_args = args
                _parser_kwargs = kwargs
            return ArgumentsMixinWithParserArgs
        else:
            return super(_ArgumentsMixinMeta, cls).__call__(*args, **kwargs)

class ArgumentsMixin(object):
    """
    Application mixin that adds argument parsing.
    """
    __metaclass__ = _ArgumentsMixinMeta

    def __init__(self, *args, **kwargs):
        if not hasattr(self.__class__, '_argv'):
            ArgumentsMixin._argv = sys.argv[1:]

        # Find all argument proxies
        arg_names = [name for name in dir(self) if hasattr(self, name) and ArgumentProxy == type(getattr(self, name))]
        lookup_names = []

        # Create the argument parser
        parser_args = self.__class__._parser_args if hasattr(self.__class__, '_parser_args') else ()
        parser_kwargs = self.__class__._parser_kwargs if hasattr(self.__class__, '_parser_kwargs') else {}
        parser = argparse.ArgumentParser(*parser_args, **parser_kwargs)
        for name in arg_names:
            proxy = getattr(self, name)
            if not len(proxy.args):
                parser.add_argument(*(name,), **proxy.kwargs)
                lookup_names.append(name)
            elif '-' != proxy.args[0][0]:
                parser.add_argument(*proxy.args, **proxy.kwargs)
                lookup_names.append(proxy.args[0])
            else:
                parser.add_argument(*proxy.args, dest = name, **proxy.kwargs)
                lookup_names.append(name)

        # Parse the arguments
        parsed_args, leftover = parser.parse_known_args(ArgumentsMixin._argv)

        # Set the parsed arguments on the object
        for arg_name, lookup_name in zip(arg_names, lookup_names):
            prop = getattr(parsed_args, lookup_name)
            setattr(self, arg_name, prop)

        # Adapt sys.argv
        ArgumentsMixin._argv = leftover
        
        # Continue base class initialization
        super(ArgumentsMixin, self).__init__()

class ArgumentProxy(object):
    def __init__(self, *args, **kwargs):
        super(ArgumentProxy, self).__init__()
        self.args   = args
        self.kwargs = kwargs

def arg(*args, **kwargs):
    """
    Marks a class attribute as an argument by returning an ArgumentProxy
    object that will be used during the argument parsing. All parameters
    are forwarded to the 'add_argument' call of the argparse module.
    """
    return ArgumentProxy(*args, **kwargs)
