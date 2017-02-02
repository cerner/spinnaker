# Copyright 2015 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import re
import sys

import yaml_util


class SettingsConfigurator(object):
  """Defines methods for manipulating spinnaker configuration data."""

  @property
  def bindings(self):
    """Returns the system level yaml bindings.

    This is spinnaker.yml with spinnaker-local imposed on top of it.
    """
    if self.__bindings is None:
      self.__bindings = yaml_util.load_bindings(
          self.installation_config_dir, self.installation_config_dir)
    return self.__bindings

  @property
  def installation_config_dir(self):
    """Returns the location of the system installed config directory."""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '../../config'))

  def __init__(self, bindings=None):
    """Constructor

    Args:
      installation_parameters [InstallationParameters] if None then use default
      bindings [YamlBindings] Allows bindings to be explicitly injected for
         testing. Otherwise they are loaded on demand.
    """
    self.__bindings = bindings   # Either injected or loaded on demand.

  def update_deck_settings(self):
    """Update the settings.js file from configuration info."""
    source_path = os.path.join(self.installation_config_dir, 'settings.js')
    with open(source_path, 'r') as f:
      source = f.read()

    settings = self.process_deck_settings(source)
    self.check_deck_settings(settings)

    target_path = os.path.join(self.installation_config_dir, 'parsedSettings.js')
    print 'Rewriting deck settings in "{path}".'.format(path=target_path)
    with open(target_path, 'w') as f:
      f.write(''.join(settings))

  def check_deck_settings(self, source):
    """Check the javascript for references to unresolved spring variables.

    We're going to assume that $ does not appear anywhere. If in fact
    $ is needed for some other reason we can be more explicit looking for ${.*}.
    However we will be more conservative to catch typos like forgetting the
    opening or closing }.

    Args: source [string]
    Raises: ValueError if it found any
    """
    bad_lines = []
    for match in re.finditer(r'^(?!\s*//\s*var\s+)(.*\$.*)', source, re.MULTILINE):
      bad_lines.append(match.group(1))
    if bad_lines: 
      raise ValueError('The settings.js seems to contain unresolved variable references.'
                       '\n  {0}'.format('\n  '.join(bad_lines)))

  def process_deck_settings(self, source):
    offset = source.find('// BEGIN reconfigure_spinnaker')
    if offset < 0:
      raise ValueError(
        'deck settings file does not contain a'
        ' "# BEGIN reconfigure_spinnaker" marker.')
    end = source.find('// END reconfigure_spinnaker')
    if end < 0:
      raise ValueError(
        'deck settings file does not contain a'
        ' "// END reconfigure_spinnaker" marker.')

    original_block = source[offset:end]
    # Remove all the explicit declarations in this block
    # Leaving us with just comments
    block = re.sub('\n\s*var\s+\w+\s*=(.+)\n', '\n', original_block)
    settings = [source[:offset]]

    # Now iterate over the comments looking for var specifications
    offset = 0
    for match in re.finditer('//\s*var\s+(\w+)\s*=\s*(.+?);?\n', block) or []:
      settings.append(block[offset:match.end()])
      offset = match.end()
      name = match.group(1)
      value = self.bindings.replace(match.group(2))
      if value is None:
        value = ''
      if isinstance(value, bool):
        # Convert to javascript bool value by lowercasing the string
        settings.append('var {name} = {value};\n'.format(
           name=name, value=str(value).lower()))
      else:
        # Quote strings, don't quote numbers.
        settings.append('var {name} = {value!r};\n'.format(
           name=name, value=value))

    settings.append(block[offset:])
    settings.append(source[end:])
    return ''.join(settings)
