################################################################################
# base._unittests.tests.testsettings
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
from testing import TestCase
from base.application.settings import \
    Settings, \
    InvalidModifierError, NoOptionError, NoSectionError, \
    InvalidOptionValue, InvalidOptionName, \
    to_int, to_bool, \
    read_from_list
import os

class Test_Settings(TestCase):
    _TEST_FILE   = "testfile.cnf"
    _TEST_FILE_2 = "testfile2.cnf"

    def setUp(self):
        # Create a sample config file
        sample_config_file = """
[existing_section]
existing_option = some_value
int_option = 2
        """
        with open(Test_Settings._TEST_FILE, 'w') as f:
            f.write(sample_config_file)

        # Create a sample external config dict
        self.ext_config = {
            'existing_option': "some_value"
        }

        # Create a Settings object based on the sample config file
        self.settings = Settings(
            config_file = Test_Settings._TEST_FILE,
            ext_config = { 'ext': self.ext_config }
           )

    def tearDown(self):
        # Don't leave test files behind
        test_files = [Test_Settings._TEST_FILE, Test_Settings._TEST_FILE_2]
        for file in test_files:
            if os.path.exists(file): os.remove(file)

    def test_sections(self):
        # External section is always there
        self.assertEqual(
            2,
            len(self.settings.sections()) 
           )
        self.assertEqual(
            ['existing_section', 'ext'], self.settings.sections()
           )
        self.assertEqual(
            'existing_section' in self.settings.sections(),
            True
           )

    def test_rw_access_existing_section_existing_option(self):
        # Read access
        self.assertEqual(
            self.settings['existing_section']['existing_option'],
            "some_value"
           )

        # Write access
        self.settings['existing_section']['existing_option'] = "new_value"
        self.assertEqual(
            self.settings['existing_section']['existing_option'],
            "new_value"
           )

    def test_rw_access_existing_section_new_option(self):
        # Read access
        def _helper_fnc():
            return self.settings['existing_section']['new_option']
        self.assertRaises(NoOptionError, _helper_fnc)

        # Write access
        self.settings['existing_section']['new_option'] = "new_value"
        self.assertEqual(
            self.settings['existing_section']['new_option'],
            "new_value"
           )

    def test_rw_access_new_section_new_option(self):
        # Read access
        def _helper_fnc():
            return self.settings['new_section']['new_option']
        self.assertRaises(NoOptionError, _helper_fnc)

        # Write access
        self.settings['new_section']['new_option'] = "new_value"
        self.assertEqual(
            self.settings['new_section']['new_option'],
            "new_value"
           )

    def test_rw_access_external_section_existing_option(self):
        # Read access
        self.assertEqual(
            self.settings['ext']['existing_option'],
            "some_value"
           )

        # Write access
        self.settings['ext']['existing_option'] = "new_value"
        self.assertEqual(
            self.settings['ext']['existing_option'],
            "new_value"
           )
        self.assertEqual(
            self.ext_config['existing_option'],
            "new_value"
           )

    def test_rw_access_external_section_new_option(self):
        # Read access
        def _helper_fnc():
            return self.settings['ext']['new_option']
        self.assertRaises(NoOptionError, _helper_fnc)

        # Write access
        self.settings['ext']['new_option'] = "new_value"
        self.assertEqual(
            self.settings['ext']['new_option'],
            "new_value"
           )
        self.assertEqual(
            self.ext_config['new_option'],
            "new_value"
           )

    def test_modifier_external_section(self):
        def _helper_fnc():
            return self.settings(default = "default_value")\
                ['ext']['existing_option']
        self.assertRaises(InvalidModifierError, _helper_fnc)

    def test_modifier_default_existing_section_existing_option(self):
        self.assertEqual(
            self.settings(default = "default_value")\
                ['existing_section']['existing_option'],
            "some_value"
           )

    def test_modifier_default_existing_section_new_option(self):
        self.assertEqual(
            self.settings(default = "default_value")\
                ['existing_section']['new_option'],
            "default_value"
           )

    def test_modifier_default_new_section_new_option(self):
        self.assertEqual(
            self.settings(default = "new_value").new_section.new_option,
            "new_value"
           )

    def test_settings_invalid_option_value(self):
        def _helper_fnc():
            self.settings(default = { "a" : 2 }).new_section.new_option
        self.assertRaises(InvalidOptionValue, _helper_fnc)

    def test_modifier_invalid_option_name(self):
        def _helper_fnc():
            self.settings.existing_section[22] = "new_value"
        self.assertRaises(InvalidOptionName, _helper_fnc)

    def test_modifier_invalid_existing_section_existing_option(self):
        def _helper_fnc():
            return self.settings(invalid_modifier_ = "blabla")\
                ['existing_section']['existing_option']
        self.assertRaises(InvalidModifierError, _helper_fnc)

    def test_modifier_type_existing_section_existing_int_option(self):
        self.assertEqual(
            2,
            self.settings(convert = to_int)['existing_section']['int_option']
           )

    def test_via_attributes_rw_access_existing_sectionExistingOption(self):
        # Read access
        self.assertEqual(
            "some_value",
            self.settings.existing_section.existing_option
           )

        # Write access
        self.settings.existing_section.existing_option = "new_value"
        self.assertEqual(
            "new_value",
            self.settings.existing_section.existing_option
           )

    def test_via_attributes_rw_access_new_section_new_option(self):
        # Read access
        def _helper_fnc():
            return self.settings.new_section.new_option
        self.assertRaises(NoOptionError, _helper_fnc)

        # Write access
        self.settings.new_section.new_option = "new_value"
        self.assertEqual(
            "new_value",
            self.settings.new_section.new_option
           )

    def test_via_attributes_modifier_default_existing_section_new_option(self):
        self.assertEqual(
            "default_value",
            self.settings(default = "default_value").existing_section.new_option
           )

    def test_via_attributes_modifier_type_existing_section_int_option(self):
        self.assertEqual(
            2,
            self.settings(convert = to_int).existing_section.int_option
           )

    def test_multiple_files_without_external_config(self):
        # Create the second sample config file
        sample_config_file = """
[existing_section]
existing_option = some_other_value

[existing_section_2]
existing_option_2 = some_value
        """
        with open(Test_Settings._TEST_FILE_2, 'w') as f:
            f.write(sample_config_file)

        multiple_settings = Settings(
            config_file = [
                Test_Settings._TEST_FILE,
                Test_Settings._TEST_FILE_2
               ]
           )
        self.assertEqual(
            multiple_settings.sections(),
            ['existing_section', 'existing_section_2']
           )
        self.assertEqual(
            multiple_settings.existing_section_2.existing_option_2,
            "some_value"
           )
        self.assertEqual(
            multiple_settings.existing_section.existing_option,
            "some_other_value")

    def test_multiple_files_with_external_config(self):
        # Create the second sample config file
        sample_config_file = """
[existing_section]
existing_option = some_other_value

[existing_section_2]
existing_option_2 = some_value
        """
        with open(Test_Settings._TEST_FILE_2, 'w') as f:
            f.write(sample_config_file)

        multiple_settings = Settings(
            config_file = [
                Test_Settings._TEST_FILE,
                Test_Settings._TEST_FILE_2
               ],
            ext_config = { 'ext': self.ext_config }
           )
        self.assertEqual(
            multiple_settings.sections(),
            ['existing_section', 'existing_section_2', 'ext']
           )
        self.assertEqual(
            multiple_settings.existing_section_2.existing_option_2,
            "some_value"
           )
        self.assertEqual(
            multiple_settings.existing_section.existing_option,
            "some_other_value")

    def test_settings_iterator(self):
        self.assertEqual(
            [section for section in self.settings],
            ['existing_section', 'ext']
           )
        self.assertEqual(
            'existing_section' in self.settings,
            True
           )
        self.assertEqual(
            'nonexisting_section' in self.settings,
            False
           )

    def test_section_iterator(self):
        # Options in custom section
        self.assertEqual(
            [option for option in self.settings.existing_section],
            ['existing_option', 'int_option']
           )
        self.assertEqual(
            'existing_option' in self.settings.existing_section,
            True
           )
        self.assertEqual(
            'nonexisting_option' in self.settings.existing_section,
            False
           )

        # Options in External section
        self.assertEqual(
            [option for option in self.settings.ext],
            ['existing_option']
           )
        self.assertEqual(
            'existing_option' in self.settings.existing_section,
            True
           )
        self.assertEqual(
            'nonexisting_option' in self.settings.existing_section,
            False
           )

    def test_read_from_list(self):
        options_list = [
            'existing_section:int_option=4',
            'existing_section:existing_option=other_value'
           ]
        read_from_list(self.settings, options_list)
        self.assertEqual(
            "other_value",
            self.settings.existing_section.existing_option
           )
        self.assertEqual(
            "4",
            self.settings.existing_section.int_option
           )

    def test_option_value_adapters(self):
        # bool
        self.settings.bool_section.new_option_true = True
        self.assertEqual("true", self.settings.bool_section.new_option_true)
        self.assertEqual(True, self.settings(convert = to_bool).bool_section.new_option_true)

        self.settings.bool_section.new_option_false = False
        self.assertEqual("false", self.settings.bool_section.new_option_false)
        self.assertEqual(False, self.settings(convert = to_bool).bool_section.new_option_false)

        self.settings.bool_section.new_option_true_string = 'true'
        self.assertEqual(True, self.settings(convert = to_bool).bool_section.new_option_true_string)

        self.settings.bool_section.new_option_false_string = 'false'
        self.assertEqual(False, self.settings(convert = to_bool).bool_section.new_option_false_string)

        # int
        self.settings.int_section.new_option = 16
        self.assertEqual("16", self.settings.int_section.new_option)

        # float
        self.settings.float_section.new_option = 16.4
        self.assertEqual("16.4", self.settings.float_section.new_option)

        # list
        self.settings.list_section.new_option = ["a", "b", "c"]
        self.assertEqual("a:b:c", self.settings.list_section.new_option)      
