################################################################################
# base.server.view
# Author: Djamel Grine.
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
from base.py.objects import is_iterable
from base.py.modules import this_module_path_relative
from base.application.settings import Settings
from flask import request, Response
from flask.ext.classy import FlaskView, route as flaskclassy_route
from functools import wraps
import json

log = get_logger()

def find_arg_holder(func):
    """
    Finds the argument holder in a function.
    """
    arg_holder = None
    f = func
    while arg_holder is None:
        if not hasattr(f, '__wrapped_function__'):
            if not hasattr(f, '__arg_holder__'):
                class Args(object):
                    def __repr__(self):
                        d = dict(self.__dict__)
                        for item in self.__dict__:
                            if item.startswith('_'): del d[item]
                        return repr(d)
                setattr(f, '__arg_holder__', Args())
            arg_holder = getattr(f, '__arg_holder__')
        else:
            f = getattr(f, '__wrapped_function__')
    return arg_holder

def _enable_arg_holder(wrapped_func, func):
    setattr(wrapped_func, '__wrapped_function__', func)

class View(object):
    """
    Base class for views. A concrete base class should be created by using the
    View.create class method.
    """

    # Exception to be raised by the 'arg' decorators
    ArgumentError = Exception

    @classmethod
    def create(cls, route_base, decorators = None):
        """
        Returns a base class for a concrete view. The view is prepared with the 
        given route base.
        """
        assert type(route_base) in (str, unicode), "Expected string type"

        name = 'View_%s' % route_base
        bases = (FlaskView, cls, object)
        attrs = {
            'route_base': route_base,
            'trailing_slash': True
        }
        view = type(name, bases, attrs)

        # Decorators that should be applied in the order of incoming request
        # Note: these decorators are applied on all view functions by the
        # FlaskView class
        decorators = [] if decorators is None else decorators
        view.decorators = decorators + [
            view._decorator_handle_endpoint,
            view._decorator_create_request_settings,
            view._decorator_handle_exceptions
           ]

        # Return the view
        return view

    @classmethod
    def _create_response_from_error(cls, error):
        """
        Implements the response creation in case of an error. Should be 
        overwritten by the concrete class.
        """
        raise

    @classmethod
    def _create_response(cls, content):
        """
        Implements the response creation. Should be overwritten by the concrete
        class.
        """
        if isinstance(content, Response): return content
        return Response(content)

    @classmethod
    def _serialize_result(cls, result):
        """
        Implements the serialization. Should be overwritten by the concrete
        class.
        """
        return result

    @classmethod
    def _configure_request_settings(cls):
        """
        Implements the initial configuration of the request settings. Should be
        overwritten by the concrete class.
        """
        pass

    @classmethod
    def _decorator_create_request_settings(cls, fnc):
        """
        Decorator method that adds a 'settings' object to the request.
        Since the handling of a request is a pipeline, this settings object will
        essentially allow the endpoint to configure subsequent processing steps 
        in the pipeline. Initial configuration of the settings can be done
        through use of the '_configure_request_settings' hook.
        """
        @wraps(fnc)
        def wrapper(*args, **kwargs):
            # Set up the request context if it hasn't been setup
            if not hasattr(request, 'settings'):
                class RequestSettings(object):
                    def __init__(self):
                        super(RequestSettings, self).__init__()

                        # Serialization
                        self.serialization = Settings()

                        # Response
                        self.response = Settings()

                log.noise("Setting up request settings prior to call...")

                # Set the settings as a request attribute
                setattr(request, 'settings', RequestSettings())

                # Configure the settings
                cls._configure_request_settings()

            # Continue with the call
            return fnc(*args, **kwargs)
        return wrapper

    @classmethod
    def _decorator_handle_endpoint(cls, func):
        """
        Decorator method that automates handling of the serialization of the
        endpoint result and creation of a response.
        The actual serialization and response creation is implemented by the
        '_serialize_result' and '_create_response' class methods. Concrete
        classes should specialize these if required.
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Invoke endpoint
            if hasattr(func, '__name__'):
                log.noise("Invoking endpoint '%s'...", func.__name__)
            else:
                log.noise("Invoking endpoint...")

            # Return a cached version if requested
            # Caching is done by the delegate which is set by the 'cached'
            # decorator
            cached_key = None
            if hasattr(func, '__cache__'):
                cached_key = func.__cache__.key_generator()
                cached_serialized_result = func.__cache__.delegate().query(cached_key)
                if cached_serialized_result:
                    # Create the response
                    log.noise("Creating response from cached result...")
                    return cls._create_response(cached_serialized_result)

            # Invoke the endpoint
            result = func(*args, **kwargs)

            # Serialize endpoint result
            log.noise("Serializing result...")
            serialized_result = cls._serialize_result(result)

            # Store a cached version if requested
            if hasattr(func, '__cache__'):
                caching_kwargs = func.__cache__.kwargs
                func.__cache__.delegate().store(cached_key, serialized_result, **caching_kwargs)

            # Create the response
            log.noise("Creating response...")
            return cls._create_response(serialized_result)
        return wrapper

    @classmethod
    def _decorator_handle_exceptions(cls, func):
        """
        Decorator method that automates handling of exceptions occurring in the
        endpoint. All exceptions are caught and the response is generated by
        calling the '_create_response_from_error' class method.
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Let the endpoint handle the request and catch all exceptions
            try:
                return func(*args, **kwargs)

            # Handle all exceptions
            except Exception as error:
                return cls._create_response_from_error(error)
        return wrapper

    @staticmethod
    def route(*args, **kwargs):
        """
        Defines the route of an endpoint.
        """
        return flaskclassy_route(*args, **kwargs)

    @classmethod
    def cached(cls, cache, key_generator, **kwargs):
        """
        Marks the endpoint as cached: serialized results will be cached.
        
        :param cache:
            A callable object that returns the caching delegate. This caching
            delegate is reponsable for the actual caching. It must support the
            following calls:
                query(key)
                store(key, value, **kwargs)
        :param kwargs:
            Keyword arguments forwarded to the 'store' call of the caching
            delegate.
        """
        assert cache is not None, "Cache delegate provider missing"
        def _decorator(func):
            class AttributeHolder(): pass
            if hasattr(func, 'im_func'):
                func.im_func.__cache__ = AttributeHolder()
            else:
                func.__cache__ = AttributeHolder()
            setattr(func.__cache__, 'delegate', cache)
            setattr(func.__cache__, 'key_generator', key_generator)
            setattr(func.__cache__, 'kwargs', kwargs)
            return func
        return _decorator

    @classmethod
    def arg(cls, name, source = 'url', required = False, cast = None, \
        values = None, default = None, validate = None, multiple = False):
        """
        Adds the description of a request argument to an endpoint.
        The argument handling is performed behind-the-screens and the result
        is offered as a member attribute to the 'args' parameter of the 
        endpoint.

        :note:
            - multiple: Only supported for URL arguments.
        """
        # Get the argument source
        assert source in ('url', 'body'), "Invalid argument source"

        def _decorator(func):
            @wraps(func)
            def wrapped_func_arg(self, **kwargs):
                # Find the argument holder and add the parameter
                arg_holder = find_arg_holder(func)

                # Parse the body if required
                args = None
                if 'url' == source:
                    args = request.args
                elif 'body' == source:
                    # At this point, we should look at the content-type to
                    # see how we can extract the arguments
                    if not 'Content-Type' in request.headers:
                        raise cls.ArgumentError("No content-type specified")
                    content_type = request.headers['Content-Type']
                    if '' == content_type:
                        raise cls.ArgumentError("No content-type specified")

                    if 'application/json' in content_type:
                        try:
                            args = request.get_json(force = True)
                        except Exception as err:
                            raise cls.ArgumentError("Invalid JSON: %s", err )
                        if args is None:
                            raise cls.ArgumentError("Invalid JSON: null")
                    else:
                        raise cls.ArgumentError(
                            "Cannot extract parameters from request with "
                            "content type '%s'" % content_type
                           )

                # Check if the parameter is required
                if required and not name in args:
                    raise cls.ArgumentError(
                        "Parameter '%s' is required" % name
                       )

                # Retrieve the parameter
                # param = request.args.get(name, default = default)
                param = None
                default_value = default() if hasattr(default, '__call__') else default
                if 'url' == source:
                    if multiple:
                        param = args.getlist(name)
                        if [] == param: param = default_value
                    else:
                        param = args.get(name, default = default_value)
                elif 'body' == source:
                    param = args[name] if name in args else default_value

                if not param is None:
                    # Check if we must cast the parameter
                    if not cast is None:
                        try:
                            param = cast(param)

                        except Exception as error:
                            raise cls.ArgumentError(
                                "Invalid value '%s' for '%s'" % (param, name)
                               )

                        # The following assertion would prevent 'transformer'
                        # casts
                        # assert cast == type(param)

                    # Check if the value must be one of a pre-defined list
                    if not values is None and not param in values:
                        raise cls.ArgumentError(
                            "Parameter '%s' must be one of the following "
                            "values: %s" % (
                                name,
                                ', '.join(["'%s'" % v for v in values])
                               )
                           )

                    # Check if the given value passes validation
                    if not validate is None and not validate(param):
                        raise cls.ArgumentError(
                            "Invalid value '%s' for '%s'" % (param, name)
                           )

                # Add the parameter to the argument holder
                setattr(arg_holder, name, param)
                kwargs['args'] = arg_holder
                return func(self, **kwargs)

            # Enable access to the argument holder
            _enable_arg_holder(wrapped_func_arg, func)

            return wrapped_func_arg
        return _decorator

    @classmethod
    def arg_paging(cls):
        """
        Adds paging arguments 'offset' and 'limit' and some helper functions
        to the endpoint.
        """
        def _decorator(func):
            # Modify the function so that the 'offset' and 'limit' arguments
            # are declared
            modified_func = cls.arg(
                'offset',
                cast = int,
                default = 0,
                validate = lambda v: v >= 0
               )(
                    cls.arg(
                        'limit',
                        cast = int,
                        default = 10,
                        validate = lambda v: v > 0 and v <= 100
                   )
                    (
                        func
                   )
               )

            # Now add helper properties to the argument holder
            arg_holder = find_arg_holder(modified_func)
            arg_holder.page = lambda: arg_holder.offset + arg_holder.limit
            arg_holder.page_begin = lambda: arg_holder.offset
            arg_holder.page_end = lambda: arg_holder.offset + arg_holder.limit

            return modified_func
        return _decorator

    @staticmethod
    def debug_load_json_from_file(json_file):
        """
        Debug method that reads a JSON file and returns the JSON object as a 
        dictionary.
        """
        with open(this_module_path_relative(json_file), 'r') as f:
            content = json.load(f)
        return content
