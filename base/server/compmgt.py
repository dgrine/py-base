################################################################################
# base.server.compmgt
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
from base.py.modules import this_module_path_relative, \
    get_module_name_from_path, load_module
from flask import Blueprint
import os

log = get_logger()

class MaximumThreasholdReached(Exception):
    def __init__(self, Nmax):
        msg = "The maximum threshold of %d iterations was reached." % Nmax
        super(MaximumThreasholdReached, self).__init__(msg)

class CircularDependency(Exception):
    def __init__(self):
        msg = "Component relations seem to exhibit a circular dependency. "
        super(CircularDependency, self).__init__(msg)

class MissingDependency(Exception):
    def __init__(self, dependency, missing_dependency):
        msg = "Component '%s' is dependent on non-existent component '%s'" % (dependency, missing_dependency)
        super(MissingDependency, self).__init__(msg)

class ComponentManager(object):
    def __init__(self, components_path):
        super(ComponentManager, self).__init__()

        self._components_path = components_path

    def load(self, app, includes, excludes):
        """
        Loads the component in order, taking into account the dependencies
        between the components. Returns the blueprints to extend the application with.

        :returns:   A list with blueprints.
        """
        log.info("Loading server components...")
        try:
            def _component_selector(name):
                if None != includes:
                    return name in includes
                if None != excludes:
                    return not name in excludes
                return True

            # Select the components
            log.debug("Looking for components in '%s'...", self._components_path)
            components = [
                    component \
                    for component in os.listdir(self._components_path) \
                    if os.path.isdir(
                        os.path.join(self._components_path, component)
                       ) \
                    and _component_selector(component)
                ]

            # Check if components were selected
            if 0 == len(components):
                log.warning("No components were selected")
                return []

            # Helper functions
            def get_normalized_component_name(component_name):
                return get_module_name_from_path(
                        this_module_path_relative('..', '..'),
                        os.path.join(self._components_path, component_name)
                       )

            def get_friendly_component_name(normalized_component_name):
                idx = normalized_component_name.rfind('.')
                assert -1 != idx, "Invalid normalized component name '%s'" % normalized_component_name
                return normalized_component_name[ idx + 1 : ]

            # Import the component modules
            module_names = [
                get_normalized_component_name(component)
                for component in components
                ]
            log.debug("Importing component modules: %s", ', '.join(module_names))
            modules = { module_name: load_module(module_name) for module_name in module_names }
            log.debug("Finished importing modules")

            # Get the component module dependencies
            log.debug("Analyzing component dependencies...")
            for module in modules.values():
                dependencies = \
                    module.__dict__[ 'dependencies' ] \
                        if hasattr(module, 'dependencies') and list == type(module.__dict__[ 'dependencies' ]) \
                        else \
                    []
                dependencies = [ get_normalized_component_name(dep) for dep in dependencies ]

                # Check that the dependencies exist
                for dependency in dependencies:
                    if not dependency in module_names:
                        raise MissingDependency(
                            get_friendly_component_name(module.__name__),
                            get_friendly_component_name(dependency)
                           )
                if 0 == len(dependencies):
                    log.debug("Component '%s' has no dependencies", get_friendly_component_name(module.__name__))
                    module.dependencies = []
                else:
                    log.debug(
                        "Component '%s' has dependencies on %s",
                        get_friendly_component_name(module.__name__),
                        ", ".join([ "'%s'" % get_friendly_component_name(dep) for dep in dependencies ])
                       )

            # Go over the modules and load them in order
            N_failsafe = 1000
            n = 0
            loaded_modules = []
            while True:
                if len(modules) == len(loaded_modules): break
                if n >= N_failsafe:
                    raise MaximumThreasholdReached(N_failsafe)
                n += 1

                log.debug("Component-loader iteration #%d", n)
                loaded_a_module = False
                for module in modules.values():
                    log.debug("Considering '%s'...", module.__name__)
                    if module.__name__ in loaded_modules:
                        log.debug("-> Already loaded")
                        break

                    log.debug("-> Dependencies:")
                    if 0 == len(module.dependencies): log.debug("  - [ None ]")
                    dependencies_resolved = True
                    for dep in module.dependencies:
                        log.debug("   - %s", get_normalized_component_name(dep))
                        if not get_normalized_component_name(dep) in loaded_modules:
                            log.debug("      -> not resolved")
                            dependencies_resolved = False
                            break
                    if dependencies_resolved:
                        # All dependencies are resolved, mark the component module as loaded
                        log.debug("-> All dependencies resolved")
                        loaded_modules.append(module.__name__)
                        loaded_a_module = True

                        # Initialize the component
                        if not 'init' in module.__dict__:
                            raise RuntimeError("Component '%s' has no init function" % module.__name__)
                        log.info(
                            "Initializing component '%s'",
                            get_friendly_component_name(module.__name__)
                           )
                        blueprints = module.init(app)
                        for blueprint in blueprints:
                            log.debug(
                                "Initializing blueprint '%s' of component '%s' with %d view%s",
                                blueprint.name,
                                module.__name__,
                                len(blueprints),
                                's' if len(blueprints) > 1 else '',
                               )
                            for view in blueprint.views:
                                log.debug(
                                    "Registering view '%s' in blueprint '%s' of component '%s'",
                                    view.__name__,
                                    blueprint.name,
                                    module.__name__
                                   )
                                view.register(blueprint)
                            log.debug("Integrating blueprint into application...")
                            blueprint.finalize(app)
                            log.debug("Finalized integration")

                            # Build the url prefix
                            url_prefix = module.url_prefix if hasattr(module, 'url_prefix') \
                                else '/%s' % (blueprint.name)

                            # Register the blueprint
                            log.debug(
                                "Registering blueprint '%s' of component '%s' at URL prefix '%s'",
                                blueprint.name,
                                module.__name__,
                                url_prefix
                               )
                            app.server.register_blueprint(
                                blueprint,
                                url_prefix = url_prefix
                               )

                            # Log the component as loaded
                            log.info(
                                "Component '%s' loaded",
                                get_friendly_component_name(module.__name__)
                               )
                        
                if not loaded_a_module:
                    raise CircularDependency()

            log.debug("Finished loading %d component%s.", len(modules), 's' if len(modules) > 1 else '')

        except Exception as e:
            log.critical("Loading of server components failed")
            log.exception(e)
            exit(1)
