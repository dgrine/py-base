################################################################################
# base.py.modules
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
import os
import sys
import inspect
import types
import importlib

def get_caller(frame = 1):
    """
    Finds the caller that calls the function invoking this function, 
    i.e. it can be used to find which method calls you.

    :param frame:   The number of frames to trace back, with frame 1 being the
                    immediate caller.
    :returns:       The frame that called the current frame.
    """
    assert type(frame) is int, "Expected integer type, got %s" % type(frame)

    # Grab the stack leading upto
    callers = inspect.stack()  

    assert frame < len(callers) - 1
                                           # this method
    caller = callers[frame + 1]            # The caller's frame info
    return caller

def get_caller_module(frame = 1):
    """
    Finds the module that contains the function that calls the function
    invoking this function, i.e. it can be used to find which module
    calls you.

    :param frame:   The number of frames to trace back, with frame 1 being the
                    immediate caller.
    :returns:       The module that called the current frame.
    """
    assert type(frame) is int

    callers     = inspect.stack()               # Grab the stack leading upto 

    assert frame < len(callers) - 1
                                           # this method
    caller = callers[frame + 1]            # The caller's frame info
    module = inspect.getmodule(caller[0])  # The caller's module 
                                           # (caller[0] is the frame)
    return module

def this_module_path(frame = 1):
    """
    Finds out the path of this module, independently of where it is being run
    from.

    :returns:   The absolute path of this module.
    """
    return os.path.realpath(
                os.path.abspath(
                    os.path.split(
                        inspect.getfile(
                            get_caller_module(frame)
                       )
                   )[0]
               )
           )

def this_module_path_relative(*args):
    """
    Returns the fully resolved path relative to the calling module's
    path.
    """
    return os.path.realpath(
        os.path.abspath(
            os.path.join(
                this_module_path(frame = 2),
                 *args if len(args) else '.'
                )
           )
       )

def get_module_name_from_path(root_path, path):
    """
    Generates the module name from a path, starting from a given
    root path.
    """
    assert type(root_path) in (str, unicode), "Expected string type"
    assert type(path) in (str, unicode), "Expected string type"
    assert root_path in path, "First argument '%s' must be 'in' second argument '%s':" % (root_path, path)
    module_name = path[len(root_path):].replace('.py', '').replace(os.sep, '.')
    if module_name.startswith('.'): module_name = module_name[1:]
    return module_name

def load_module(module_name):
    """
    Loads a given module using the Python fully qualified module name.
    """
    assert type(module_name) in (str, unicode), "Expected string type"
    module = importlib.import_module(module_name)
    return module

def find_classes_in_module(module, filter = lambda name, value: True):
    """
    Finds the classes in the given module for which filter returns True.
    """
    assert isinstance(module, types.ModuleType), "Expected module type"

    return [value for name, value in inspect.getmembers(module) if inspect.isclass(value) and filter(name, value)]

def is_path_module(path, executable = False):
    """
    Returns whether a given path is a valid Python module.

    :param executable:
        Indicates whether to check if the Python module is runnable.
    """
    resolved_path = os.path.realpath(os.path.abspath(path))
    is_folder = os.path.isdir(resolved_path)
    has_init_py = os.path.isfile(os.path.join(resolved_path, '__init__.py'))
    is_executable = os.path.isfile(os.path.join(resolved_path, '__main__.py'))
    return is_folder and has_init_py and is_executable if executable else is_folder and has_init_py
        
