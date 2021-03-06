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

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

import time

from datetime import datetime
from datetime import timedelta
from sqlalchemy.sql import not_

from nailgun import notifier

from nailgun.db import db
from nailgun.db.sqlalchemy.models import Node
from nailgun.settings import settings

from nailgun.utils import logs


def update_nodes_status(timeout, logger):
    to_update = db().query(Node).filter(
        not_(Node.status == 'provisioning')
    ).filter(
        datetime.now() > (Node.timestamp + timedelta(seconds=timeout))
    ).filter_by(online=True)
    for node_db in to_update:
        away_message = u"Node '{0}' has gone away".format(
            node_db.human_readable_name)

        notifier.notify(
            "error",
            away_message,
            node_id=node_db.id
        )
        logger.warning(away_message)
    to_update.update({"online": False})
    db().commit()


def run():
    logger = logs.prepare_submodule_logger('assassin',
                                           settings.ASSASSIN_LOG_PATH)
    logger.info('Running Assassind...')
    try:
        while True:
            update_nodes_status(settings.KEEPALIVE['timeout'], logger)
            time.sleep(settings.KEEPALIVE['interval'])
    except (KeyboardInterrupt, SystemExit):
        logger.info('Stopping Assassind...')
        sys.exit(1)
