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

from nailgun.api.v1 import urls as api_urls
from nailgun.fake_keystone import urls as fake_keystone_urls
from nailgun.settings import settings
from nailgun.webui import urls as webui_urls


def urls():
    urls = [
            #对于v1及/api的均由api_urls.app来处理
        "/api/v1", api_urls.app(),
        "/api", api_urls.app(),
        "", webui_urls.app()
    ]
    #fake情况下,/keystone的地址自已处理
    if settings.AUTH['AUTHENTICATION_METHOD'] == 'fake':
        urls = ["/keystone", fake_keystone_urls.app()] + urls
    return urls
