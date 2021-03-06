# -*- coding: utf-8 -*-

#    Copyright 2013 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import logging
import os

import six
import yaml

from nailgun import consts
from nailgun.logger import logger


class NailgunSettings(object):
    def __init__(self):
        #构造配直文件位置
        settings_files = []
        logger.debug("Looking for settings.yaml package config "
                     "using old style __file__")
        project_path = os.path.dirname(__file__)
        project_settings_file = os.path.join(project_path, 'settings.yaml')
        settings_files.append(project_settings_file)
        settings_files.append('/etc/nailgun/settings.yaml')

        test_config = os.environ.get('NAILGUN_CONFIG')
        if test_config:
            settings_files.append(test_config)

        # If settings.yaml doesn't exist we should have default
        # config structure. Nailgun without settings is used
        # when we distribute source code to the workers for
        # distributed serialization
        self.config = {
            'VERSION': {},
            'DATABASE': {
                'engine': 'postgresql',
                'name': '',
                'host': '',
                'port': '0',
                'user': '',
                'passwd': ''
            }
        }
        #加载配直
        for sf in settings_files:
            try:
                logger.debug("Trying to read config file %s" % sf)
                self.update_from_file(sf)
            except Exception as e:
                logger.error("Error while reading config file %s: %s" %
                             (sf, str(e)))

        self.config['VERSION']['api'] = self.config.get('API')
        self.config['VERSION']['feature_groups'] = \
            self.config.get('FEATURE_GROUPS')

        fuel_release = self.get_file_content(consts.FUEL_RELEASE_FILE)
        if fuel_release:
            self.config['VERSION']['release'] = fuel_release

        fuel_openstack_version = self.get_file_content(
            consts.FUEL_OPENSTACK_VERSION_FILE)
        if fuel_openstack_version:
            self.config['VERSION']['openstack_version'] = \
                fuel_openstack_version

        if int(self.config.get("DEVELOPMENT", 0)):
            #检查发现开发模式被打开了
            logger.info("DEVELOPMENT MODE ON:")
            here = os.path.abspath(
                os.path.join(os.path.dirname(__file__), '..')
            )
            self.config.update({
                'STATIC_DIR': os.path.join(here, 'static'),
                'TEMPLATE_DIR': os.path.join(here, 'static')
            })
            logger.info("Static dir is %s" % self.config.get("STATIC_DIR"))
            logger.info("Template dir is %s" % self.config.get("TEMPLATE_DIR"))

        loglevel = self.config.get("APP_LOGLEVEL")
        if isinstance(loglevel, six.string_types):
            logger.setLevel(getattr(logging, loglevel.upper()))

    def update(self, dct):
        self.config.update(dct)

    def update_from_file(self, path):
        with open(path, "r") as custom_config:
            #从yaml中加载数据并存放self.config
            self.config.update(
                yaml.load(custom_config.read())
            )

    def get_file_content(self, path):
        #读文件内容
        try:
            with open(path, "r") as f:
                return f.read().strip()
        except Exception as e:
            logger.error("Error while reading file: %s. %s",
                         path, six.text_type(e))

    def dump(self):
        return yaml.dump(self.config)

    def __getattr__(self, name):
        return self.config.get(name, None)

    def __repr__(self):
        return "<settings object>"


settings = NailgunSettings()
