################################################################################
# base.application.settings
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
import ConfigParser
import re
import os

NoOptionError  = ConfigParser.NoOptionError
NoSectionError = ConfigParser.NoSectionError

class SettingsException(Exception): pass

class InvalidModifierError(SettingsException):
    """
    Exception signaling invalid modifier on option.
    """

    def __init__(self, modifier = None):
        msg = "'%s' is not a valid option modifier." % modifier \
              if not modifier is None \
              else "Modifiers are not allowed"
        super(InvalidModifierError, self).__init__(msg)

class InvalidOptionName(SettingsException):
    def __init__(self, option, section, type):
        msg = "Option '%s' in section '%s' must be string type, not %s" % \
            (option, section, str(type))
        super(InvalidOptionName, self).__init__(msg)

class InvalidOptionValue(SettingsException):
    def __init__(self, option, section, type):
        msg = "Option '%s' in section '%s' must be either string type "\
        "(or a type convertible to string via a registered adapter), not %s" % \
            (option, section, type)
        super(InvalidOptionValue, self).__init__(msg)

class ExternalSectionConflict(SettingsException):
    def __init__(self, section):
        msg = "External section '%s' already defined in configuration file." \
            % section
        super(ExternalSectionConflict, self).__init__(msg)

class ParsingError(SettingsException):
    def __init__(self, item):
        msg = "Parsing error: invalid format for '%s'." % item
        super(ParsingError, self).__init__(msg)

class WriteError(SettingsException):
    def __init__(self, item):
        msg = "Cannot write settings to disk as multiple config files are used."
        super(WriteError, self).__init__(msg)   

class MissingConfigurationFile(SettingsException):
    def __init__(self, config_file):
        msg = "Configuration file '%s' does not exist" % config_file
        super(MissingConfigurationFile, self).__init__(msg)

class Settings(object):
    """
    Class providing access to the settings in a configuration file.
    The class provides a uniform interface to both custom options
    (stored in the configuration file) as to external options.
    """

    # List of adapters that will be used to try to write objects
    # of non-string type as option values
    _registered_option_value_adapters = [ ]

    class Iterator(object):
        """
        Iterator class for various iterators.
        """

        def __init__(self, items):
            self.items = items
            self.current = 0

        def next(self):
            if self.current == len(self.items):
                raise StopIteration

            else:
                item = self.items[ self.current ]
                self.current += 1
                return self._convert(item)

        def _convert(self, item):
            return str(item)

    SectionIterator = Iterator
    OptionIterator  = Iterator

    def _finalize_init(self, config_items ):
        # Update the configuration from the startup config
        import re
        for config_item in config_items:
            m = re.match(r'^(\w+):(\w+)=(.+)$', config_item)
            if m:
                section = m.group(1)
                name    = m.group(2)
                value   = m.group(3)
                self[section][name] = value
                
        self._log.noise("Actual configuration settings:")
        for section in self._impl.sections():
            for item in self._impl.items(section ):
                self._log.noise(" -- %s.%s='%s'", section, item[0], item[1])

    class OptionProxyBase(object ):
        """
        Class serving as a base class for all concrete option proxies.
        It intercepts the dot-operator and []-operator calls and does
        some type checking. Concrete proxies should overload the _get 
        and _set methods.
        """

        def __init__(self, settings, section, **modifiers):
            # The attributes are set via the base class's __setattr__ method
            # in order to avoid calling our overridden __getattr__ / __setattr__ methods
            super(Settings.OptionProxyBase, self).__setattr__('settings',  settings)
            super(Settings.OptionProxyBase, self).__setattr__('section',   section)
            super(Settings.OptionProxyBase, self).__setattr__('modifiers', modifiers)

        def __getitem__(self, option):
            return self._get_option(option)

        def __setitem__(self, option, value):
            self._set_option(option, value)

        def __getattr__(self, option):
            return self._get_option(option)

        def __setattr__(self, option, value):
            self._set_option(option, value)

        def _get_option(self, option):
            if not type(option) in (str, unicode):
                raise InvalidOptionName(option, self.section, type(option))
            return self._get(option)

        def _set_option(self, option, value):
            # Check the option type
            if not type(option) in (str, unicode):
                raise InvalidOptionName(option, self.section, type(option))

            # Check the value type
            converted_value = \
                value \
                    if type(value) in (str, unicode) \
                    else \
                self.settings._adapt_value(value)
            if None == converted_value:
                raise InvalidOptionValue(option, self.section, type(value))
            assert type(converted_value) in (str, unicode), \
                "Adapter did not return a string type"

            # Set the option
            self._set(option, converted_value)

        def _get(self, option):
            raise NotImplementedError("Missing %s._get" % self.__class__.__name__)

        def _set(self, option, value):
            raise NotImplementedError("Missing %s._set" % self.__class__.__name__)

        def __str__(self):
            return self.section

        def __iter__(self):
            raise NotImplementedError("Missing %s.__iter__" % self.__class__.__name__)

        def __call__(self, **modifiers):
            """
            Operator () specification of modifiers.

            :param modifiers:
                Expandable dictionary of modifiers.
            :returns:
                A proxy to the settings, configured with the specified modifiers.
            """
            return self.__class__(settings = self.settings, section = self.section, **modifiers)

    class ExternalOptionProxy(OptionProxyBase ):
        """
        Class that provides access to an external option object without
        optional modifiers.
        """

        def _get(self, option):
            """
            Provides read-access to the option.

            :param option:
                The requested option.
            :returns:
                The option, with applied modifiers, under the section
                for which the proxy fronts.
            """
            # Validate the modifiers
            if 0 != len(self.modifiers):
                raise InvalidModifierError()
            
            # Make sure the option is in the dictionary
            if not option in self.settings._impl_external[ self.section ]:
                raise NoOptionError(
                    option  = option, 
                    section = self.section
                   )
            return self.settings._impl_external[ self.section ][ option ]

        def _set(self, option, value):
            """
            Provides write-access to the option.

            :param option:
                The requested option.
            :param value:
                The value for the requested option
            :returns:
                The option, with applied modifiers, under the section
                for which the proxy fronts.
            """
            # Set the option
            self.settings._impl_external[ self.section ][ option ] = value

        def __iter__(self):
            options = self.settings._impl_external[ self.section ].keys()
            return Settings.OptionIterator(options)

    class OptionProxy(OptionProxyBase ):
        """
        Class that provides access to a custom option with optional
        modifiers.
        """

        _allowed_modifiers = [ 'default', 'convert' ]

        def _get(self, option):
            """
            Provides read-access to the option.

            :param option:
                The requested option.
            :returns:
                The option, with applied modifiers, under the section
                for which the proxy fronts.
            """
            # Validate the modifiers
            for modifier in self.modifiers:
                if not modifier in Settings.OptionProxy._allowed_modifiers:
                    raise InvalidModifierError(modifier)

            # Apply modifier 'default'
            if 'default' in self.modifiers \
                and not self.settings._impl.has_option(self.section, option):
                default_value = self.modifiers[ 'default' ]
                self._set_option(option, default_value)

            # Get the option
            value = self.settings._impl.get(self.section, option)

            # Apply modifier 'type'
            if 'convert' in self.modifiers:
                value = self.modifiers[ 'convert' ](value)

            # Return the value
            return value

        def _set(self, option, value):
            """
            Provides write-access to the option.

            :param option:
                The requested option.
            :param value:
                The value for the requested option
            :returns:
                The option, with applied modifiers, under the section
                for which the proxy fronts.
            """
            # We always store strings
            if not type(value) in (str, unicode): value = str(value)

            # Set the option
            self.settings._impl.set(self.section, option, value)

        def __iter__(self):
            options = self.settings._impl.options(self.section)
            return Settings.OptionIterator(options)

    class SettingsProxy(object):
        """
        Class that provides delayed access to an option with optional
        modifiers.
        """

        def __init__(self, settings, **modifiers):
            self.settings  = settings
            self.modifiers = modifiers

        def __getitem__(self, section):
            return self.settings._get_section(section, **self.modifiers)

        def __getattr__(self, section):
            return self.settings._get_section(section, **self.modifiers)

    def __init__(self, config_file = None, defaults = None, \
            ext_config = None, strict = False):
        """
        Constructs the Settings object from an external configuration
        dictionary-like object and a configuration file.

        :param config_file:
            Either a string containing the path of the configuration file. 
            Or a list of paths to different configuration files.
        :param defaults:
            A dictionary of default values usable for the settings in the given
            configuration file.
        :param ext_config:
            A dictionary where the keys are the name of the section that will 
            give access to the external configuration object. This external 
            configuration object must be a dictionary-like object.
        :param strict:
            Checks for section conflicts between the provided external 
            configurations and those constructed from the given configuration
            files.
        """
        # Set the default parameters
        config_file = config_file if None != config_file else []
        defaults     = defaults if None != defaults else {}
        ext_config   = ext_config if None != ext_config else {}

        # Sanity checks
        assert dict == type(defaults), "Expected dict type for defaults"
        if type(config_file) in (str, unicode): config_file = [ config_file ]
        assert list == type(config_file), \
            "Expected a configuration file or a list of configuration files"
        for item in config_file:
            assert type(item) in (str, unicode), "Expected string type"
        assert dict == type(ext_config), "Expected dict type"
        assert bool == type(strict), "Expected bool type"

        # Set the underlying implementations
        self._impl = ConfigParser.ConfigParser(defaults = defaults)
        self._impl_external = ext_config
        
        # Read the configuration files
        for item in config_file:
            if not os.path.exists(item): raise MissingConfigurationFile(item)
        self._config_file = config_file
        self._read(self._config_file)

        # Check that there are no conflicting sections
        if strict:
            for section in self._impl.sections():
                if section in self._impl_external:
                    raise ExternalSectionConflict(section)

    def write(self):
        """
        Writes the settings to disk in the case where a single config file is loaded.
        If multiple files were loaded, throws an exception.
        """
        if 1 != len(self._config_file):
            raise WriteError()
        with open(self._config_file[0], 'w') as fout:
            self._impl.write(fout)

    def _read(self, config_file):
        """
        Reads in the settings from the configuration files.
        """
        # Read the configuration files
        self._impl.read(config_file)

    def sections(self):
        """
        Setting sections.

        :returns:
            The sections in the settings object.
        """
        return self._impl.sections() + self._impl_external.keys()

    def __call__(self, **modifiers):
        """
        Operator () specification of modifiers.

        :param modifiers:
            Expandable dictionary of modifiers.
        :returns:
            A proxy to the settings, configured with the specified modifiers.
        """
        return Settings.SettingsProxy(self, **modifiers)

    def __getitem__(self, section):
        """
        Operator [] retrieval of a section.

        :param section:
            The section to retrieve.
        :returns:
            The result of the dispatched call to the underlying
            Settings object.
        """
        return self._get_section(section)

    def __getattr__(self, section):
        return self._get_section(section)

    def _get_section(self, section, **modifiers):
        """
        Retrieves a section.

        :param section:
            The section to retrieve.
        :param modifiers:
            Expandable dictionary of modifiers.
        :returns:
            A proxy to the options in the requested section.
        """
        # Check if the section is available in the external configuration
        if section in self._impl_external:
            # Return the proxy
            return Settings.ExternalOptionProxy(self, section, **modifiers)

        # Add the section if required
        if not self._impl.has_section(section):
            self._impl.add_section(section)

        # Return the proxy
        return Settings.OptionProxy(self, section, **modifiers)

    def __iter__(self):
        """
        :returns:
            An iterator that will go over the sections.
        """
        proxies = [ self._get_section(section) for section in self.sections() ]
        return Settings.SectionIterator(proxies)

    def _adapt_value(self, value):
        """
        Looks for an adapter that takes an instance of value_type
        and returns a string from the given value.
        """
        for adapter in Settings._registered_option_value_adapters:
            adapted_value = adapter(value)
            if type(adapted_value) in (str, unicode):
                return adapted_value

    @classmethod
    def register_option_value_adapter(cls, adapter):
        """
        Registers an option value adapter with this instance.
        """
        cls._registered_option_value_adapters.append(adapter)

# Converters: from string to ...
def to_bool(value):
    value_lowercase = value.lower()
    if value_lowercase in ("true", "yes"):
        return True
    return False

def to_int(value):
    return int(value)

def to_float(value):
    return float(value)

def to_list(value, sep = ':'):
    return value.split(sep)

# Converters: from ... to string
def from_bool(value):
    if not bool == type(value): return
    if True == value:
        return "true"
    elif False == value:
        return "false"

def from_int(value):
    if not int == type(value): return
    return str(value)

def from_float(value):
    if not float == type(value): return
    return str(value)

def from_list(value):
    if not list == type(value): return
    return ":".join(value)

# Default option value adapters
Settings.register_option_value_adapter(from_bool)
Settings.register_option_value_adapter(from_int)
Settings.register_option_value_adapter(from_float)
Settings.register_option_value_adapter(from_list)

_read_from_list_regex = re.compile(
    r'(?P<section>[a-zA-Z_][a-zA-Z_0-9]*):(?P<option>[a-zA-Z_][a-zA-Z_0-9]*)=(?P<value>.*)'
   )
def read_from_list(settings, options_list):
    """
    Reads options from a given list into an existing settings object.

    :param settings:
        The existing Settings object in which the options will be loaded.
    :param options_list:
        A list of string types of the form 'section:option=value'.
    """
    assert list == type(options_list), "Expected list type"
    assert Settings == type(settings), "Expected Settings type"
    for item in options_list:
        assert type(item) in (str, unicode), "Expected string type"
        matches = _read_from_list_regex.match(item)
        if None == matches:
            raise ParsingError(item)
        section = matches.group('section')
        option  = matches.group('option')
        value   = matches.group('value')
        settings[ section ][ option ] = value
